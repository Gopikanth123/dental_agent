# logger_setup.py
import logging
import os
from logging.handlers import RotatingFileHandler
from config import config

def setup_logging():
    """
    Configures logging to output to both console and a rotating log file.
    Captures logs from all modules (Root logger).
    """
    
    # 1. Define Log Directory and File
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file_path = os.path.join(log_dir, "application.log")

    # 2. Define Format
    log_format = logging.Formatter(
        '%(asctime)s - [%(process)d] - %(name)s - %(levelname)s - %(message)s'
    )

    # 3. Create Handlers
    
    # File Handler (Rotates after 5MB, keeps 5 backup files)
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=5*1024*1024, 
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(config.LOG_LEVEL)

    # Console Handler (So you still see logs in terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(config.LOG_LEVEL)

    # 4. Configure Root Logger
    # Using the root logger ensures we capture 'uvicorn', 'fastapi', 'MCP', etc.
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)
    
    # Remove existing handlers to avoid duplicates (e.g. created by uvicorn)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging initialized. Writing to {log_file_path}")