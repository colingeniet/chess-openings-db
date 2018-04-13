from django.db import models


class Account(models.Model):
    pseudo = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=64)
    can_edit = models.ManyToManyField('Object')

    def __str__(self):
        return self.pseudo


class Object(models.Model):
    owner = models.ForeignKey(Account, models.CASCADE)


class Comment(models.Model):
    account = models.ForeignKey(Account, models.CASCADE)
    object = models.ForeignKey(Object, models.CASCADE)
    text = models.CharField(max_length=300)
    time = models.TimeField()


class Player(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    elo_rating = models.IntegerField(null=True)
    nationality = models.CharField(max_length=3, null=True)

    def __str__(self):
        return self.firstname + " " + self.lastname


class Event(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    event_name = models.CharField(max_length=60)
    location = models.CharField(max_length=60, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    def __str__(self):
        location_str = ", " + self.location if self.location else ""
        start_date_str = ", " + self.start_date if self.start_date else ""
        end_date_str = " -- " + self.end_date if self.start_date and self.end_date else ""
        return self.event_name + location_str + start_date_str + end_date_str

    def name(self):
        return self.event_name


class Game(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    moves = BinaryField()
    white = models.ForeignKey(
        Player,
        models.SET_NULL,
        related_name="plays_white",
        null=True,
    )
    black = models.ForeignKey(
        Player,
        models.SET_NULL,
        related_name="plays_black",
        null=True,
    )
    start_date = models.DateField(null=True)
    location = models.CharField(max_length=60, null=True)
    event = models.ForeignKey(Event, models.SET_NULL, null=True)
    result = models.IntegerField()

    def __str__(self):
        white_name = str(self.white) if self.white else "unknown"
        black_name = str(self.black) if self.black else "unknown"
        start_date_str = ", " + self.start_date if self.start_date else ""
        location_str = ", " + self.location if self.location else ""
        players = white_name + " vs " + black_name
        result_str = " : " + self.result_str()
        date_str = ", " + str(self.start_date) if self.start_date else ""
        event_str = ", " + self.event.name() if self.event else ""
        location_str = ", " + self.location if self.location else ""
        context = date_str + event_str + location_str
        return players + result_str + context

    def result_str(self):
        if self.result > 0:
            return "1-0"
        elif self.result < 0:
            return "0-1"
        else:
            return "1/2-1/2"


class Opening(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    moves = BinaryField()
    opening_name = models.CharField(max_length=30)

    def __str__(self):
        return self.opening_name
