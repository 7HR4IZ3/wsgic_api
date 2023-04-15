from wsgic.routing import Router
from .views import *

router = Router()
routes = router.get_routes()

# routes.get("*", index)
