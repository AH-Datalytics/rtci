from rtci.bot import BotFramework
from tests.test_common import TestCommonAdapter


class TestCreateTeardown(TestCommonAdapter):

    async def test_create_and_shutdown(self):
        bot: BotFramework = BotFramework.create()
        self.assertIsNotNone(bot)
