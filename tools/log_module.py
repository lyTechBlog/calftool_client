import logging
import os

# Set default log directory and file
LOG_DIR = "logs"
LOG_FILE = "app.log"

# Create the log directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Set up the logger
logger = logging.getLogger("my_app_logger")
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE))
file_handler.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a logging format including filename and line number
formatter = logging.Formatter(
    '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Expose the logger at the module level
log = logger

if __name__ == "__main__":
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")
    log.debug("This is a debug message")
