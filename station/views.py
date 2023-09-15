from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from station.models import TrainType
from station.serializers import TrainTypeSerializer


class TrainTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
