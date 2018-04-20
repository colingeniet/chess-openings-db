from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^game/(?P<pk>[0-9]+)/$', views.GameDetail.as_view(), name='game'),
    url(r'^player/(?P<pk>[0-9]+)/$', views.PlayerDetail.as_view(), name='player'),
    url(r'^event/(?P<pk>[0-9]+)/$', views.EventDetail.as_view(), name='event'),
    url(r'^game/$', views.game_list, name='game_list'),
]
