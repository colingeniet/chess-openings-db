from django.conf.urls import url

from . import views

urlpatterns = [
    url('games', views.games, name='games'),
]
