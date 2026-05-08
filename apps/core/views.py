from rest_framework import viewsets
from apps.core.models import Company, Division, Location, BinLocation
from apps.core.serializers import (
    CompanySerializer,
    DivisionSerializer,
    LocationSerializer,
    BinLocationSerializer,
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.prefetch_related("locations")
    serializer_class = DivisionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        division_type = self.request.query_params.get("division_type")
        if division_type:
            qs = qs.filter(division_type=division_type)
        is_factory = self.request.query_params.get("is_factory")
        if is_factory is not None:
            qs = qs.filter(division_type="factory" if is_factory.lower() == "true" else "head_office")
        return qs


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.select_related("division", "parent")
    serializer_class = LocationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        division = self.request.query_params.get("division")
        if division:
            qs = qs.filter(division_id=division)
        location_type = self.request.query_params.get("location_type")
        if location_type:
            qs = qs.filter(location_type=location_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs


class BinLocationViewSet(viewsets.ModelViewSet):
    queryset = BinLocation.objects.select_related("location__division")
    serializer_class = BinLocationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        location = self.request.query_params.get("location")
        if location:
            qs = qs.filter(location_id=location)
        division = self.request.query_params.get("division")
        if division:
            qs = qs.filter(location__division_id=division)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs