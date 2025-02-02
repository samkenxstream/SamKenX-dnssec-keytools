"""
Functions to validate KSRs.

The functions are organized to match the specifications, starting with the top
level function 'validate_request' in this file.

NOTE: Only validation that can be performed with _only the KSR_ are done here.
      Some checks that are done with the current KSR (KSR(n)) and the previous
      SKR (SKR(n-1)) are done elsewhere (tools_common.daisy) to avoid the KSR
      package importing the SKR package.
"""

import logging
from dataclasses import asdict

from kskm.common.config_misc import RequestPolicy
from kskm.ksr import Request
from kskm.ksr.verify_bundles import verify_bundles
from kskm.ksr.verify_header import verify_header
from kskm.ksr.verify_policy import verify_policy

__author__ = "ft"


logger = logging.getLogger(__name__)


def validate_request(request: Request, policy: RequestPolicy) -> bool:
    """
    Validate that a loaded request conforms to the policy.

    All the sub-functions to this function are expected to raise a PolicyException
    on errors. Dealing with return values to determine outcome makes it too easy
    to screw up.
    """
    logger.info("Validating KSR using request policy:")
    for k, v in sorted(asdict(policy).items()):
        logger.info(f"  {k}: {v}")
    verify_header(request, policy, logger)
    verify_bundles(request, policy, logger)
    verify_policy(request, policy, logger)
    # The 'Verify KSR/SKR chaining' checks depend on things outside the KSR, so
    # they can't be in the kskm.ksr package (to avoid circular dependencies).
    return True
