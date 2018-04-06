from django.db import models


class PSQLByteArray(models.Field):
    def db_type(self, connection):
        if connection.setting_dict['ENGINE'] == 'django.db.backends.postgresql':
            return 'bytea'
        else:
            raise NotSupportedError("PSQLByteArray type requires psql backend")


class Account(models.Model):
    pseudo = models.CharField(max_length=20)
    password = models.CharField(max_length=64)
    can_edit = models.ManyToManyField('Object')


class Object(models.Model):
    owner = models.ForeignKey(Account, models.CASCADE)


class Comment(models.Model):
    account = models.ForeignKey(Account, models.CASCADE)
    object = models.ForeignKey(Object, models.CASCADE)
    text = models.CharField(max_length=300)
    time = models.TimeField()


class Player(models.Model):
    id = models.ForeignKey(Object, models.PROTECT, primaryKey=True)
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    elo_rating = models.IntegerField()
    nationality = models.CharField(max_length=3)


class Event(models.Model):
    id = models.ForeignKey(Object, models.PROTECT, primaryKey=True)
    event_name = models.CharField(max_length=60)
    location = models.CharField(max_length=60)
    start_date = models.DateField()
    end_date = models.DateField()


class Game(models.Model):
    id = models.ForeignKey(Object, models.PROTECT, primaryKey=True)
    moves = PSQLByteArray()
    white = models.ForeignKey(Player, models.SET_NULL)
    black = models.ForeignKey(Player, models.SET_NULL)
    start_date = models.DateField()
    location = models.CharField(max_length=60)
    event = models.ForeignKey(Event, models.SET_NULL)
    result = models.IntegerField()


class Opening(models.Model):
    id = models.ForeignKey(Object, models.PROTECT, primaryKey=True)
    moves = PSQLByteArray()
    opening_name = models.CharField(30)
