from django.db import models
from django.db.models import Q
from . import pgn
from . import lookup


models.BinaryField.register_lookup(lookup.ChessStartsWith)
models.BinaryField.register_lookup(lookup.ChessStartsOf)


class Account(models.Model):
    """A website user account."""
    pseudo = models.CharField(max_length=20, unique=True, db_index=True)
    password = models.BinaryField(max_length=64)
    salt = models.BinaryField(max_length=64)
    admin = models.BooleanField(default=False, db_index=True)
    can_edit = models.ManyToManyField('Object')

    def __str__(self):
        return self.pseudo

    def has_edit_rights(self, obj):
        id = obj.object_id
        obj = Object.objects.get(pk=id)
        return self.admin or obj.owner == self or self.can_edit.filter(id=id).exists()


def has_edit_rights(account_pk, obj):
    return Account.objects.get(pk=account_pk).has_edit_rights(obj)


class Object(models.Model):
    """An object to be displayed in the website."""
    owner = models.ForeignKey(Account, models.CASCADE)

    def comments(self):
        return Comment.objects.filter(object=self).order_by('time')

    def delete(self):
        self.account_set.clear()
        return super(Object, self).delete()


def create_obj(account):
    obj = Object(owner=account)
    obj.save()
    return obj


class Comment(models.Model):
    """A comment on an object."""
    account = models.ForeignKey(Account, models.CASCADE)
    object = models.ForeignKey(Object, models.CASCADE)
    text = models.CharField(max_length=300)
    time = models.DateTimeField(auto_now=True, db_index=True)


class Player(models.Model):
    """A chess player record."""
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    firstname = models.CharField(max_length=50, blank=True, db_index=True)
    lastname = models.CharField(max_length=50, blank=True, db_index=True)
    elo_rating = models.IntegerField(null=True, db_index=True)
    nationality = models.CharField(max_length=3, null=True, db_index=True)

    def __str__(self):
        elo_str = " ({})".format(self.elo_rating) if self.elo_rating else ""
        return "{} {}{}".format(self.firstname, self.lastname, elo_str)

    def pgn_str(self):
        return self.lastname + ", " + self.firstname

    def games(self):
        return Game.objects.filter(Q(white=self) | Q(black=self))

    def delete(self):
        obj = self.object
        return super(Player, self).delete() + obj.delete()


def find_player(firstname, lastname):
    """Search a player by name."""
    return Player.objects.filter(firstname=firstname, lastname=lastname)


def find_or_add_player(firstname, lastname, owner, **kwargs):
    """Search a player by name, creates it if not found."""
    res = find_player(firstname, lastname)
    if res.exists():
        return res.first()
    else:
        obj = Object(owner=owner)
        obj.save()
        player = Player(
            object=obj,
            firstname=firstname,
            lastname=lastname,
            **kwargs
        )
        player.save()
        return player


class Event(models.Model):
    """A chess event record."""
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    event_name = models.CharField(max_length=60, db_index=True)
    location = models.CharField(max_length=60, null=True, db_index=True)
    start_date = models.DateField(null=True, db_index=True)
    end_date = models.DateField(null=True, db_index=True)

    def __str__(self):
        location_str = ", " + self.location if self.location else ""
        start_date_str = ", " + str(self.start_date) if self.start_date else ""
        end_date_str = " -- " + str(self.end_date) if self.end_date else ""
        return self.event_name + location_str + start_date_str + end_date_str

    def name(self):
        return self.event_name

    def games(self):
        return Game.objects.filter(event=self)

    def delete(self):
        obj = self.object
        return super(Event, self).delete() + obj.delete()


def find_or_add_event(name, owner, **kwargs):
    """Search an event by name, creates it if not found."""
    res = Event.objects.filter(event_name=name)
    if res.exists():
        return res.first()
    else:
        obj = Object(owner=owner)
        obj.save()
        event = Event(
            object=obj,
            event_name=name,
            **kwargs
        )
        event.save()
        return event


class Game(models.Model):
    """A chess game record."""
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
    start_date = models.DateField(null=True, db_index=True)
    location = models.CharField(max_length=60, null=True, db_index=True)
    event = models.ForeignKey(Event, models.SET_NULL, null=True)
    result = models.CharField(max_length=7, db_index=True)

    def __str__(self):
        white_name = str(self.white) if self.white else "unknown"
        black_name = str(self.black) if self.black else "unknown"
        location_str = ", " + self.location if self.location else ""
        players = white_name + " vs " + black_name
        result_str = " : " + self.result
        date_str = ", " + str(self.start_date) if self.start_date else ""
        event_str = ", " + self.event.name() if self.event else ""
        location_str = ", " + self.location if self.location else ""
        context = date_str + event_str + location_str
        return players + result_str + context

    def moves_san(self):
        binary_moves = [ord(x) for x in self.moves]
        return pgn.san_moves(pgn.decode_moves(binary_moves))

    def openings(self):
        return Opening.objects.filter(moves__chs_startof=self.moves)

    def delete(self):
        obj = self.object
        return super(Game, self).delete() + obj.delete()


class Opening(models.Model):
    """A chess opening record."""
    object = models.OneToOneField(Object, models.PROTECT, primary_key=True)
    moves = models.BinaryField(db_index=True)
    opening_name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.opening_name

    def moves_san(self):
        binary_moves = [ord(x) for x in self.moves]
        return pgn.san_moves(pgn.decode_moves(binary_moves))

    def games(self):
        return Game.objects.filter(moves__chs_startswith=self.moves)

    def variations(self):
        return Opening.objects.filter(
                moves__chs_startswith=self.moves
            ).exclude(object_id=self.object_id)

    def variation_of(self):
        return Opening.objects.filter(
                moves__chs_startof=self.moves
            ).exclude(object_id=self.object_id)

    def delete(self):
        obj = self.object
        return super(Opening, self).delete() + obj.delete()
