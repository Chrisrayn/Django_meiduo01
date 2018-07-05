from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'areas', views.AreaViewSet, base_name='areas')

urlpatterns = []

urlpatterns += router.urls
