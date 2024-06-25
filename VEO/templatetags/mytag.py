from django import template
from VEO.models import Veoservices
  

register = template.Library()

@register.simple_tag
def get_total_a_traiter():
    return Veoservices.objects.filter(statutdoute="Non traité").count()
