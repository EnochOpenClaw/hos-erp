from rest_framework import serializers
from apps.core.models import Company, Division, Location, BinLocation


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "code", "tax_id", "email", "phone", "address", "is_active", "created_at", "updated_at"]


class DivisionSerializer(serializers.ModelSerializer):
    division_type_display = serializers.CharField(source="get_division_type_display", read_only=True)
    factory_type_display = serializers.CharField(source="get_factory_type_display", read_only=True, default=None)
    is_factory = serializers.BooleanField(read_only=True)
    location_count = serializers.IntegerField(source="locations.count", read_only=True)

    class Meta:
        model = Division
        fields = [
            "id", "name", "code", "division_type", "division_type_display",
            "factory_type", "factory_type_display", "parent", "is_active",
            "sort_order", "is_factory", "location_count", "created_at", "updated_at",
        ]


class LocationSerializer(serializers.ModelSerializer):
    location_type_display = serializers.CharField(source="get_location_type_display", read_only=True)
    division_code = serializers.CharField(source="division.code", read_only=True)
    division_name = serializers.CharField(source="division.name", read_only=True)
    full_path = serializers.CharField(read_only=True)
    bin_count = serializers.IntegerField(source="bins.count", read_only=True)

    class Meta:
        model = Location
        fields = [
            "id", "division", "division_code", "division_name", "parent",
            "name", "code", "location_type", "location_type_display",
            "is_active", "full_path", "bin_count", "created_at", "updated_at",
        ]


class BinLocationSerializer(serializers.ModelSerializer):
    division_code = serializers.CharField(source="location.division.code", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    full_code = serializers.CharField(read_only=True)
    full_path = serializers.CharField(source="location.full_path", read_only=True)

    class Meta:
        model = BinLocation
        fields = [
            "id", "location", "division_code", "location_code", "location_name",
            "name", "barcode", "is_active", "full_code", "full_path",
            "created_at", "updated_at",
        ]