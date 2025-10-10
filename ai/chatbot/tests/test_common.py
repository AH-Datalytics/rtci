import unittest

import litellm
from langchain.globals import set_debug

from rtci.rtci import RealTimeCrime


class TestCommonAdapter(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        RealTimeCrime.bootstrap(debug_mode=True)
        set_debug(True)
        litellm._turn_on_debug()

    async def asyncTearDown(self):
        RealTimeCrime.shutdown()
