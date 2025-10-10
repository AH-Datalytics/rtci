import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    __instance = None

    @staticmethod
    def current():
        if Logger.__instance is None:
            raise RuntimeError("Logger is not loaded.")
        return Logger.__instance

    @staticmethod
    def configure(log_file: str | Path = None, debug_mode: bool = False):
        if Logger.__instance:
            return Logger.__instance
        log_list = [Logger.__configure_app_logger(log_file, debug_mode)]
        Logger.__instance = Logger(log_list, debug_mode)
        return Logger.__instance

    @staticmethod
    def __configure_app_logger(log_file: str | Path, debug_mode: bool):
        main_logger = logging.getLogger("rtci")
        trace_level = logging.DEBUG - 5
        if debug_mode:
            main_logger.setLevel(trace_level)
        else:
            main_logger.setLevel(logging.INFO)
        Logger.__addLoggingLevel("TRACE", trace_level)
        formatter = logging.Formatter(
            "{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        main_logger.addHandler(stream_handler)
        if log_file is not None:
            log_path = Path(log_file)
            log_dir = Path(log_path).parent
            if not os.path.isfile(log_dir):
                log_dir.mkdir(exist_ok=True, parents=True)
            if debug_mode:
                file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
                file_handler.setFormatter(formatter)
                main_logger.addHandler(file_handler)
            else:
                backup_count = 10
                max_size_mb = 10
                max_bytes = max_size_mb * 1024 * 1024
                file_handler = RotatingFileHandler(
                    filename=log_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8")
                file_handler.setFormatter(formatter)
                main_logger.addHandler(file_handler)
        return main_logger

    def __init__(self, delegate_loggers: list, debug_mode: bool = False):
        self.logs = list(delegate_loggers)
        self.debug_mode = debug_mode

    def exception(self, message: str):
        for log in self.logs:
            log.exception(message)

    def error(self, message: str, error: Exception | str = None):
        for log in self.logs:
            log.error(message, exc_info=error)

    def warning(self, message: str, error: Exception | str = None):
        for log in self.logs:
            log.warning(message, exc_info=error)

    def info(self, message: str):
        for log in self.logs:
            log.info(message)

    def debug(self, message: str):
        for log in self.logs:
            log.debug(message)

    def trace(self, message: str):
        if not self.debug_mode:
            return
        for log in self.logs:
            try:
                log.trace(message)
            except AttributeError:
                print(message)

    @staticmethod
    def __addLoggingLevel(levelName, levelNum, methodName=None):
        if not methodName:
            methodName = levelName.lower()
        if hasattr(logging, levelName):
            return False
        if hasattr(logging, methodName):
            return False
        if hasattr(logging.getLoggerClass(), methodName):
            return False

        def logForLevel(self, message, *args, **kwargs):
            if self.isEnabledFor(levelNum):
                self._log(levelNum, message, args, **kwargs)

        def logToRoot(message, *args, **kwargs):
            logging.log(levelNum, message, *args, **kwargs)

        logging.addLevelName(levelNum, levelName)
        setattr(logging, levelName, levelNum)
        setattr(logging.getLoggerClass(), methodName, logForLevel)
        setattr(logging, methodName, logToRoot)
        return True


def logger() -> Logger:
    return Logger.current()
