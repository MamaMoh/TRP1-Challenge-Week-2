"""Logging utilities for Automaton Auditor."""
import logging
import sys
from typing import Optional


def setup_logger(name: str = "automaton_auditor", level: int = logging.INFO, verbose: bool = False) -> logging.Logger:
    """Setup logger for the application.
    
    Args:
        name: Logger name
        level: Logging level
        verbose: If True, use DEBUG level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger  # Already configured
    
    logger.setLevel(logging.DEBUG if verbose else level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance.
    
    Args:
        name: Logger name (default: automaton_auditor)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name or "automaton_auditor")
