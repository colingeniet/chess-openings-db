from django.db import models
from django.db.models import Q


class Account(models.Model):
    pseudo = models.CharField(max_length=20, unique=True, db_index=True)
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
    time = models.DateTimeField(auto_now=True)


class Player(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    firstname = models.CharField(max_length=50, blank=True, db_index=True)
    lastname = models.CharField(max_length=50, blank=True, db_index=True)
    elo_rating = models.IntegerField(null=True)
    nationality = models.CharField(max_length=3, null=True)

    def __str__(self):
        return self.firstname + " " + self.lastname

    def pgn_str(self):
        return self.lastname + ", " + self.firstname

    def games(self):
        return Game.objects.filter(Q(white=self) | Q(black=self))


def find_player(firstname, lastname):
    return Player.objects.filter(firstname=firstname, lastname=lastname)


def find_or_add_player(firstname, lastname, owner):
    res = find_player(firstname, lastname)
    if len(res) > 0:
        return res[0]
    else:
        obj=Object(owner=owner)
        obj.save()
        player = Player(
            object=obj,
            firstname=firstname,
            lastname=lastname
        )
        player.save()
        return player


class Event(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    event_name = models.CharField(max_length=60, db_index=True)
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

    def games(self):
        return Game.objects.filter(event=self)


def find_or_add_event(name, owner):
    res = Event.objects.filter(event_name=name)
    if len(res) > 0:
        return res[0]
    else:
        obj=Object(owner=owner)
        obj.save()
        event = Event(
            object=obj,
            event_name=name
        )
        event.save()
        return event


class Game(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    moves = models.BinaryField(db_index=True)
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
    result = models.CharField(max_length=7)

    def __str__(self):
        white_name = str(self.white) if self.white else "unknown"
        black_name = str(self.black) if self.black else "unknown"
        start_date_str = ", " + self.start_date.strftime('%Y.%m.%d') if self.start_date else ""
        location_str = ", " + self.location if self.location else ""
        players = white_name + " vs " + black_name
        result_str = " : " + self.result
        date_str = ", " + str(self.start_date) if self.start_date else ""
        event_str = ", " + self.event.name() if self.event else ""
        location_str = ", " + self.location if self.location else ""
        context = date_str + event_str + location_str
        return players + result_str + context


class Opening(models.Model):
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    moves = models.BinaryField(db_index=True)
    opening_name = models.CharField(max_length=50, db_index=True)

    def __str__(self):
        return self.opening_name
