import logging

def setup_logger(logger_name=None):
    # Get the logger for this module or for the specified module
    logger = logging.getLogger(logger_name or __name__)

    # Set the logging level
    logger.setLevel(logging.DEBUG)

    # Check if the logger already has handlers
    if not logger.handlers:
        # Create a console handler with the same log level
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)

        # Create a formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)-7s] %(name)-25s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Add the formatter to the handler
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

    return logger