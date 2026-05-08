from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import CompanyViewSet, DivisionViewSet, LocationViewSet, BinLocationViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet)
router.register("divisions", DivisionViewSet)
router.register("locations", LocationViewSet)
router.register("bin-locations", BinLocationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]