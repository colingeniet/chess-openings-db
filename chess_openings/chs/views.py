from django.http import Http404, HttpResponseRedirect
from django.views import generic
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.db.models.sql.constants import INNER, LOUTER
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


def can_edit(session, object):
    return ('account' in session and session['account']
            and models.has_edit_rights(session['account'], object))


class GameDetail(generic.DetailView):
    model = models.Game

    def get_context_data(self, **kwargs):
        context = super(GameDetail, self).get_context_data(**kwargs)
        context['openings'] = context['game'].openings()
        context['can_edit'] = can_edit(self.request.session, context['game'])
        return context


class PlayerDetail(generic.DetailView):
    model = models.Player

    def get_context_data(self, **kwargs):
        context = super(PlayerDetail, self).get_context_data(**kwargs)
        context['player_games'] = context['player'].games()[:50]
        context['can_edit'] = can_edit(self.request.session, context['player'])
        return context


class EventDetail(generic.DetailView):
    model = models.Event

    def get_context_data(self, **kwargs):
        context = super(EventDetail, self).get_context_data(**kwargs)
        context['event_games'] = context['event'].games()[:50]
        context['can_edit'] = can_edit(self.request.session, context['event'])
        return context


class OpeningDetail(generic.DetailView):
    model = models.Opening

    def get_context_data(self, **kwargs):
        context = super(OpeningDetail, self).get_context_data(**kwargs)
        opening = context['opening']
        context['opening_games'] = opening.games()[:50]
        context['variations'] = opening.variations()
        context['variation_of'] = opening.variation_of()
        context['can_edit'] = can_edit(self.request.session, opening)
        return context


# This is a big hack to get django to get django to do a weird join.
# The problem is with queries like 'games where either player is ...'.
# Such queries are best done with a single join :
#   chs_game JOIN chs_player ON
#   white_id = chs_player.object_id OR black_id = chs_player.object_id
#
# Unfortunaly, django is really not designed to do joins with strange
# conditions, such as join conditions with an OR.
# Equivalent queries that can easily be expressed through django are
# heavily inefficient (~10 times slower during my tests).

# This class is a hacked version of `django.db.models.sql.datastructures.Join`
# which is used has a join descriptor by `django.db.models.sql.query.Query`.
# It is responsible for producing the SQL code associated with the join,
# making it easy to change in order to do a custom join condition.
class PlayerLookupJoin(object):
    def __init__(self, parent_alias, condition, params):
        # Join table
        self.table_name = 'chs_player'
        self.parent_alias = parent_alias
        # Note: table_alias is not necessarily known at instantiation time.
        self.table_alias = None
        # LOUTER or INNER
        self.join_type = INNER
        # Is this join nullabled?
        self.nullable = False
        # Custom join condition. Takes the table alias to use as parameters.
        self.condition = condition
        # parameters for join condition
        self.params = params

    def as_sql(self, compiler, connection):
        qn = compiler.quote_name_unless_alias

        condition = '%s.white_id = %s.object_id OR %s.black_id = %s.object_id'
        condition = condition % (
            qn(self.parent_alias),
            qn(self.table_alias),
            qn(self.parent_alias),
            qn(self.table_alias),
        )

        custom_condition = self.condition(qn(self.table_alias))
        params = self.params

        on_clause_sql = '(%s) AND (%s)' % (condition, custom_condition)

        alias_str = '' if self.table_alias == self.table_name else (' %s' % self.table_alias)
        sql = '%s %s%s ON (%s)' % (self.join_type, qn(self.table_name), alias_str, on_clause_sql)
        return sql, params

    def relabeled_clone(self, change_map):
        new_parent_alias = change_map.get(self.parent_alias, self.parent_alias)
        new_table_alias = change_map.get(self.table_alias, self.table_alias)
        return self.__class__(
            self.table_name, new_parent_alias, new_table_alias, self.join_type,
            self.join_field, self.nullable)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.table_name == other.table_name and
                self.parent_alias == other.parent_alias
            )
        return False

    def demote(self):
        new = self.relabeled_clone({})
        new.join_type = INNER
        return new

    def promote(self):
        new = self.relabeled_clone({})
        new.join_type = LOUTER
        return new


