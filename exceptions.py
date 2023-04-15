from wsgic.thirdparty.bottle import HTTPError

class ApiAuthError(HTTPError):
    def __init__(self, status=401, body="Access Denied", exception=None, traceback=None, **more_headers):
        return super().__init__(status, body, exception, traceback, **more_headers)
