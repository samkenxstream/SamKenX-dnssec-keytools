"""Load and parse configuration."""
from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import (IO, Dict, Iterable, List, Mapping, NewType, Optional, Type,
                    Union, cast)

import yaml

from kskm.common.data import AlgorithmDNSSEC, SignaturePolicy, Policy
from kskm.common.integrity import checksum_bytes2str
from kskm.common.parse_utils import duration_to_timedelta, parse_datetime


__author__ = 'ft'

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Base exception for errors in the configuration."""

    pass


class KSKMConfig(object):

    def __init__(self, data: Mapping):
        self._data = data
        self._hsm: Optional[Mapping] = None
        self._ksk_keys: Optional[KSKKeysType] = None
        self._ksk_policy: Optional[KSKPolicy] = None
        self._request_policy: Optional[RequestPolicy] = None
        self._response_policy: Optional[ResponsePolicy] = None

    @property
    def hsm(self) -> Mapping:
        if self._hsm is None:
            self._hsm = self._data.get('hsm', {})
        assert self._hsm is not None  # help type checker
        return self._hsm

    @property
    def ksk_policy(self) -> KSKPolicy:
        if self._ksk_policy is None:
            self._ksk_policy = KSKPolicy.from_dict(self._data.get('ksk_policy', {}))
        assert self._ksk_policy is not None  # help type checker
        return self._ksk_policy

    @property
    def ksk_keys(self) -> KSKKeysType:
        """
        Load KSK key definitions from the config.

        Example:
        ---
        keys:
          ksk_current:
            description: Root DNSSEC KSK 2010
            label: Kjqmt7v
            algorithm: RSASHA256
            rsa_size: 2048
            rsa_exponent: 65537
            valid_from: 2010-07-15T00:00:00+00:00
            valid_until: 2019-01-11T00:00:00+00:00
        """
        if self._ksk_keys is None:
            res: Dict[str, KSKKey] = {}
            if 'keys' not in self._data:
                return cast(KSKKeysType, res)
            for name, v in self._data['keys'].items():
                key = KSKKey.from_dict(v)
                res[name] = key
            self._ksk_keys = cast(KSKKeysType, res)
        assert self._ksk_keys is not None  # help type checker
        return self._ksk_keys

    def get_filename(self, which: str) -> Optional[str]:
        """Get a filename from the configuration."""
        if 'filenames' in self._data:
            _this = self._data['filenames'].get(which)
            if isinstance(_this, str):
                return _this
        return None

    @property
    def request_policy(self) -> RequestPolicy:
        if self._request_policy is None:
            policy = RequestPolicy.from_dict(self._data.get('request_policy', {}))
            if policy.dns_ttl == 0:
                # Replace with the value configured to be used when signing the bundles
                policy = replace(policy, dns_ttl=self.ksk_policy.ttl)
            self._request_policy = policy
        return self._request_policy

    @property
    def response_policy(self) -> ResponsePolicy:
        if self._response_policy is None:
            self._response_policy = ResponsePolicy.from_dict(self._data.get('response_policy', {}))
        assert self._response_policy is not None  # help type checker
        return self._response_policy

    def get_schema(self, name: str) -> Schema:
        """
        Parse a named entry from the 'schemas' section of config.

        Example config:

            schemas:
              revoke:
            1:
              publish:
                - ksk_current
                - ksk_next
              sign: ksk_next
            2:
              publish: ksk_next
              revoke: ksk_current
              sign:
                - ksk_current
                - ksk_next
            ...
            9:
              publish: ksk_next
              sign: ksk_next

        Note that 'revoke' is optional. Entries may be single key names, or
        list of key names. In the resulting Schema, it is always a list of key names,
        even if there is a single key name in the list.

        :return: A Schema instance for the schema requested.
        """
        data = self._data['schemas'][name]
        _actions: Dict[int, SchemaAction] = {}
        for num in range(1, 10):
            _this = SchemaAction(publish=_parse_keylist(data[num]['publish']),
                                 sign=_parse_keylist(data[num]['sign']),
                                 revoke=_parse_keylist(data[num].get('revoke', [])))
            _actions[num] = _this
        return Schema(name=name, actions=_actions)

    @classmethod
    def from_yaml(cls, stream: IO) -> KSKMConfig:
        """Load configuration from a YAML stream."""
        return cls(yaml.safe_load(stream))


def get_config(filename: Optional[str]) -> KSKMConfig:
    """Top-level function to load configuration, or return a default ConfigType instance."""
    if not filename:
        # Avoid having Optional[ConfigType] everywhere by always having a config, even if it is empty
        return KSKMConfig({})
    with open(filename, 'rb') as fd:
        config_bytes = fd.read()
        logger.info("Loaded configuration from file %s %s", filename, checksum_bytes2str(config_bytes))
        fd.seek(0)
        return KSKMConfig.from_yaml(fd)



@dataclass(frozen=True)
class RequestPolicy(Policy):
    """Configuration knobs for validating KSRs."""

    # Verify KSR header parameters
    acceptable_domains: List[str] = field(default_factory=lambda: ['.'])

    # Verify KSR bundles
    num_bundles: int = 9
    validate_signatures: bool = True
    keys_match_zsk_policy: bool = True
    rsa_exponent_match_zsk_policy: bool = True

    # Verify KSR policy parameters
    check_bundle_overlap: bool = True
    signature_algorithms_match_zsk_policy: bool = True
    approved_algorithms: List[str] = field(default_factory=lambda: ['RSASHA256'])
    rsa_approved_exponents: List[int] = field(default_factory=lambda: [3, 65537])
    rsa_approved_key_sizes: List[int] = field(default_factory=lambda: [2048])
    signature_validity_match_zsk_policy: bool = True
    check_keys_match_ksk_operator_policy: bool = True
    # TODO: Only have 3 as acceptable key set length, and require special policy for special case?
    acceptable_key_set_lengths: List[int] = field(default_factory=lambda: [2, 3])
    dns_ttl: int = 0  # if this is 0, the config value ksk_policy.ttl will be used instead

    # Verify KSR/SKR chaining
    check_request_daisy_chain: bool = True
    # TODO: match policy timers
    # TODO: match policy algorithms (match against acceptable)
    # TODO: protocol, flags match
    # TODO: TTL limit


@dataclass(frozen=True)
class ResponsePolicy(Policy):
    """Validation parameters for SKRs."""

    num_bundles: int = 9
    validate_signatures: bool = True



SigningKey = NewType('SigningKey', str)


@dataclass(frozen=True)
class SchemaAction(object):
    """Actions to take for a specific bundle."""

    publish: Iterable[SigningKey]
    sign: Iterable[SigningKey]
    revoke: Iterable[SigningKey]


@dataclass(frozen=True)
class Schema(object):
    """A named schema used when signing KSRs."""

    name: str
    actions: Mapping[int, SchemaAction]




def _parse_keylist(elem: Union[str, List[str]]) -> List[SigningKey]:
    if isinstance(elem, list):
        return [SigningKey(x) for x in elem]
    return [SigningKey(elem)]


@dataclass()
class KSKPolicy(object):
    """
    Signing policy for the KSK operator.

    This corresponds to the 'ksk_policy' section of ksrsigner.yaml.
    """

    signature_policy: SignaturePolicy
    ttl: int
    signers_name: str = '.'

    @classmethod
    def from_dict(cls, data: Mapping) -> KSKPolicy:
        """
        Load the 'ksk_policy' section of the configuration.
    
        Algorithms are not initialised here, but rather created dynamically from the KSK keys used
        in the schema.
        """
        _get_timedelta = lambda name: duration_to_timedelta(data.get(name))
        
        _sp = SignaturePolicy(publish_safety=_get_timedelta('publish_safety'),
                              retire_safety=_get_timedelta('retire_safety'),
                              max_signature_validity=_get_timedelta('max_signature_validity'),
                              min_signature_validity=_get_timedelta('min_signature_validity'),
                              max_validity_overlap=_get_timedelta('max_validity_overlap'),
                              min_validity_overlap=_get_timedelta('min_validity_overlap'),
                              algorithms=set(),
                              )
        return cls(signature_policy=_sp,
                   ttl=int(data.get('ttl', 172800)),
                   )

@dataclass()
class KSKKey(object):
    """
    A key that can be used in schemas.

    This corresponds to an entry in the 'keys' section of ksrsigner.yaml.
    """

    description: str
    label: str
    algorithm: AlgorithmDNSSEC
    valid_from: datetime
    valid_until: Optional[datetime] = None
    rsa_size: Optional[int] = None
    rsa_exponent: Optional[int] = None

    @classmethod
    def from_dict(cls: Type[KSKKey], data: dict) -> KSKKey:
        """Instantiate KSKKey from a dict of values."""
        # do not modify callers data
        _data = deepcopy(data)
        if 'algorithm' in _data:
            _data['algorithm'] = AlgorithmDNSSEC[_data['algorithm']]
        for _dt in ['valid_from', 'valid_until']:
            # If the dict is loaded from YAML, these values will already be converted to datetime.
            # If they are not, convert them here.
            if _dt in _data and not isinstance(_data[_dt], datetime):
                _data[_dt] = parse_datetime(_data[_dt])
            elif _dt in _data:
                # Set timezone UTC in the datetime
                _data[_dt] = _data[_dt].replace(tzinfo=timezone.utc)
        return cls(**_data)


KSKKeysType = NewType('KSKKeysType', Mapping[str, KSKKey])
