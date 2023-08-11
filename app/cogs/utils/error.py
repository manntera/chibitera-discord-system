import traceback
from functools import wraps

import sentry_sdk

__all__ = ("excepter", )

def excepter(func):
    @wraps(func)
    async def wrapped(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            orig_error = getattr(e, "original", e)
            error_msg = "".join(
                traceback.TracebackException.from_exception(orig_error).format()
            )
            print("err: ", error_msg)

            with sentry_sdk.configure_scope() as scope:
                sentry_sdk.capture_exception(e)
                scope.clear()
            return

    return wrapped