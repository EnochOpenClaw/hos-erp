from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views import MaterialCategoryViewSet, ExtrusionTypeViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", MaterialCategoryViewSet)
router.register("extrusion-types", ExtrusionTypeViewSet)
router.register("products", ProductViewSet)

urlpatterns = [
    path("", include(router.urls)),
]