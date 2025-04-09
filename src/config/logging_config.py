import logging
import socket
from logging.handlers import SocketHandler
from typing import Dict


def setup_logging(config: Dict) -> logging.Logger:
    """
    Setup logging configuration with Logstash integration
    """
    logger = logging.getLogger('document-chat')

    if not logger.handlers:  #Prevent duplicate handlers
        # Set the log level
        log_level = getattr(logging, config['log_level'].upper(), logging.INFO)
        logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Create Logstash handler
        logstash_handler = SocketHandler(
            config['logstash_host'],
            config['logstash_port']
        )
        logstash_handler.setFormatter(formatter)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add both handlers to logger
        logger.addHandler(logstash_handler)
        logger.addHandler(console_handler)

    # Add extra context
    logger = logging.LoggerAdapter(logger, {
        'hostname': socket.gethostname(),
        'app_name': config['app_name']
    })

    return logger
