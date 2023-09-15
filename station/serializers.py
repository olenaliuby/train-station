from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from station.models import (
    TrainType,
    Train,
    Carriage,
    Station
)


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "number", "train_type")


class CarriageSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        data = super().validate(attrs=attrs)
        Carriage.validate_carriage_number(
            attrs["number"],
            attrs["train"],
            ValidationError,
        )
        return data

    class Meta:
        model = Carriage
        fields = (
            "id",
            "number",
            "carriage_type",
            "seats",
            "seat_price",
            "train"
        )


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")
