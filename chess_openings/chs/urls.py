from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^game/(?P<pk>[0-9]+)/$',
        views.GameDetail.as_view(),
        name='game'),
    url(r'^game/$',
        views.GameList.as_view(),
        name='game_list'),
    url(r'^player/(?P<pk>[0-9]+)/$',
        views.PlayerDetail.as_view(),
        name='player'),
    url(r'^player/$',
        views.PlayerList.as_view(),
        name='player_list'),
    url(r'^event/(?P<pk>[0-9]+)/$',
        views.EventDetail.as_view(),
        name='event'),
    url(r'^event/$',
        views.EventList.as_view(),
        name='event_list'),
    url(r'^opening/(?P<pk>[0-9]+)/$',
        views.OpeningDetail.as_view(),
        name='opening'),
    url(r'^opening/$',
        views.OpeningList.as_view(),
        name='opening_list'),
]
