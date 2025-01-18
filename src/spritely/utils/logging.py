import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Union
import colorlog  # Add color support

def setup_logging(
    log_level: Union[str, int] = "INFO",
    log_file: Optional[Path] = None,
    use_color: bool = True
) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file path
        use_color: Whether to use colored output in console
        
    Returns:
        logging.Logger: The configured root logger
    """
    if log_file is None:
        log_dir = Path.home() / ".spritely" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "spritely.log"
    
    # Convert string log level to logging constant if needed
    numeric_level = (log_level if isinstance(log_level, int) 
                    else getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    if use_color:
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s",
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING': 'yellow',
                'ERROR':   'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
    
    # Rotating file handler (10 MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(numeric_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(numeric_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create and configure application logger
    logger = logging.getLogger("spritely")
    logger.info(f"Logging initialized at level {log_level}")
    logger.info(f"Log file: {log_file}")
    
    return logger

def get_logger(name: str, log_level: Optional[Union[str, int]] = None) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (will be prefixed with 'spritely.')
        log_level: Optional specific log level for this logger
        
    Returns:
        logging.Logger: The configured logger
    """
    logger = logging.getLogger(f"spritely.{name}")
    
    if log_level is not None:
        numeric_level = (log_level if isinstance(log_level, int)
                        else getattr(logging, log_level.upper(), logging.INFO))
        logger.setLevel(numeric_level)
    
    return logger 