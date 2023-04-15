import inspect
import json

from wsgic.views import BaseView, FunctionView, render, partial
from wsgic.views.templates import Jinja2Template
from wsgic.routing import Router, Route, _url
from wsgic.handlers.files import FileSystemStorage
from wsgic.http import JsonResponse, XmlResponse, request, response
from wsgic.helpers import makelist
from wsgic.thirdparty.swagger import swagger
from pathlib import Path


from .mixins import *

render = partial(render, engine=Jinja2Template)

appdir = FileSystemStorage(directory=Path(__file__).parent.as_uri().replace("file:///", ""))

class ApiTrait:
    response_codes = {
        'created': 201,
        'deleted': 200,
        'updated': 200,
        'no_content': 204,
        'invalid_request': 400,
        'unsupported_response_type': 400,
        'invalid_scope': 400,
        'temporarily_unavailable': 400,
        'invalid_grant': 400,
        'invalid_credentials': 400,
        'invalid_refresh': 400,
        'no_data': 400,
        'invalid_data': 400,
        'access_denied': 401,
        'unauthorized': 401,
        'invalid_client': 401,
        'forbidden' : 403,
        'resource_not_found': 404,
        'not_acceptable': 406,
        'resource_exists': 409,
        'conflict': 409,
        'resource_gone': 410,
        'payload_too_large': 413,
        'unsupported_media_type': 415,
        'too_many_requests': 429,
        'server_error': 500,
        'unsupported_grant_type': 501,
        'not_implemented': 501,
    }

    response_type = "json"
    responses_class = {
        "json": JsonResponse,
        "xml": XmlResponse
    }
    query_format = False
    query_format_key = "format"

    def __get_format(self):
        format = request.GET.get(self.query_format_key, self.response_type) if self.query_format else self.response_type
        if format not in self.responses_class:
            format = 'json'
        return format

    def respond(self, data, status=200, headers=None):
        return self.responses_class[self.__get_format()](data, status, headers=headers)

    def fail(self, *errors, status=400, code=None, headers=None):
        data = {
            "status": status,
            "code": code,
            "messages": list(errors)
        }
        return self.responses_class[self.__get_format()](data, status, headers=headers)

    def respondCreated(self, data):
        return self.responses_class[self.__get_format()](data, self.response_codes["created"])

    def respondDeleted(self, data):
        return self.responses_class[self.__get_format()](data, self.response_codes["deleted"])
    
    def respondUpdated(self, data):
        return self.responses_class[self.__get_format()](data, self.response_codes["updated"])

    def respondNoContent(self):
        return self.responses_class[self.__get_format()]({}, self.response_codes["no_content"])

    def failUnauthorized(self, description, code=None):
        return self.fail(description, self.response_codes["unauthorized"], code=code)

    def failForbidden(self, description, code=None):
        return self.fail(description, self.response_codes["forbidden"], code=code)

    def failNotFound(self, description="Not Found", code=None):
        return self.fail(description, self.response_codes["resource_not_found"], code=code)

    def failValidationError(self, description="Bad Requests", code=None):
        return self.fail(description, self.response_codes["invalid_data"], code=code)

    def failValidationError(self, *description, code=None):
        return self.fail(*description, self.response_codes["invalid_data"], code=code)

    def failResourceExists(self, description="Resource Exists", code=None):
        return self.fail(description, self.response_codes["resource_exists"], code=code)

    def failResourceGone(self, description="Resource Gone", code=None):
        return self.fail(description, self.response_codes["resource_gone"], code=code)

    def failTooManyRequests(self, description="Too Many Requests", code=None):
        return self.fail(description, self.response_codes["too_many_requests"], code=code)

    def failServerError(self, description="Server Error", code=None):
        return self.fail(description, self.response_codes["server_error"], code=code)

class ApiView(ApiTrait, BaseView, CreateMixin, UpdateMixin, DestroyMixin, RetrieveMixin, AuthenticationMixin):
    def index(self):
        print("index...")
        data = self.model.objects.all()
        data = data.serialize()
        print("Serializing:", data)
        return self.respond(data or {})

class SwaggerView:
    router: Router = None

    def __init__(self, router=None, *args, **kwargs):
        self.router = self.router or router

    def setup_routes(self, router, config):
        self.url = _url(config["rule"]+"/spec")
        self.assets_url = _url(config["rule"]+"/swagger_assets")

        self.router = self.router or router
        self.routes = self.router.get_routes()[1]
        self.routes.static(self.assets_url, store=appdir["templates"]["swagger"])
        self.routes.add(self.url, self.generate_spec)
        self.routes.add(config["rule"], self.index)

    def index(self):
        context = {
            "open_api_spec": self.url,
            "assets_url": self.assets_url
        }
        return render("swagger/index.html", context)
    
    def generate_spec(self):
        return JsonResponse(swagger(self.router))
    
    def generate_path_specs(self):
        route: Route
        specs = {}

        for route in self.routes.data:
            gen = self.generate_route_spec(route)
            if gen:
                gen = {**specs.get(route.rule, {}), **gen}
                specs[route.rule.replace("<", "{").replace(">", "}")] = gen
        return specs
    
    def generate_route_spec(self, route: Route):
        spec = {}
        docs = json.loads(inspect.getdoc(route.callback) or route.config.get("api_spec", "{}"))
        for method in makelist(route.method):
            if docs.get(method.lower()):
                method_spec = docs.get(method.lower(), {})
                spec[method.lower()] = method_spec
        return spec
