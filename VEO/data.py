import pandas as pd
from .models import Veoservices
from django.db.models import Count
from django.db.models import Q

def get_veoservices_for_dash():
    queryset = Veoservices.objects.values('Procédure').annotate(
        nombre_dossiers=Count('Procédure'),
        doute_general=Count('Dossier', filter=Q(statutdoute='Doute confirmé') | Q(statutdoute='Doute rejeté') | Q(statutdoute='Attente Photos Avant')),
        doute_confirme=Count('Dossier', filter=Q(statutdoute='Doute confirmé')),
        doute_rejete=Count('Dossier', filter=Q(statutdoute='Doute rejeté'))
    ).order_by('Procédure')
    df = pd.DataFrame(list(queryset))
    #print(df)  
    return df


