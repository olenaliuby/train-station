from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from station.models import (
    TrainType,
    Train,
    Carriage,
    Station,
    Route,
    Crew,
    Journey,
    Order,
    Ticket
)


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


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


class CarriageListSerializer(CarriageSerializer):
    train = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "number", "train_type")


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )
    carriage_count = serializers.SerializerMethodField()

    def get_carriage_count(self, obj):
        return obj.carriages.count()

    class Meta:
        model = Train
        fields = ("id", "name", "number", "train_type", "carriage_count")


class TrainDetailSerializer(TrainSerializer):
    carriages = CarriageListSerializer(many=True, read_only=True)

    class Meta:
        model = Train
        fields = ("id", "name", "number", "train_type", "carriages")


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


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super().validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["seat"],
            attrs["carriage"],
            attrs["journey"].train,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "seat", "carriage", "journey")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order
