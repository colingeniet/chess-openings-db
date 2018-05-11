from django.http import Http404, HttpResponseRedirect
from django.views import generic
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from . import pgn

from . import models

import hashlib


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

    def get_context_data(self, **kwargs):
        context = super(GameDetail, self).get_context_data(**kwargs)
        context['openings'] = context['game'].openings()[:50]
        return context


class PlayerDetail(generic.DetailView):
    model = models.Player

    def get_context_data(self, **kwargs):
        context = super(PlayerDetail, self).get_context_data(**kwargs)
        context['player_games'] = context['player'].games()[:50]
        return context


class EventDetail(generic.DetailView):
    model = models.Event

    def get_context_data(self, **kwargs):
        context = super(EventDetail, self).get_context_data(**kwargs)
        context['event_games'] = context['event'].games()[:50]
        return context


class OpeningDetail(generic.DetailView):
    model = models.Opening

    def get_context_data(self, **kwargs):
        context = super(OpeningDetail, self).get_context_data(**kwargs)
        context['opening_games'] = context['opening'].games()[:50]
        return context


class GameList(PaginatedListView):
    paginate_by = 50
    context_object_name = "game_list"

    def get_queryset(self):
        query = self.request.GET

        def is_set(attr):
            return attr in query and query[attr]

        result = models.Game.objects
        if is_set('result'):
            result = result.filter(result=query['result'])
        if is_set('location'):
            result = result.filter(location__icontains=query['location'])
        if is_set('event'):
            result = result.filter(event__event_name__icontains=query['event'])
        if is_set('white'):
            result = result.filter(
                Q(white__lastname__icontains=query['white'])
                | Q(white__firstname__icontains=query['white'])
            )
        if is_set('white_nat'):
            result = result.filter(white__nationality=query['white_nat'])
        if is_set('black'):
            result = result.filter(
                Q(black__lastname__icontains=query['black'])
                | Q(black__firstname__icontains=query['black'])
            )
        if is_set('black_nat'):
            result = result.filter(white__nationality=query['black_nat'])
        if is_set('player'):
            result = result.filter(
                Q(white__lastname__icontains=query['player'])
                | Q(black__lastname__icontains=query['player'])
            )
        if is_set('player_nat'):
            result = result.filter(
                Q(white__nationality=query['player_nat'])
                | Q(black__nationality=query['player_nat'])
            )
        if is_set('opening'):
            try:
                opening = models.Opening.objects.get(
                    opening_name=query['opening']
                )
                result = result.filter(moves__chs_startswith=opening.moves)
            except models.Opening.DoesNotExist:
                result = models.Game.objects.none()
        if is_set('moves'):
            moves = pgn.encode_moves_from_uci(query['moves'].split(','))
            result = result.filter(moves__chs_startswith=moves)
        return result.all()

    def get_context_data(self, **kwargs):
        context = super(GameList, self).get_context_data(**kwargs)
        queryset = self.get_queryset()
        games = queryset.count()
        white = queryset.filter(result='1-0').count()
        black = queryset.filter(result='0-1').count()
        draws = queryset.filter(result='1/2-1/2').count()
        context['game_number'] = games
        context['white_wins'] = white
        context['black_wins'] = black
        context['draws'] = draws
        if games == 0:
            context['white_percent'] = 0
            context['black_percent'] = 0
            context['draws_percent'] = 0
        else:
            context['white_percent'] = white / games * 100
            context['black_percent'] = black / games * 100
            context['draws_percent'] = draws / games * 100
        return context


class PlayerList(PaginatedListView):
    model = models.Player
    paginate_by = 50


class EventList(PaginatedListView):
    model = models.Event
    paginate_by = 50


class OpeningList(PaginatedListView):
    model = models.Opening
    paginate_by = 50


def search_game(request):
    return render(request, 'chs/game_search.html')


def search_player(request):
    return render(request, 'chs/player_search.html')


def search_event(request):
    return render(request, 'chs/event_search.html')


def search_opening(request):
    return render(request, 'chs/opening_search.html')


def create_game(request):
    return render(request, 'chs/game_create.html')


def add_game(request):
    return HttpResponseRedirect(reverse('chess:game_list'))


def add_game_pgn(request):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    if not request.POST['pgn']:
        return render(request, 'chs/error.html', {
            'error': "pgn file not found"
        })
    pgn.load_string(request.POST['pgn'], account)
    return HttpResponseRedirect(reverse('chess:game_list'))


def object(request, pk):
    obj = get_object_or_404(models.Object, id=pk)
    if models.Game.objects.filter(object=obj).exists():
        return HttpResponseRedirect(reverse('chess:game', args=(obj.id,)))
    elif models.Player.objects.filter(object=pk).exists():
        return HttpResponseRedirect(reverse('chess:player', args=(obj.id,)))
    elif models.Event.objects.filter(object=pk).exists():
        return HttpResponseRedirect(reverse('chess:event', args=(obj.id,)))
    elif models.Opening.objects.filter(object=pk).exists():
        return HttpResponseRedirect(reverse('chess:opening', args=(obj.id,)))
    else:
        raise Http404("Requested object does not exists")


def comment(request, pk):
    obj = get_object_or_404(models.Object, id=pk)
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    comment = models.Comment(account=account,
                             object=obj,
                             text=request.POST['comment_text'])
    comment.save()
    return HttpResponseRedirect(reverse('chess:object', args=(obj.id,)))


def login(request):
    return render(request, 'chs/login.html')


def handle_login(request):
    if not request.POST['account']:
        return render(request, 'chs/login.html', {
            'error': "missing username"
        })
    if not request.POST['password']:
        return render(request, 'chs/login.html', {
            'error': "missing password"
        })
    try:
        account = models.Account.objects.get(pseudo=request.POST['account'])
        digest = hashlib.sha512(request.POST['password'].encode()).digest()
        if(digest != bytes(account.password)):
            return render(request, 'chs/login.html', {
                'error': "incorrect username or password"
            })
        request.session['account'] = account.id
        return HttpResponseRedirect(reverse('chess:mainpage'))
    except models.Account.DoesNotExist:
        return render(request, 'chs/login.html', {
            'error': "incorrect username or password"
        })


def logout(request):
    try:
        del request.session['account']
    except KeyError:
        pass
    request.session.flush()
    return HttpResponseRedirect(reverse('chess:mainpage'))


def register(request):
    return render(request, 'chs/register.html')


def handle_register(request):
    if not request.POST['account']:
        return render(request, 'chs/register.html', {
            'error': "missing username"
        })
    if not request.POST['password'] or not request.POST['password2']:
        return render(request, 'chs/register.html', {
            'error': "missing password"
        })
    if request.POST['password'] != request.POST['password2']:
        return render(request, 'chs/register.html', {
            'error': "passwords do not match"
        })
    if models.Account.objects.filter(pseudo=request.POST['account']).exists():
        return render(request, 'chs/register.html', {
            'error': "username already used"
        })
    account = models.Account(
        pseudo=request.POST['account'],
        password=hashlib.sha512(request.POST['password'].encode()).digest()
    )
    account.save()
    request.session['account'] = account.id
    return HttpResponseRedirect(reverse('chess:mainpage'))


def mainpage(request):
    return HttpResponseRedirect(reverse('chess:game_list'))
