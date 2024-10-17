import requests

from requests.adapters import HTTPAdapter, Retry


def mount_session():
    session = requests.Session()
    session_retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=session_retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
