import time
import requests
from functools import wraps
from requests.exceptions import RequestException


def retry_on_failure(max_attempts=3, backoff=1.5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as e:
                    status = e.response.status_code
                    if 400 <= status < 500:
                        raise
                    attempt += 1
                    print(
                        f"Server error ({status}), retrying ({attempt}/{max_attempts})..."
                    )
                except RequestException as e:
                    attempt += 1
                    print(f"Network error: {e}, retrying ({attempt}/{max_attempts})...")
                time.sleep(backoff**attempt)
            raise RuntimeError(f"Failed after {max_attempts} attempts.")

        return wrapper

    return decorator
