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


def game_list(request):
    try:
        page = int(request.GET['page'])
    except KeyError:
        page = 1

    games = models.Game.objects.all()[(page-1)*50:page*50]
    context = {
        'game_list': games,
        'page': page
    }
    return render(request, "chs/game_list.html", context)
