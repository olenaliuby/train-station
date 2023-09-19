from datetime import datetime

from django.db.models import OuterRef, Subquery, Sum, Count, Value
from django.db.models.functions import Coalesce
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
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
from station.permissions import IsAdminOrIfAuthenticatedReadOnly
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
    OrderListSerializer,
    TrainImageSerializer, JourneyImageSerializer, CrewImageSerializer
)


class TrainTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer
        if self.action == "upload_image":
            return TrainImageSerializer
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

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser]
    )
    def upload_image(self, request, pk=None):
        """Endpoint to upload an image to a train"""
        train = self.get_object()
        serializer = self.get_serializer(
            train,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CarriageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Carriage.objects.select_related("train")
    serializer_class = CarriageSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Route.objects.select_related("from_station", "to_station")
    serializer_class = RouteSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "upload_image":
            return CrewImageSerializer
        return CrewSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser]
    )
    def upload_image(self, request, pk=None):
        """Endpoint to upload an image to a crew member"""
        crew = self.get_object()
        serializer = self.get_serializer(
            crew,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class JourneyViewSet(viewsets.ModelViewSet):
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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        """
        Subquery for tickets count for each journey.
        Retrieve the journeys with filters.
        """

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

        departure_time = self.request.query_params.get("departure_time")
        arrival_time = self.request.query_params.get("arrival_time")
        train_id_str = self.request.query_params.get("train")

        if departure_time is not None:
            departure_date = datetime.strptime(
                departure_time,
                "%Y-%m-%d"
            ).date()
            queryset = queryset.filter(departure_time__day=departure_date.day)

        if arrival_time is not None:
            arrival_date = datetime.strptime(arrival_time, "%Y-%m-%d").date()
            queryset = queryset.filter(arrival_time__day=arrival_date.day)

        if train_id_str is not None:
            queryset = queryset.filter(train__id=int(train_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyDetailSerializer
        if self.action == "upload_image":
            return JourneyImageSerializer
        return JourneySerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser]
    )
    def upload_image(self, request, pk=None):
        """Endpoint to upload an image to a journey"""
        journey = self.get_object()
        serializer = self.get_serializer(
            journey,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
