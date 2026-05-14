from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewSet, ControlSheetViewSet,
    ControlSheetLineViewSet, CutRequirementViewSet,
    CuttingQueueViewSet,
)

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"control-sheets", ControlSheetViewSet, basename="control-sheet")
router.register(r"control-sheet-lines", ControlSheetLineViewSet, basename="control-sheet-line")
router.register(r"cut-requirements", CutRequirementViewSet, basename="cut-requirement")

# CuttingQueueViewSet has plain list/retrieve (not @action) so DefaultRouter
# won't route them. Add explicit as_view() paths alongside the router.
urlpatterns = [
    # Cutting queue — plain list/retrieve (not auto-routed by DefaultRouter)
    path("factory/", CuttingQueueViewSet.as_view({"get": "list"}), name="factory-list"),
    path("factory/reorder/", CuttingQueueViewSet.as_view({"post": "reorder"}), name="factory-reorder"),
    path("factory/<uuid:pk>/", CuttingQueueViewSet.as_view({"get": "retrieve"}), name="factory-detail"),
    # router handles @action methods: reorder, flip_bar, mark_cut, reset_bar
    path("", include(router.urls)),
]