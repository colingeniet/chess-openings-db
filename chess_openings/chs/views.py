from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.views import generic

from . import models


def pagination_links(current, total):
    adjacent_links_per_side = 2
    distant_links_per_side = 3

    left_adjacent = current - adjacent_links_per_side
    right_adjacent = current + adjacent_links_per_side

    left_distant_pages = left_adjacent - 1
    right_distant_pages = total - right_adjacent
    left_step = max(1, left_distant_pages // distant_links_per_side)
    right_step = max(1, right_distant_pages // distant_links_per_side)

    left = list(range(1, left_adjacent, left_step))
    middle = list(range(left_adjacent, right_adjacent + 1))
    right = list(range(total, right_adjacent, -right_step))
    right.reverse()

    return left + middle + right



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

    n_results = 50
    games = models.Game.objects.all()[(page-1)*n_results:page*n_results]
    context = {
        'game_list': games,
        'page': page
    }
    return render(request, "chs/game_list.html", context)
