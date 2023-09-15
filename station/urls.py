from django.urls import path, include
from rest_framework import routers

from station.views import (
    TrainTypeViewSet,
    TrainViewSet,
    CarriageViewSet,
    StationViewSet
)

router = routers.DefaultRouter()
router.register("train_types", TrainTypeViewSet)
router.register("trains", TrainViewSet)
router.register("carriages", CarriageViewSet)
router.register("stations", StationViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "station"
