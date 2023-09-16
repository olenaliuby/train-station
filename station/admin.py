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


class TicketInLine(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInLine,)


class CarriageInLine(admin.TabularInline):
    model = Carriage
    extra = 1


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    inlines = (CarriageInLine,)


admin.site.register(TrainType)
admin.site.register(Carriage)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Crew)
admin.site.register(Journey)
admin.site.register(Ticket)
