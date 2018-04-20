from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.views import generic

from . import models


class GameDetail(generic.DetailView):
    model = models.Game

class PlayerDetail(generic.DetailView):
    model = models.Player

class EventDetail(generic.DetailView):
    model = models.Event

class OpeningDetail(generic.DetailView):
    model = models.Opening


class GameList(generic.ListView):
    model = models.Game
    context_object_name = 'game_list'

    def get_queryset(self):
        return models.Game.objects.all()[:50]
