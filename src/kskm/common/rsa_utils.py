"""Various functions relating to the RSA algorithm."""
import base64
import math
import struct
from dataclasses import dataclass, field

from kskm.common.data import AlgorithmDNSSEC, AlgorithmPolicyRSA
from kskm.common.public_key import KSKM_PublicKey

__author__ = "ft"


def is_algorithm_rsa(alg: AlgorithmDNSSEC) -> bool:
    """Check if `alg' is one of the known RSA algorithms."""
    return alg in [
        AlgorithmDNSSEC.RSASHA1,
        AlgorithmDNSSEC.RSASHA256,
        AlgorithmDNSSEC.RSASHA512,
    ]


def parse_signature_policy_rsa(data: dict) -> AlgorithmPolicyRSA:
    """
    Parse RSA ZSK SignatureAlgorithm entries.

    The ZSK policy on a parsed KSR XML contains dicts like this:

    {'attrs': {'algorithm': '8'},
     'value': {'RSA': {'attrs': {'exponent': '3', 'size': '1024'}, 'value': ''}}}
    """
    attr_alg = AlgorithmDNSSEC(int(data["attrs"]["algorithm"]))
    attrs = data["value"]["RSA"]["attrs"]
    rsa = AlgorithmPolicyRSA(
        bits=int(attrs["size"]), exponent=int(attrs["exponent"]), algorithm=attr_alg,
    )
    return rsa


@dataclass(frozen=True)
class KSKM_PublicKey_RSA(KSKM_PublicKey):
    """A parsed DNSSEC RSA public key."""

    exponent: int
    n: bytes = field(repr=False)

    def __str__(self) -> str:
        """Return KSK Public Key as string."""
        return f"alg=RSA bits={self.bits} exp={self.exponent}"


def decode_rsa_public_key(key: bytes) -> KSKM_PublicKey_RSA:
    """Parse DNSSEC RSA public_key, as specified in RFC3110."""
    _bytes = base64.b64decode(key)
    if _bytes[0] == 0:
        # two bytes length of exponent follows
        (_exponent_len,) = struct.unpack("!H", _bytes[1:3])
        _bytes = _bytes[3:]
    else:
        (_exponent_len,) = struct.unpack("!B", _bytes[0:1])
        _bytes = _bytes[1:]

    rsa_e = int.from_bytes(_bytes[:_exponent_len], byteorder="big")
    rsa_n = _bytes[_exponent_len:]
    return KSKM_PublicKey_RSA(bits=len(rsa_n) * 8, exponent=rsa_e, n=rsa_n)


def encode_rsa_public_key(key: KSKM_PublicKey_RSA) -> bytes:
    """
    Encode a public key (probably loaded from an HSM) into base64 encoded Key.public_key form.

    This is specified in RFC 3110, section 2.
    """
    _exp_len = math.ceil(int.bit_length(key.exponent) / 8)
    exp = int.to_bytes(key.exponent, length=_exp_len, byteorder="big")
    if _exp_len > 255:
        # A value larger than 255 can't be represented using a single byte. Use long variant
        # of encoding, which is a zero byte followed by the value in two bytes.
        exp_header = b"\0" + struct.pack("!H", _exp_len)
    else:
        exp_header = struct.pack("!B", _exp_len)
    return base64.b64encode(exp_header + exp + key.n)
