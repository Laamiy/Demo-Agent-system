import logging
from pathlib import Path

def setup_production_logger():
    logger = logging.getLogger("Rapid Agent")
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Formatter
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        
        # Console Handler (Show INFO and above on screen to keep it clean)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO) 
        console.setFormatter(fmt)
        
        # File Handler (Save all DEBUG details to a file)
        log_file = Path("data_loading.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        
        logger.addHandler(console)
        logger.addHandler(file_handler)
        
    return logger

logger = setup_production_logger()