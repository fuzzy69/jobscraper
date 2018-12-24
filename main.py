# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import sys
from argparse import ArgumentParser
from logging import DEBUG, Formatter, INFO, StreamHandler, WARNING
from logging.handlers import RotatingFileHandler
from os.path import join

from application.webui.base import app
from application.webui.misc import ensure_dir
from config import LOG_DIR, WEBUI_HOST, WEBUI_LOGGING, WEBUI_LOG_FILE, WEBUI_LOG_FORMAT, WEBUI_PORT, __title__


def main() -> int:
    """WebUI server main entry point. Parse provided command line arguments, setup a Flask server and run it."""
    # Command line arguments
    parser = ArgumentParser(description=__title__)
    parser.add_argument("-d", action="store_true", dest="debug", help="Run WebUI server in a development mode")
    parser.add_argument("-v", action="store_true", dest="verbose", help="Enable verbose logging")
    args = parser.parse_args()
    # Create required directories if they don't exist
    ensure_dir(join(LOG_DIR, "celery"))
    ensure_dir(join(LOG_DIR, "spiders"))
    ensure_dir(join(LOG_DIR, "webui"))
    # Logging
    if WEBUI_LOGGING:
        log_level = DEBUG if args.verbose else INFO
        if app.logger.hasHandlers():  # Remove previous log handlers
            app.logger.handlers.clear()
        # File logging
        file_formatter = Formatter(*WEBUI_LOG_FORMAT)
        file_handler = RotatingFileHandler(WEBUI_LOG_FILE, maxBytes=1024 * 1024 * 10)
        file_handler.setLevel(WARNING)
        file_handler.setFormatter(file_formatter)
        # Console logging
        stream_formatter = Formatter(*WEBUI_LOG_FORMAT)
        stream_handler = StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(stream_formatter)
        # Set up Flask logging
        app.logger.addHandler(stream_handler)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)

    app.run(host=WEBUI_HOST, port=WEBUI_PORT, debug=args.debug)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
