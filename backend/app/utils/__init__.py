"""Logger utility"""
import logging

def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    return logging.getLogger(name)
