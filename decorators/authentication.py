from functools import wraps

from wsgic_auth.core import BasicAuth, SessionAuth, DigestAuth
from wsgic_auth.core.token import TokenAuth

from ..exceptions import ApiAuthError

def __auth(auth):
    def main(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            aut = auth()
            if aut.user():
                return func(*args, **kwargs)
            else:
                raise ApiAuthError(401, "Access Denied.")
        return wrapper
    return main

sessionauth = __auth(SessionAuth)
basicauth = __auth(BasicAuth)
digestauth = __auth(DigestAuth)
tokenauth = __auth(TokenAuth)
