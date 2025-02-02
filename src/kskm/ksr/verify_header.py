"""Controls to verify KSR header."""
from logging import Logger

from kskm.common.config_misc import RequestPolicy
from kskm.common.validate import PolicyViolation
from kskm.ksr import Request


class KSR_HeaderPolicyViolation(PolicyViolation):
    """Policy violation in a KSRs header."""


class KSR_ID_Violation(KSR_HeaderPolicyViolation):
    """KSR-ID policy violation."""


class KSR_DOMAIN_Violation(KSR_HeaderPolicyViolation):
    """KSR-DOMAIN policy violation."""


def verify_header(request: Request, policy: RequestPolicy, logger: Logger) -> None:
    """Check the header elements of a Key Signing Request."""
    logger.debug('Begin "Verify KSR header"')

    check_domain(request, policy, logger)
    check_id(request, policy, logger)

    logger.debug('End "Verify KSR header"')


def check_domain(request: Request, policy: RequestPolicy, logger: Logger) -> None:
    """
    Check the domain name in the request.

    KSR-DOMAIN:
      Verify that the KSR domain name is correct.
    """
    if request.domain not in policy.acceptable_domains:
        raise KSR_DOMAIN_Violation(
            f"KSR-DOMAIN: Request domain {request.domain!r} not in "
            f"policy's acceptable domains {policy.acceptable_domains}"
        )
    logger.info(f"KSR-DOMAIN: Verified domain {request.domain!r}")


def check_id(request: Request, policy: RequestPolicy, logger: Logger) -> None:
    """
    Check the ID in the request.

    KSR-ID:
      Verify that the KSR ID is unique.
    """
    logger.info("KSR-ID: Will be checked later, when SKR is available")
