from django.contrib import admin

from station.models import (
    TrainType,
    Train,
    Carriage,
    Station,
    Route,
    Crew,
    Journey,
    Ticket,
    Order
)

admin.site.register(TrainType)
admin.site.register(Train)
admin.site.register(Carriage)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Crew)
admin.site.register(Journey)
admin.site.register(Ticket)
admin.site.register(Order)
