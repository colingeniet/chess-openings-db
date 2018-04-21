from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.views import generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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

class EventDetail(generic.DetailView):
    model = models.Event

class OpeningDetail(generic.DetailView):
    model = models.Opening


class GameList(PaginatedListView):
    model = models.Game
    paginate_by = 50
