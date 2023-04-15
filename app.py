from wsgic import WSGIApp
from wsgic.helpers import config

class Wsgic_ApiApp(WSGIApp):
    def __init__(self):
        super().__init__("wsgic_api.urls:router", config)

__app__ = Wsgic_ApiApp()
__app__.setup()