class GameList(PaginatedListView):
    paginate_by = 50
    context_object_name = "game_list"

    def get_queryset(self):
        query = self.request.GET

        def is_set(attr):
            return attr in query and query[attr]

        result = models.Game.objects.all()
        if is_set('result'):
            result = result.filter(result=query['result'])
        if is_set('location'):
            result = result.filter(location__icontains=query['location'])
        if is_set('event'):
            result = result.filter(event__event_name__icontains=query['event'])
        if is_set('after'):
            result = result.filter(start_date__gte=query['after'])
        if is_set('before'):
            result = result.filter(start_date__lte=query['before'])
        if is_set('white'):
            result = result.filter(
                Q(white__lastname__icontains=query['white'])
                | Q(white__firstname__icontains=query['white'])
            )
        if is_set('white_nat'):
            result = result.filter(white__nationality=query['white_nat'])
        if is_set('white_elo_min'):
            result = result.filter(white__elo_rating__gte=query['white_elo_min'])
        if is_set('white_elo_max'):
            result = result.filter(white__elo_rating__lte=query['white_elo_max'])

        if is_set('black'):
            result = result.filter(
                Q(black__lastname__icontains=query['black'])
                | Q(black__firstname__icontains=query['black'])
            )
        if is_set('black_nat'):
            result = result.filter(white__nationality=query['black_nat'])
        if is_set('black_elo_min'):
            result = result.filter(black__elo_rating__gte=query['black_elo_min'])
        if is_set('black_elo_max'):
            result = result.filter(black__elo_rating__lte=query['black_elo_max'])

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

        if is_set('player'):
            def condition(table):
                sql = 'UPPER(%s.lastname) = UPPER(%s) OR UPPER(%s.firstname) = UPPER(%s)'
                return sql % (table, '%s', table, '%s')

            join = PlayerLookupJoin(
                result.query.get_initial_alias(),
                condition,
                [query['player'], query['player']]
            )
            result.query.join(join, [])
        if is_set('player_nat'):
            def condition(table):
                sql = '%s.nationality = %s'
                return sql % (table, '%s')

            join = PlayerLookupJoin(
                result.query.get_initial_alias(),
                condition,
                [query['player_nat']]
            )
            result.query.join(join, [])
        if is_set('player_elo_min'):
            def condition(table):
                sql = '%s.elo_rating >= %s'
                return sql % (table, '%s')

            join = PlayerLookupJoin(
                result.query.get_initial_alias(),
                condition,
                [query['player_elo_min']]
            )
            result.query.join(join, [])
        if is_set('player_elo_max'):
            def condition(table):
                sql = '%s.elo_rating <= %s'
                return sql % (table, '%s')

            join = PlayerLookupJoin(
                result.query.get_initial_alias(),
                condition,
                [query['player_elo_max']]
            )
            result.query.join(join, [])
        return result.order_by('start_date')

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
    paginate_by = 50

    def get_queryset(self):
        query = self.request.GET

        def is_set(attr):
            return attr in query and query[attr]

        result = models.Player.objects
        if is_set('name'):
            result = result.filter(
                Q(firstname__icontains=query['name'])
                | Q(lastname__icontains=query['name']))
        if is_set('elo_min'):
            result = result.filter(elo_rating__gte=query['elo_min'])
        if is_set('elo_max'):
            result = result.filter(elo_rating__lte=query['elo_max'])
        if is_set('nationality'):
            result = result.filter(nationality=query['nationality'])
        return result.order_by('lastname')


class EventList(PaginatedListView):
    paginate_by = 50

    def get_queryset(self):
        query = self.request.GET

        def is_set(attr):
            return attr in query and query[attr]

        result = models.Event.objects
        if is_set('name'):
            result = result.filter(event_name__icontains=query['name'])
        if is_set('location'):
            result = result.filter(location__icontains=query['location'])
        if is_set('after'):
            result = result.filter(start_date__gte=query['after'])
        if is_set('before'):
            result = result.filter(start_date__lte=query['before'])
        return result.order_by('start_date')


class OpeningList(PaginatedListView):
    paginate_by = 50

    def get_queryset(self):
        query = self.request.GET

        def is_set(attr):
            return attr in query and query[attr]

        result = models.Opening.objects
        if is_set('name'):
            result = result.filter(opening_name__icontains=query['name'])
        return result.order_by('opening_name')


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


def create_player(request):
    return render(request, 'chs/player_create.html')


def create_event(request):
    return render(request, 'chs/event_create.html')


def create_opening(request):
    return render(request, 'chs/opening_create.html')


def edit_game(request, pk):
    game = get_object_or_404(models.Game, object_id=pk)
    return render(request, 'chs/game_create.html', {'game': game})


def edit_player(request, pk):
    player = get_object_or_404(models.Player, object_id=pk)
    return render(request, 'chs/player_create.html', {'player': player})


def edit_event(request, pk):
    event = get_object_or_404(models.Event, object_id=pk)
    return render(request, 'chs/event_create.html', {'event': event})


def edit_opening(request, pk):
    opening = get_object_or_404(models.Opening, object_id=pk)
    return render(request, 'chs/opening_create.html', {'opening': opening})


def add_game(request):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    if 'id' in request.POST and request.POST['id']:
        game = get_object_or_404(models.Game, object_id=request.POST['id'])
        if not account.has_edit_rights(game):
            return render(request, 'chs/error.html', {
                'error': "you can not edit this object"
            })
    else:
        obj = models.create_obj(account)
        game = models.Game(object=obj)

    if not (request.POST['moves'] and request.POST['result']):
        return render(request, 'chs/error.html', {
            'error': "missing game information"
        })
    game.moves = pgn.encode_moves_from_uci(request.POST['moves'].split(','))
    game.result = request.POST['result']
    if request.POST['event']:
        game.event = models.find_or_add_event(request.POST['event'], account)
    else:
        game.event = None
    game.location = request.POST.get('location')
    if not game.location:
        game.location = None
    game.date = request.POST.get('date')
    if not game.date:
        game.date = None

    white_fn = request.POST.get('white_first', "")
    white_ln = request.POST.get('white_last', "")
    if white_fn or white_ln:
        game.white = models.find_or_add_player(white_fn, white_ln, account)
    else:
        game.white = None

    black_fn = request.POST.get('black_first', "")
    black_ln = request.POST.get('black_last', "")
    if black_fn or black_ln:
        game.black = models.find_or_add_player(black_fn, black_ln, account)
    else:
        game.black = None

    game.save()
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


