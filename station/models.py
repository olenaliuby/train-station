from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TrainType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=255)
    number = models.IntegerField(unique=True)
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Carriage(models.Model):
    class CarriageType(models.TextChoices):
        ECONOMY = ("Economy", "Economy Class")
        BUSINESS = ("Business", "Business Class")
        PREMIUM = ("Premium", "Premium Class")

    CARRIAGE_TYPE_SEAT_PRICES = {
        CarriageType.ECONOMY: 50,
        CarriageType.BUSINESS: 100,
        CarriageType.PREMIUM: 150,
    }

    carriage_type = models.CharField(
        max_length=10,
        choices=CarriageType.choices,
        default=CarriageType.ECONOMY,
    )

    number = models.IntegerField()
    seats = models.IntegerField()
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="carriages"
    )

    @property
    def seat_price(self):
        return self.CARRIAGE_TYPE_SEAT_PRICES[
            Carriage.CarriageType(self.carriage_type)
        ]

    @staticmethod
    def validate_carriage_number(number, train, error_to_raise):
        if Carriage.objects.filter(number=number, train=train).exists():
            raise error_to_raise(
                {
                    "number": "Carriage with this number "
                              "already exists for this train."
                }
            )

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["number", "train"],
                name="unique_carriage_number"
            )
        ]

    def __str__(self):
        return f"Carriage {self.number} of {self.train}"


class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Route(models.Model):
    name = models.CharField(max_length=255)
    distance = models.IntegerField()
    from_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="from_station"
    )
    to_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="to_station"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Journey(models.Model):
    crew = models.ManyToManyField(Crew)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys"
    )

    def clean(self):
        if self.departure_time >= self.arrival_time:
            raise ValidationError(
                {
                    "arrival_time":
                        "Arrival time must be greater than departure time"
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Journey, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self):
        return (
            f"Journey {self.route.name}, train number — {self.train.number} "
            f"[{self.departure_time} - {self.arrival_time}]"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} by {self.user} at {self.created_at}"


class Ticket(models.Model):
    seat = models.IntegerField()
    carriage = models.ForeignKey(
        Carriage,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    @property
    def price(self):
        return self.carriage.seat_price

    @staticmethod
    def validate_ticket(seat, carriage, error_to_raise):
        for ticket_attr_value, ticket_attr_name, carriage_attr_name in [
            (seat, "seat", "seats"),
        ]:
            count_attrs = getattr(carriage, carriage_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                                          f"number must be "
                                          f"in available range: "
                                          f"(1, {carriage_attr_name}): "
                                          f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        self.validate_ticket(
            self.seat, self.carriage, ValidationError,
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["carriage", "seat", "journey"],
                name="unique_ticket"
            )
        ]
        ordering = ["carriage", "seat"]

    def __str__(self):
        return (
            f"Ticket for {self.journey} "
            f"in carriage {self.carriage.number} seat {self.seat}"
        )
