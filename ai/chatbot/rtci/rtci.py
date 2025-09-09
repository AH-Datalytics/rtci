from pathlib import Path

from dotenv import load_dotenv

from rtci.util.log import Logger
from rtci.util.prompt import PromptLibrary


class RealTimeCrime:
    prompt_library: PromptLibrary
    logger: Logger

    @staticmethod
    def bootstrap(dotenv_path: str | Path = None, debug_mode: bool = False):
        load_dotenv(dotenv_path=dotenv_path)
        RealTimeCrime.logger = Logger.configure(debug_mode=debug_mode)
        RealTimeCrime.prompt_library = PromptLibrary.create()
        if debug_mode:
            RealTimeCrime.prompt_library.push_prompts()

    @staticmethod
    def shutdown():
        pass