def add_player(request):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    if 'id' in request.POST and request.POST['id']:
        player = get_object_or_404(models.Player, object_id=request.POST['id'])
        if not account.has_edit_rights(player):
            return render(request, 'chs/error.html', {
                'error': "you can not edit this object"
            })
    else:
        obj = models.create_obj(account)
        player = models.Player(object=obj)

    player.firstname = request.POST.get('firstname', "")
    player.lastname = request.POST.get('lastname', "")
    player.elo_rating = request.POST.get('elo')
    if not player.elo_rating:
        player.elo_rating = None
    player.nationality = request.POST.get('nationality')
    if not player.nationality:
        player.nationality = None

    player.save()
    return HttpResponseRedirect(reverse('chess:player_list'))


def add_event(request):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    if 'id' in request.POST and request.POST['id']:
        event = get_object_or_404(models.Event, object_id=request.POST['id'])
        if not account.has_edit_rights(event):
            return render(request, 'chs/error.html', {
                'error': "you can not edit this object"
            })
    else:
        obj = models.create_obj(account)
        event = models.Event(object=obj)

    event.event_name = request.POST['event_name']
    event.location = request.POST.get("location")
    if not event.location:
        event.location = None
    event.start_date = request.POST.get('start_date')
    if not event.start_date:
        event.start_date = None
    event.end_date = request.POST.get('end_date')
    if not event.end_date:
        event.end_date = None

    event.save()
    return HttpResponseRedirect(reverse('chess:event_list'))


def add_opening(request):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    if 'id' in request.POST and request.POST['id']:
        opening = get_object_or_404(models.Opening, object_id=request.POST['id'])
        if not account.has_edit_rights(opening):
            return render(request, 'chs/error.html', {
                'error': "you can not edit this object"
            })
        new = False
    else:
        obj = models.create_obj(account)
        opening = models.Opening(object=obj)
        new = True

    if not (request.POST['moves']):
        return render(request, 'chs/error.html', {
            'error': "missing game information"
        })
    opening.moves = pgn.encode_moves_from_uci(request.POST['moves'].split(','))
    if not (request.POST['opening_name']):
        return render(request, 'chs/error.html', {
            'error': "missing opening name"
        })
    opening.opening_name = request.POST['opening_name']
    if new and models.Opening.objects.filter(opening_name=opening.opening_name).exists():
        return render(request, 'chs/error.html', {
            'error': "opening name already used"
        })

    opening.save()
    return HttpResponseRedirect(reverse('chess:opening_list'))


def delete_game(request, pk):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    game = get_object_or_404(models.Game, object_id=pk)
    if not account.has_edit_rights(game):
        return render(request, 'chs/error.html', {
            'error': "you can not delete this object"
        })
    game.delete()
    return HttpResponseRedirect(reverse('chess:game_list'))


def delete_player(request, pk):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    player = get_object_or_404(models.Player, object_id=pk)
    if not account.has_edit_rights(player):
        return render(request, 'chs/error.html', {
            'error': "you can not delete this object"
        })
    player.delete()
    return HttpResponseRedirect(reverse('chess:player_list'))


def delete_event(request, pk):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    event = get_object_or_404(models.Event, object_id=pk)
    if not account.has_edit_rights(event):
        return render(request, 'chs/error.html', {
            'error': "you can not delete this object"
        })
    event.delete()
    return HttpResponseRedirect(reverse('chess:event_list'))


def delete_opening(request, pk):
    try:
        account = models.Account.objects.get(id=request.session['account'])
    except (KeyError, models.Account.DoesNotExist):
        return render(request, 'chs/error.html', {
            'error': "incorrect login informations"
        })
    opening = get_object_or_404(models.Opening, object_id=pk)
    if not account.has_edit_rights(opening):
        return render(request, 'chs/error.html', {
            'error': "you can not delete this object"
        })
    opening.delete()
    return HttpResponseRedirect(reverse('chess:opening_list'))


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
        if 'next' in request.POST:
            path = request.POST['next']
        else:
            path = '/'
        return HttpResponseRedirect(path)
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
    if 'next' in request.GET:
        path = request.GET['next']
    else:
        path = '/'
    return HttpResponseRedirect(path)


def register(request):
    return render(request, 'chs/register.html')


def handle_register(request):
    if not request.POST['account']:
        return render(request, 'chs/register.html', {
            'error': "missing username"
        })
    if not request.POST['password']:
        return render(request, 'chs/register.html', {
            'error': "missing password"
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
    if 'next' in request.POST:
        path = request.POST['next']
    else:
        path = '/'
    return HttpResponseRedirect(path)


def mainpage(request):
    return HttpResponseRedirect(reverse('chess:game_list'))
