from os import environ
from pathlib import Path

import matplotlib
from dotenv import load_dotenv

from rtci.util.cache import FileCache
from rtci.util.log import Logger
from rtci.util.prompt import PromptLibrary


class RealTimeCrime:
    prompt_library: PromptLibrary
    file_cache: FileCache
    logger: Logger

    @staticmethod
    def bootstrap(dotenv_path: str | Path = None, debug_mode: bool = False):
        load_dotenv(dotenv_path=dotenv_path)
        RealTimeCrime.logger = Logger.configure(debug_mode=debug_mode)
        RealTimeCrime.prompt_library = PromptLibrary.create(ignore_s3=debug_mode)
        RealTimeCrime.file_cache = FileCache.create()
        # set the matplotlib backend to 'Agg' to prevent crash on macOS
        # 'Agg' is a non-interactive backend that can be used in a non-main thread
        matplotlib.use('Agg')
        # set the environment variable to disable parallelism in tokenizers
        environ["TOKENIZERS_PARALLELISM"] = "false"
        if not debug_mode:
            RealTimeCrime.prompt_library.push_prompts()

    @staticmethod
    def shutdown():
        if RealTimeCrime.file_cache:
            RealTimeCrime.file_cache.close()
