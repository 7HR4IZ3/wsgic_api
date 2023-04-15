from wsgic.http import request
from wsgic_api.exceptions import ApiAuthError

class BaseMixin:
    def get_object(self, **kwargs):
        return self.model.objects.get_one(**kwargs)

class CreateMixin(BaseMixin):
    """
    Create a model instance.
    """
    def create(self, **kwargs):
        data = request.json
        self.model.objects.create(**data)
        ret = self.get_object(**data)
        return self.respondCreated(ret.serialize())

class ListMixin(BaseMixin):
    """
    List a queryset.
    """
    def list(self, **kwargs):
        data = self.get_object(**kwargs)
        data = data.serialize()
        return self.respond(data or {})

class RetrieveMixin(BaseMixin):
    """
    Retrieve a model instance.
    """
    def retrieve(self, **kwargs):
        x = self.get_object(**kwargs)
        if x:
            return self.respond(x.serialize())
        return self.failNotFound("No %s with id: %s"%(self.model.__table_name__(), kwargs["id"]))

class UpdateMixin(BaseMixin):
    """
    Update a model instance.
    """
    def update(self, **kwargs):
        # partial = kwargs.pop('partial', False)
        self.model.objects.update(request.json, **kwargs)
        instance = self.get_object(**kwargs)
        # serializer = self.get_serializer(instance, data=request.data, partial=partial)
        # serializer.is_valid(raise_exception=True)
        # self.perform_update(instance)
        

        # if getattr(instance, '_prefetched_objects_cache', None):
        #     # If 'prefetch_related' has been applied to a queryset, we need to
        #     # forcibly invalidate the prefetch cache on the instance.
        #     instance._prefetched_objects_cache = {}
        if instance:
            return self.respondUpdated(instance.serialize())
        return self.failNotFound()
    
    def get_serializer(self, instance, **kw):
        return instance

class DestroyMixin(BaseMixin):
    """
    Destroy a model instance.
    """
    def delete(self, **kwargs):
        instance = self.get_object(**kwargs)
        if instance:
            self.perform_destroy(instance)
            return self.respondDeleted({})
        return self.failResourceGone()

    def perform_destroy(self, instance):
        self.model.objects.delete(**instance.serialize())

class AuthenticationMixin(BaseMixin):
    authenticators = []

    def get_auth_wrapper(self, func):
        authenticators = [x(func) for x in self.authenticators]
        auth_len = len(authenticators)

        def wrapper(*args, **kwargs):
            for index, item in enumerate(authenticators):
                try:
                    return item(*args, **kwargs)
                except ApiAuthError as e:
                    if (index+1 == auth_len):raise e
                    else:pass
        return wrapper
