from django.db.models import OuterRef, Subquery, Sum, Count, Value
from django.db.models.functions import Coalesce
from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

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
from station.serializers import (
    TrainTypeSerializer,
    TrainSerializer,
    CarriageSerializer,
    StationSerializer,
    RouteSerializer,
    CrewSerializer,
    JourneySerializer,
    OrderSerializer,
    CarriageListSerializer,
    TrainListSerializer,
    TrainDetailSerializer,
    RouteListSerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    OrderListSerializer
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
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = (
        Train.objects.select_related("train_type")
        .annotate(carriage_count=Count("carriages"))
    )
    serializer_class = TrainSerializer

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer
        return TrainSerializer

    def get_queryset(self):
        """Retrieve the trains with filters"""
        name = self.request.query_params.get("name")
        number = self.request.query_params.get("number")
        train_type = self.request.query_params.get("train_type")
        queryset = self.queryset

        if number is not None:
            queryset = queryset.filter(number__icontains=number)

        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        if train_type is not None:
            train_type_ids = self._params_to_ints(train_type)
            queryset = queryset.filter(train_type__id__in=train_type_ids)

        return queryset


class CarriageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Carriage.objects.select_related("train")
    serializer_class = CarriageSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CarriageListSerializer
        return CarriageSerializer


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

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteListSerializer
        return RouteSerializer


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class JourneyViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = (
        Journey.objects
        .select_related(
            "route__to_station",
            "route__from_station",
            "train__train_type"
        )
        .prefetch_related("crew")
    )
    serializer_class = JourneySerializer

    def get_queryset(self):
        tickets_subquery = (
            Ticket.objects.filter(journey=OuterRef("pk"))
            .values("journey")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        queryset = super().get_queryset().annotate(
            tickets_available=(
                    Sum("train__carriages__seats")
                    - Coalesce(Subquery(tickets_subquery), Value(0))
            )
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyDetailSerializer
        return JourneySerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 100


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.select_related("ticket__carriage__train")
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
