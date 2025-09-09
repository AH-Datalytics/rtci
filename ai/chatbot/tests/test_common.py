import unittest

from rtci.rtci import RealTimeCrime


class TestCommonAdapter(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        RealTimeCrime.bootstrap(debug_mode=True)

    async def asyncTearDown(self):
        RealTimeCrime.shutdown()
