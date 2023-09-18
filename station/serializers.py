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
    carriage_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "number",
            "train_type",
            "carriage_count",
            "capacity"
        )


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


class RouteListSerializer(RouteSerializer):
    from_station = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )
    to_station = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super().validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["seat"],
            attrs["carriage"],
            attrs["journey"],
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "seat", "carriage", "journey")


class TicketListSerializer(TicketSerializer):
    carriage_number = serializers.IntegerField(
        source="carriage.number",
        read_only=True
    )
    journey_route_name = serializers.CharField(
        source="journey.route.name",
        read_only=True
    )
    journey_train_number = serializers.IntegerField(
        source="journey.train.number",
        read_only=True
    )
    journey_departure_time = serializers.CharField(
        source="journey.departure_time",
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "seat",
            "carriage_number",
            "journey_route_name",
            "journey_train_number",
            "journey_departure_time"
        )


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("seat", "carriage")


class JourneySerializer(serializers.ModelSerializer):
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    crew = CrewSerializer(many=True, required=False)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew"
        )

    def create(self, validated_data):
        crew_data = validated_data.pop("crew", [])
        journey = Journey.objects.create(**validated_data)
        crew_members = Crew.objects.bulk_create(
            [Crew(**data) for data in crew_data]
        )
        journey.crew.add(*crew_members)
        return journey


class JourneyListSerializer(JourneySerializer):
    route_name = serializers.CharField(source="route.name", read_only=True)
    train_name = serializers.CharField(source="train.name", read_only=True)
    train_number = serializers.CharField(source="train.number", read_only=True)
    train_type = serializers.CharField(
        source="train.train_type.name",
        read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route_name",
            "train_name",
            "train_number",
            "train_type",
            "tickets_available",
            "departure_time",
            "arrival_time",
            "crew",
        )


class JourneyDetailSerializer(JourneySerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainDetailSerializer(many=False, read_only=True)
    taken_seats = TicketSeatsSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "taken_seats"
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

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


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
