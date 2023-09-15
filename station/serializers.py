from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from station.models import TrainType, Train, Carriage


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "number", "train_type")


class CarriageSerializer(serializers.ModelSerializer):
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
