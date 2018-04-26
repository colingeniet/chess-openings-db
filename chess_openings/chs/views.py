from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.views import generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from . import models


def pagination_links(current, total):
    """Creates a list of page numbers to link to."""
    adjacent_links_per_side = 2
    distant_links_per_side = 3

    left_adjacent = current - adjacent_links_per_side
    right_adjacent = current + adjacent_links_per_side

    left_distant_pages = left_adjacent - 1
    right_distant_pages = total - right_adjacent
    left_step = max(1, left_distant_pages // distant_links_per_side)
    right_step = max(1, right_distant_pages // distant_links_per_side)

    left = list(range(1, left_adjacent, left_step))
    middle = list(range(max(1, left_adjacent), min(total, right_adjacent) + 1))
    right = list(range(total, right_adjacent, -right_step))
    right.reverse()

    return left + middle + right


class PaginatedListView(generic.ListView):
    def get_context_data(self, **kwargs):
        context = super(PaginatedListView, self).get_context_data(**kwargs)
        if context['paginator']:
            current = context['page_obj'].number
            total = context['paginator'].num_pages
            context['page_links'] = pagination_links(current, total)
        return context


class GameDetail(generic.DetailView):
    model = models.Game


class PlayerDetail(generic.DetailView):
    model = models.Player

    def get_context_data(self, **kwargs):
        context = super(generic.DetailView, self).get_context_data(**kwargs)
        context['player_games'] = context['player'].games()[:50]
        return context


class EventDetail(generic.DetailView):
    model = models.Event

    def get_context_data(self, **kwargs):
        context = super(generic.DetailView, self).get_context_data(**kwargs)
        context['event_games'] = context['event'].games()[:50]
        return context


class OpeningDetail(generic.DetailView):
    model = models.Opening


class GameList(PaginatedListView):
    paginate_by = 50
    context_object_name = "game_list"

    def get_queryset(self):
        query = self.request.GET
        result = models.Game.objects.all()
        if 'result' in query:
            result = result.filter(result=query['result'])
        if 'white' in query:
            result = result.filter(white__lastname__icontains=query['white'])
        if 'black' in query:
            result = result.filter(black__lastname__icontains=query['black'])
        if 'player' in query:
            result = result.filter(
                Q(white__lastname__icontains=query['player'])
                | Q(black__lastname__icontains=query['player']))
        if 'event' in query:
            result = result.filter(event__event_name__icontains=query['event'])
        return result


class PlayerList(PaginatedListView):
    model = models.Player
    paginate_by = 50


class EventList(PaginatedListView):
    model = models.Event
    paginate_by = 50


class OpeningList(PaginatedListView):
    model = models.Opening
    paginate_by = 50
