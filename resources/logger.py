import logging
import os
from dotenv import load_dotenv
from google.cloud import logging as gcp_logging
from colorama import Fore, Style, init
from singleton_decorator import singleton

init()
load_dotenv()

INF_ENV = os.getenv("INF_ENV", "develop")  # Default to develop
PROJECT_ID = os.getenv("PROJECT_ID")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validate environment
if not INF_ENV:
    raise ValueError("Missing INF_ENV variable in .env file.")
if not PROJECT_ID:
    raise ValueError("Missing PROJECT_ID variable in .env file.")


@singleton
class LoggerSingleton:
    def __init__(self, process):
        try:
            client = gcp_logging.Client(project=PROJECT_ID)
            self._logger = client.logger(process)
        except Exception as e:
            print(f"Failed to initialize GCP logger: {e}")
            raise

    def log_struct(self, info, severity="INFO", **kw):
        try:
            self._logger.log_struct(info, severity=severity, **kw)
        except Exception as e:
            print(f"Error logging to GCP: {e}")
            raise  # Raise to make failures visible

class GcpLogger:
    def __init__(self, process: str, env: str = 'develop'):
        self.process = process
        self.environment = env
        self._logger = LoggerSingleton(process)
        self._color_map = {
            'INFO': Fore.BLUE,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'DEBUG': Fore.GREEN,
            'ALERT': Fore.RED
        }

    def print_to_console(self, severity, message):
        color = self._color_map.get(severity, Fore.RESET)
        print(f"{color}{severity}: {message}{Style.RESET_ALL}")

    def debug(self, message: str, customer_id='system'):
        if LOG_LEVEL == 'DEBUG':
            self.write_log_entry("DEBUG", message, customer_id)

    def info(self, message: str, customer_id='system'):
        self.write_log_entry("INFO", message, customer_id)

    def warning(self, message: str, customer_id='system'):
        self.write_log_entry("WARNING", message, customer_id)

    def error(self, message: str, customer_id='system'):
        self.write_log_entry("ERROR", message, customer_id)

    def critical(self, message: str, customer_id='system'):
        self.write_log_entry("CRITICAL", message, customer_id)

    def exception(self, message: str, customer_id='system'):
        self.write_log_entry("ERROR", message, customer_id)

    def write_log_entry(self, severity: str, message: str, customer_id: str):
        log_entry = {
            "process": self.process,
            "message": message,
            "environment": self.environment,
            "customer": customer_id
        }
        # Always log to GCP
        self._logger.log_struct(log_entry, severity=severity)
        # Print to console only if not in production
        if self.environment not in ['production']:
            self.print_to_console(severity, message)

def get_logger(name: str) -> 'GcpLogger':
    return GcpLogger(process=name, env=INF_ENV)