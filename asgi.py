from .app import __app__ as Wsgic_ApiApp

application = Wsgic_ApiApp.wrapped_app("asgi")
