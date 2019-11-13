#!/usr/bin/env python3

"""KSR Receiver Web Server."""

import argparse
import logging

import yaml
import voluptuous.humanize
from werkzeug.serving import run_simple

from kskm.wksr.peercert import PeerCertWSGIRequestHandler
from kskm.wksr.server import generate_app, generate_ssl_context
from kskm.common.config_schema import wksr_config_schema

DEFAULT_HOSTNAME = '127.0.0.1'
DEFAULT_PORT = 8443
DEFAULT_CONFIG = 'wksr.yaml'


def main() -> None:
    """Main program function."""
    parser = argparse.ArgumentParser(description='KSR Web Server',
                                     add_help=True,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     )

    parser.add_argument('--config',
                        dest='config',
                        metavar='filename',
                        default=DEFAULT_CONFIG,
                        help='Configuration file')
    parser.add_argument('--hostname',
                        dest='hostname',
                        default=DEFAULT_HOSTNAME,
                        help=f'Default hostname (default {DEFAULT_HOSTNAME})')
    parser.add_argument('--port',
                        dest='port',
                        default=DEFAULT_PORT,
                        help='Port to listen on')
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='Enable debugging')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    config = yaml.load(open(args.config).read(), Loader=yaml.SafeLoader)
    voluptuous.humanize.validate_with_humanized_errors(config, ksrsigner_config_schema)

    ssl_context = generate_ssl_context(config['tls'])
    app = generate_app(config)

    run_simple(hostname=args.hostname, port=args.port, ssl_context=ssl_context,
               application=app, request_handler=PeerCertWSGIRequestHandler)


if __name__ == "__main__":
    main()
