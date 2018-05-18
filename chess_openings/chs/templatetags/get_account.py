from django import template
from chs.models import Account

register = template.Library()


@register.filter
def get_account(value):
    try:
        return Account.objects.get(id=int(value))
    except Account.DoesNotExist:
        return "error"
