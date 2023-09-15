from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from station.models import (
    TrainType,
    Train,
    Carriage,
    Station,
    Route
)
from station.serializers import (
    TrainTypeSerializer,
    TrainSerializer,
    CarriageSerializer,
    StationSerializer,
    RouteSerializer
)


class TrainTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Train.objects.select_related("train_type")
    serializer_class = TrainSerializer


class CarriageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Carriage.objects.select_related("train")
    serializer_class = CarriageSerializer


class StationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Route.objects.select_related("from_station", "to_station")
    serializer_class = RouteSerializer
