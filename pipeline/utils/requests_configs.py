import requests
import ssl
import urllib3

from requests.adapters import HTTPAdapter, Retry


def mount_session():
    session = requests.Session()
    session_retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=session_retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def mount_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    return session


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    # "transport adapter" that allows use of custom ssl_context
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        self.poolmanager = None
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )
