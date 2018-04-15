from django.shortcuts import render

from django.http import HttpResponse

from .models import Game

def games(request):
    return HttpResponse(Game.objects.first())
