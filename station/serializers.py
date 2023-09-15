from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from station.models import (
    TrainType,
    Train,
    Carriage,
    Station,
    Route,
    Crew,
    Journey
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


class RouteSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        from_station = attrs.get("from_station")
        to_station = attrs.get("to_station")
        if from_station == to_station:
            raise serializers.ValidationError(
                "Source (from station) and destination "
                "(to station) cannot be the same."
            )
        return attrs

    class Meta:
        model = Route
        fields = ("id", "name", "distance", "from_station", "to_station")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time"
        )
