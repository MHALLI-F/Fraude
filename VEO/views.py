from os import lseek
from django.shortcuts import render, get_object_or_404
from .models import Veodata, Assistance, Bris_De_Glace, Veoservices,veotest

import datetime
from datetime import  timedelta


from django.utils.timezone import is_aware, make_naive, get_current_timezone

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.core.serializers import serialize
import json
from django.db.models.functions import Cast , Coalesce
from django.core.serializers.json import DjangoJSONEncoder
import psycopg2
import gzip
from django.http import FileResponse
from django.db.models import FloatField, F, Case, When, Value
import csv
from django.db.models import Q
from django.db.models import FloatField, ExpressionWrapper, F, Case, When
from django.db.models import CharField
from django.db.models.functions import Cast
from .models import Veoservices, Veodata, Collaborateur
from django.db import models
from django.db.models import DateTimeField
from django.utils.timezone import now

from .dash_app import app as dash_app  
from django.http import JsonResponse
from .data import get_veoservices_for_dash  
from django.shortcuts import render
from django.db.models import Sum
import re
from django.urls import reverse, resolve

from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.urls import resolve
from .models import Veoservices
import datetime
from django.db.models.functions import TruncMonth
from django.db.models import Count, Avg
from django.core.serializers.json import DjangoJSONEncoder
import json

logger = logging.getLogger(__name__)

def get_data_for_chart():
    data = Veoservices.objects.values('Procédure').annotate(
        total_dossiers=Count('id'),
        douteux_dossiers=Count('id', filter=Q(RateFraude__gt=30.0))  
    ).order_by('Procédure')
    return list(data)

def get_confirmed_doubt_data():
    three_months_ago = datetime.datetime.now() - timedelta(days=150)
    data = Veoservices.objects.filter(
        date_creation_nv__gte=three_months_ago,
        statutdoute='Doute confirmé'
    ).values('statutdoute').annotate(
        count=Count('id'),
        average_fraud_rate=Avg('RateFraude')
    ).order_by('statutdoute')  

    formatted_data = [
        {
            'statutdoute': item['statutdoute'],
            'count': item['count'],
            'average_fraud_rate': item['average_fraud_rate']
        }
        for item in data
    ]
    return formatted_data



def get_garage_fraud_data():
    three_months_ago = datetime.datetime.now() - timedelta(days=150)
    data = Veoservices.objects.filter(date_creation_nv__gte=three_months_ago)
    return data.values('GaragePN').annotate(
        count=Count('id'), 
        average_fraud_rate=Avg('RateFraude')
    ).order_by('GaragePN')

def get_expert_fraud_data():
    three_months_ago = datetime.datetime.now() - timedelta(days=150)

    # Filtrer les données en excluant les valeurs spécifiques dans `Statut`
    data = Veoservices.objects.filter(
        date_creation_nv__gte=three_months_ago
    ).filter(
        ~Q(Statut__iexact='Changement procédure') & 
        ~Q(Statut__iexact='Expert Test') & 
        ~Q(Statut__iexact='Garage Test') & 
        ~Q(Statut__iexact='Dossier sans suite') & 
        ~Q(Statut__iexact='Dossier sans suite après expertise')
    )

    # Annoter les résultats pour obtenir les compteurs et le taux moyen de fraude
    data = data.values('Expert').annotate(
        count=Count('id'), 
        average_fraud_rate=Avg('RateFraude')
    ).order_by('Expert')

    return list(data)

def get_fraud_data():
    three_months_ago = datetime.datetime.now() - timedelta(days=150)
    data = Veoservices.objects.filter(date_creation_nv__gte=three_months_ago, RateFraude__gte=30.0)
    data = data.annotate(month=TruncMonth('date_creation_nv')).values('month').annotate(
        count=Count('id'),
        average_fraud_rate=Avg('RateFraude')
    ).order_by('month')
    
    formatted_data = [
        {
            'month': item['month'].strftime('%Y-%m'), 
            'count': item['count'],
            'average_fraud_rate': item['average_fraud_rate']
        }
        for item in data
    ]

    return formatted_data
def dashboard_data(request): 
    data = get_veoservices_for_dash()
    fraud_data = get_fraud_data()
    expert_data = get_expert_fraud_data()
    garage_data = get_garage_fraud_data()
    confirmed_doubt_data = get_confirmed_doubt_data()
    data_for_chart = get_data_for_chart()  
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    total_a_traiter = nbrDAT()

    context = {
        'SupUse': SupUse(request),
        'user_name': user_name,
        'total_a_traiter': total_a_traiter,
        'data': data.to_json(orient='records'),
        'fraud_data': json.dumps(fraud_data, cls=DjangoJSONEncoder),  
        'expert_data': json.dumps(expert_data, cls=DjangoJSONEncoder),
        'garage_data': garage_data,
        'confirmed_doubt_data': json.dumps(confirmed_doubt_data, cls=DjangoJSONEncoder),
        'data_for_chart': json.dumps(data_for_chart, cls=DjangoJSONEncoder)  
    }
    return render(request, 'chart.html', context)



    
def chart(request):
    dash_url = 'http://92.222.221.200:9009/dashboard/'
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    total_a_traiter = nbrDAT()
    context = {'dash_url': dash_url,
               'total_a_traiter': total_a_traiter,
               'user_name': user_name,
                'SupUse': SupUse(request)  
    }
    return render(request, 'chart.html', context)


@login_required
def filter_veoservices_by_date_and_status(request, template_name='home.html'):
    is_supuse = SupUse(request)
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    return filter_veoservices_helper(request, template_name, is_supuse, user_name)

@login_required
def filter_veoservices_by_date_and_statusAT(request, template_name='dossieratrait.html'):
    is_supuse = SupUse(request)
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    return filter_veoservices_helper(request, template_name, is_supuse, user_name)

@login_required
def filter_veoservices_by_date_and_statusT(request, template_name='dossiertrait.html'):
    is_supuse = SupUse(request)
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    return filter_veoservices_helper(request, template_name, is_supuse, user_name)

def filter_veoservices_helper(request, template_name, is_supuse, user_name):
    queryset = Veoservices.objects.all()
    fixed_date = request.GET.get('fixed_date')
    statut = request.GET.get('statut')

    if fixed_date and statut:
        try:
            parsed_date = datetime.datetime.strptime(fixed_date, '%Y-%m-%d')
            start_date = parsed_date.date()  # utilise la date sans heure
            end_date = (parsed_date + timedelta(days=1)).date()
            statuts_valide = [
                "Dossier créé", "Dossier envoyé", "Rdv replanifié", "CDC envoyé au garage",
                "Photos Avant", "Offre communiquée", "Devis envoyé par le garage",
                "Instance Accord compagnie", "Instance Accord Expert2", "Accord à modifier",
                "Accord à envoyer", "Devis validé", "Demande 2e accord", "Attente facture",
                "Instance FFT/rapport", "Instance RDV Client", "Instance publication rapport",
                "Dossier complété", "Dossier réglé", "Dossier sans suite",
                "Dossier sans suite après expertise", "Annulé par l'expert",
                "Dossier traité en Hifad", "Rapport rejeté", "Changement procédure",
                "Dossier en instruction", "Dossier rejeté"
            ]
            if statut in statuts_valide:
                queryset = queryset.filter(
                    date_creation_nv__gte=start_date,
                    date_creation_nv__lt=end_date,
                    Statut=statut
                )
        except ValueError:
            pass

    else:
        if fixed_date:
            try:
                parsed_date = datetime.datetime.strptime(fixed_date, '%Y-%m-%d')
                start_date = parsed_date.date()  
                end_date = (parsed_date + timedelta(days=1)).date()
                queryset = queryset.filter(date_creation_nv__gte=start_date, date_creation_nv__lt=end_date)
            except ValueError:
                pass

        if statut:
            statuts_valide = [
                "Dossier créé", "Dossier envoyé", "Rdv replanifié", "CDC envoyé au garage",
                "Photos Avant", "Offre communiquée", "Devis envoyé par le garage",
                "Instance Accord compagnie", "Instance Accord Expert2", "Accord à modifier",
                "Accord à envoyer", "Devis validé", "Demande 2e accord", "Attente facture",
                "Instance FFT/rapport", "Instance RDV Client", "Instance publication rapport",
                "Dossier complété", "Dossier réglé", "Dossier sans suite",
                "Dossier sans suite après expertise", "Annulé par l'expert",
                "Dossier traité en Hifad", "Rapport rejeté", "Changement procédure",
                "Dossier en instruction", "Dossier rejeté"
            ]
            if statut in statuts_valide:
                queryset = queryset.filter(Statut=statut)

    # Exclure les enregistrements où RateFraude est None pour 'dossieratrait.html'
    if template_name == 'dossieratrait.html':
        queryset = queryset.exclude(RateFraude__isnull=True)

    # Exclure les dossiers avec statut doute 'Non traité' pour 'dossiertrait.html'
    if template_name == 'dossiertrait.html':
        queryset = queryset.exclude(statutdoute='Non traité')

    paginator = Paginator(queryset, 9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {'list_Veo_recente': veopg, 'user_name': user_name}
    return render(request, template_name, context)

@login_required
def filter_by_rate_fraude(request):
    
    exact_fraude_rate = request.GET.get('fraude_min', None)

    
    if exact_fraude_rate:
        list_Veo_recente = Veoservices.objects.filter(
            RateFraude=exact_fraude_rate  
        ).order_by('-RateFraude') 
    else:
        list_Veo_recente = Veoservices.objects.all().order_by('-RateFraude')

    
    paginator = Paginator(list_Veo_recente, 9)  
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {
        "list_Veo_recente": veopg,
        "SupUse": SupUse(request), 
        "user_name": f"{request.user.first_name} {request.user.last_name}".strip()
    }

    return render(request, "dossieratrait.html", context)





def send_test_email(request):
    send_mail(
        'Test veosmart',
        'Ta7iyaa l a7laaa ftoomaa zin t3alam mhm ha tanjrb wahd l3iba fik .',
        'khadija.elwazati@gmail.com',  
        ['f.mhalli@veosmart.ma'],  
        fail_silently=False,
    )
    return HttpResponse("Email envoyé avec succès!")

def send_fraud_alert(service):
    rate_fraude = service.RateFraude
    if rate_fraude is None:
        print(f"Service {service.id}: RateFraude est None, aucune action nécessaire.")
        return "RateFraude est None, aucune action nécessaire."

    try:
        rate_fraude_float = float(rate_fraude)
    except ValueError:
        print(f"Service {service.id}: Valeur non valide pour RateFraude: {rate_fraude}")
        return f"Valeur non valide pour RateFraude: {rate_fraude}"

    
    collaborateurs = Collaborateur.objects.all()
    emails = [coll.email for coll in collaborateurs]

    if rate_fraude_float > 50.0:
        try:
            link = f"https://fraude.omegasin.ma{reverse('details', kwargs={'Dossier': service.id})}"
            print(f"Service {service.id}: Lien d'alerte email généré : {link}")
        except Exception as e:
            print(f"Service {service.id}: Erreur lors de la génération du lien : {e}")
            return f"Erreur lors de la génération du lien : {e}"

        context = {
            'dossier_reference': service.Dossier,
            'immatriculation': service.Immatriculation,
            'date_sinistre': service.Date_sinistre,
            'rate_fraude': rate_fraude_float,
            'link': link
        }

        subject = f"Alerte de Fraude Élevée pour le Dossier {context['dossier_reference']}"

        html_message = render_to_string('fraud_alert_email.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.EMAIL_HOST_USER,
                emails,  
                html_message=html_message,
                fail_silently=False,
            )
            print(f"Service {service.id}: Notification envoyée avec succès aux emails : {', '.join(emails)}")
            return f"Notification envoyée avec succès aux emails : {', '.join(emails)}"
        except Exception as e:
            print(f"Service {service.id}: Erreur lors de l'envoi de l'email : {e}")
            return f"Erreur lors de l'envoi de l'email : {e}"
    else:
        print(f"Service {service.id}: Aucune notification nécessaire.")
        return "Aucune notification nécessaire."



def test_fraud_alert(request):
    veoservices = Veoservices.objects.all()
    
    for service in veoservices:
        result = send_fraud_alert(service)
        print(result)  

    return HttpResponse("Tous les enregistrements traités")







#def check_and_send_fraud_alert(request, veoservice_id):
    #veoservice = get_object_or_404(Veoservices, id=veoservice_id)
    #if veoservice.RateFraude > 50.0:
     #   return send_fraud_alert(request, veoservice_id)
    #return HttpResponse("Mise à jour effectuée et aucune notification envoyée.")
# nettoyage  de  numéro de  chassis 
def net_numch(a):
    a=a.replace(' ','').replace('-','').replace('_','').replace(',','').replace('.','').replace('*','')
    return a

def inter_dt(dtV , dtE):
    if (dtV and dtE):
        dtV = datetime.strptime(dtV, "%d/%m/%Y").date()
        dtE = datetime.strptime(dtE, "%d/%m/%Y").date()
        return abs(dtV - dtE).days
def inter_dt2(dtV , dtE):
    if (dtV and dtE):
        dtE = datetime.strptime(dtE, "%d/%m/%Y").date()
        dtV = datetime.strptime(dtV, "%d %b, %Y %H:%M:%S").date()
        return (dtV - dtE).days

################################################################### Nettoyage des immatriculations
#Enlever les zéros de début
def remove_zerostart (val):
    i=0
    while (val.startswith('0') and i<len(val)):
        l=list(val)
        l[0]=''
        i=i+1
        val = ''.join(l)
    return val

#Enlever les "WW" à la fin
def remove_WW(a):
    if a.endswith("WW"):
        a= ''.join(list(a)[0:-2])
        if(a.startswith("WW")):
            return a
        else :
            return "WW"+a
    else:
        return a

#Enlever les zeros après les "WW" de début
def remove_WW0(a):
    if a.startswith("WW0"):
        a=''.join(list(a)[2:])
        a=remove_zerostart(a)
        a="WW"+a
        return a
    else:
        return a

#Enlever le mot "EAD" s'il existe
def remove_EAD(a):
    if (a.startswith("EAD")):
        return ''.join(list(a)[3:])
    else:
        return a

#Ajouter le le zéro après le caractère (B7 ==> B07)
def add_zero(a):
    if (len(a) <= 2 or a != '' or not (a is None)):
        if (a[-1].isdigit() and (not a[-2].isdigit())):
            res=list(a)[0:-1]
            res.append("0")
            res.append(a[-1])
            return ''.join(res)
        else:
            return a
    else:
        return a

#Enlever les imm qui contient que des chiffres ou bien que des caractères
def test(a):
    b=''.join(i for i in a if i.isdigit())
    c=''.join(i for i in a if not (i.isdigit()))
    if ((len(b) == len(a)) or ((len(c) == len(a)))):
        return ""
    else:
        return a


#Preprocessing "Immatriculation" (Appeler toutes les fcts défénies)
def Preprocessing_Imm (a):
    if a!=None:
        a=remove_EAD(a)
        a=a.strip()
        a=a.upper()
        a=a.replace(" ", "")
        a=a.replace("/", "")
        a=a.replace("'", "")
        a=a.replace(".", "")
        a=a.replace('-','')
        a=remove_zerostart(a)
        a=remove_WW(a)
        a=remove_WW0(a)
        if (a != '' and not(a is None)):
            a=add_zero(a)
            a=test(a)
            return a


#Convertir Rate fraude de string to float
def str_to_float(stri):
    if stri == "" or stri == "'0.0'" or stri  == None:
        stri=0.0
    else:
        stri=float(stri)
    return stri

#changement fonct
def extraction_traitement(request):
    try:
        with closing(psycopg2.connect(host='0.0.0.0', port=5432, dbname='veo', user='postgres', password='MDPveosmart@123')) as conn:
            with conn.cursor() as cur:
                file_path = '/home/extraction/dossierstraités.csv'
                with open(file_path, 'w', newline='') as fid:
                    sql = 'COPY (SELECT * FROM public."VEO_veoservices") TO STDOUT WITH (FORMAT CSV, HEADER, ENCODING "UTF-8");'
                    cur.copy_expert(sql, fid)
                with open(file_path, 'rb') as fd:
                    return FileResponse(fd, as_attachment=True, filename='Extraction_dossierstraités.csv')
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}", status=500)


#cette fonc prend 22s tahiya l FZ ila qriti code sifti lia wslat ta7iya 
#@login_required
#def inis(request):
    #Today_DateVeo = datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    #Today_DateVeo = datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    #NBDAT = nbrDAT()
    #list_Veo_recente = []
    #list_Veoservices = Veoservices.objects.all()

    #for veo in list_Veoservices:
        #if veo.Date_création:
            #veo.Date_création = datetime.datetime.strptime(veo.Date_création, '%d/%m/%Y %H:%M')
            #veo.RateFraude = str_to_float(veo.RateFraude)
        #if veo.Statut != "Changement procédure" and veo.RateFraude == 60.0:
            #list_Veo_recente.append(veo)

    # Trier la liste par Date_création en ordre décroissant
    #list_Veo_recente.sort(key=lambda r: r.Date_création, reverse=True)

    #paginator = Paginator(list_Veo_recente, 9)
    #page = request.GET.get('page')
    #veopg = paginator.get_page(page)

    #context = {"SupUse": SupUse(request), "list_Veo_recente": veopg, "NBDossiers": NBDAT}
    #return render(request, "home.html", context)


#cette fonc me donne en temps 9s tahiya l FZ ila qriti code sifti lia wslat ta7iya 
#@login_required
#def inis(request):
    #today_date_veo = datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    #today_date_veo = datetime.datetime.strptime(today_date_veo, '%d/%m/%Y %H:%M')
    #nb_dat = nbrDAT()

    #def safe_float(value):
        #try:
            #return float(value)
        #except (ValueError, TypeError):
            #return None

    #list_veoservices = Veoservices.objects.all()
    #filtered_veoservices = []
    #for veo in list_veoservices:
        # Convertir RateFraude en float, gérer les valeurs non numériques
        #rate_fraude_float = safe_float(veo.RateFraude)
        #if rate_fraude_float is not None:  
            #veo.rate_fraude_float = rate_fraude_float
            #filtered_veoservices.append(veo)

    # Filtrer pour obtenir les entrées avec un taux de fraude de 60.0 et un statut changeement de procedure 
    #list_veo_recente = [veo for veo in filtered_veoservices if veo.rate_fraude_float == 60.0 and veo.Statut != "Changement procédure"]

    #list_veo_recente.sort(key=lambda r: r.Date_création, reverse=True)
    #paginator = Paginator(list_veo_recente, 9)
    #page = request.GET.get('page')
    #veopg = paginator.get_page(page)

    #context = {
        #"SupUse": SupUse(request),
        #"list_Veo_recente": veopg,
        #"NBDossiers": nb_dat
    #}
    #return render(request, "home.html", context)

@login_required
def inis(request):
    current_url = resolve(request.path_info).url_name
    display_data = (current_url == 'inis')

    nbdat = nbrDAT()  
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()

    total_a_traiter = total_traite = total_doute_confirme = moyenne_doute = 0
    veopg = None

    if display_data:
        total_a_traiter = nbdat
        total_dossiers = Veoservices.objects.count()

        if total_dossiers > 0:
            total_traite = Veoservices.objects.filter(statutdoute__in=['Doute confirmé', 'Doute rejeté']).count()
            total_doute_confirme = Veoservices.objects.filter(statutdoute='Doute confirmé').count()

            rate_fraude_values = Veoservices.objects.exclude(Q(RateFraude__isnull=True) | Q(RateFraude=0.0)).values_list('RateFraude', flat=True)
            if rate_fraude_values:
                total_rate_fraude = sum(rate_fraude_values)
                moyenne_doute = total_rate_fraude / len(rate_fraude_values) if rate_fraude_values else 0

        five_days_ago_start_of_day = datetime.datetime.now() - datetime.timedelta(days=6)
        list_veo_recente = Veoservices.objects.filter(
            date_creation_nv__gte=five_days_ago_start_of_day
        ).exclude(
            Q(Statut="Changement de procédure") | Q(Expert="Expert Test") | Q(RateFraude__isnull=True) | Q(RateFraude=0.0) | Q(RateFraude=5.0) | Q(RateFraude=10.0)
        ).order_by('statutdoute')

        paginator = Paginator(list_veo_recente, 9)
        page = request.GET.get('page')
        try:
            veopg = paginator.get_page(page)
        except PageNotAnInteger:
            veopg = paginator.get_page(1)
        except EmptyPage:
            veopg = paginator.get_page(paginator.num_pages)

    context = {
        "list_Veo_recente": veopg,
        "NBDossiers": total_dossiers,
        "total_a_traiter": total_a_traiter,
        "total_traite": total_traite,
        "total_doute_confirme": total_doute_confirme,
        "moyenne_doute": moyenne_doute,
        "display_data": display_data,
        'user_name': user_name,
        'SupUse': SupUse(request)  
    }

    return render(request, "home.html", context)




@login_required
def details(request, Dossier):
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    total_a_traiter = nbrDAT()
    Veo=get_object_or_404(Veoservices,id=Dossier)
    Rate=Veo.RateFraude
    NBD=nbrDAT()
    NBDT=nbrDT()
    ls=Veo.Reg1()
    R1=ls[0]
    R1_P=ls[1]
    R1_A=ls[2]
    ls=Veo.Reg2()
    R2=ls[0]
    R2_DDA=ls[1]
    R2_DS=ls[2]
    ls=Veo.Reg3()
    R3=ls[0]
    R3_DDA=ls[1]
    R3_DS=ls[2]
    ls=Veo.Reg4()
    R4=ls[0]
    R4_SP=ls[1]
    R4_SA=ls[2]
    ls=Veo.Reg5()
    R5=ls[0]
    #Dossier assistance qui à la  date moins  de 7h et plus de 20h
    R5_Assis=ls[1]
    ls=Veo.Reg6()
    R6=ls[0]
    #Les  deux dossiers Assistance qui ne dépassent pas 3 mois
    R6_Assis1=ls[1]
    R6_Assis2=ls[2]
    ls=Veo.Reg7()
    R7=ls[0]
    R7_P=ls[1]
    R7_A=ls[2]
    ls=Veo.Reg9()
    R9=ls[0]
    R9_DFP=ls[1]
    R9_DS=ls[2]

    R8=Veo.Reg8()
    ls=Veo.Reg10()
    R10=ls[0]
    R10_Dos=ls[1]
    ls=Veo.Reg12()
    R12=ls[0]
    R12_Dos=ls[1]
    

    R11=Veo.Reg11()
    ls=Veo.Reg13()
    R13=ls[0]
    R13_Dos=ls[1]
    
    R14 =Veo.Reg14()
    #ls =Veo.Reg15()
    #R15=ls[0]
    #R15_CN=ls[1]
    #ls =Veo.Reg16()
    #R16=ls[0]
    #R16_Dos=ls[1]
    #ls =Veo.Reg17()
    #R17=ls[0]
    #R17_Int=ls[1]
    # Vérifier si c'est superuser
    Rate = R1 + R2 + R3 + R4 + R5 + R6 + R7 + R8 + R9 + R10 + R11 + R12 + R13 + R14 
    if Rate<=100:  
        Veoservices.objects.filter(id=Dossier).update(RateFraude=round(Rate,2))   
    

# si le pourcentage est  supérieure à 100% -> 100%
    else:
        Rate>=100
        Veoservices.objects.filter(id=Dossier).update(RateFraude=100)
    

    if request.user.is_superuser:
        SupUse = True
    else:
        SupUse = False
    context={"SupUse":SupUse,'user_name': user_name, "total_a_traiter": total_a_traiter,"NBDT":NBDT,"NBDossiers":NBD,"Veo":Veo,"Rate":Rate ,"R1": R1,"R1_P": R1_P, "R1_A":R1_A, "R2":R2, "R2_DDA":R2_DDA, "R2_DS":R2_DS,"R3":R3, "R3_DDA":R3_DDA, "R3_DS":R3_DS, "R4":R4, "R4_SP":R4_SP, "R4_SA":R4_SA,"R5":R5 ,"R5_Assis":R5_Assis ,"R6":R6,"R6_Assis1":R6_Assis1 ,"R6_Assis2":R6_Assis2,"R7":R7,"R7_P":R7_P,"R7_A":R7_A, "R9_DFP":R9_DFP, "R9_DS":R9_DS, "R9":R9,"R8":R8,"R11":R11, "R10_Dos":R10_Dos,"R10":R10 , "R12_Dos":R12_Dos,"R12":R12 , "R13_Dos":R13_Dos,"R13":R13, "R14":R14} #,"R17_Int":R17_Int ,"R17":R17 , "R15":R15,"R15_CN":R15_CN,}

    return render(request,"detail.html",context)
#def nbrDAT():
    #NBD=0
    #Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    #Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    #today_date_veo = datetime.datetime.today()
    #five_days_ago = today_date_veo - datetime.timedelta(days=5)

    # Utilisation d'une requête filtrée pour réduire le nombre d'objets chargés en mémoire
    #list_veoservices = Veoservices.objects.annotate(
        #string_rate_fraude=Cast('RateFraude', output_field=CharField())
    #).filter(
        #Date_création__isnull=False,
        #Date_création__gte=five_days_ago.strftime('%d/%m/%Y %H:%M')
    #).filter(
        #Q(
            #(Q(statutdoute="Non traité") & ~Q(Statut="Changement de procédure") & Q(string_rate_fraude__in=['0', '0.0', '5.0', '10.0'])) |
            #(Q(statutdoute="Attente photos Avant") & ~Q(Photos_Avant="") & Q(Photos_Avant__isnull=False) & ~Q(Statut="Changement de procédure") & Q(string_rate_fraude__in=['0', '0.0', '5.0', '10.0']))
        #)
    #)

    # Comptage direct du nombre d'éléments
    #nbd = list_veoservices.count()
    #return nbd

def nbrDAT():

    
    five_days_ago_start_of_day = datetime.datetime.now() - datetime.timedelta(days=6)

    all_veoservices = Veoservices.objects.filter(
        Date_création__isnull=False,
        statutdoute="Non traité",
        date_creation_nv__gte=five_days_ago_start_of_day
    ).exclude(
        Q(Statut="Changement de procédure") | Q(Expert="Expert Test") | Q(RateFraude__isnull=True) | Q(RateFraude=0.0) | Q(RateFraude=5.0) | Q(RateFraude=10.0)
    )

    
    additional_list = Veoservices.objects.filter(
        statutdoute="Attente photos Avant",
        date_creation_nv__gte=five_days_ago_start_of_day,
        Photos_Avant__isnull=False
    ).exclude(
        Q(Photos_Avant="") | Q(Expert="Expert Test") | Q(Statut="Changement de procédure") | Q(RateFraude__isnull=True) | Q(RateFraude=0.0) | Q(RateFraude=10.0)
    )

    # Fusionner les résultats et trier
    list_Veo_recente = list(all_veoservices) + list(additional_list)

 
    count = len(list_Veo_recente)

    return count

def nbrDT():
    list_Veoservices=Veoservices.objects.all()
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    NBD=0
    for i in list_Veoservices:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=5 and (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté")   and i.Statut!="Dossier sans suite" and i.Statut!="Changement de procédure") :
                NBD=NBD+1
    return NBD

#def DosAff():
    #Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    #Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    #fifty_days_ago = datetime.datetime.today() - datetime.timedelta(days=50)
    
    # Filtrer les Veoservices créés dans les 50 derniers jours, sans "Changement de procédure"
    #list_Veo_recente = Veoservices.objects.annotate(
        #safe_rate_fraude=Case(
            #When(RateFraude__regex=r'^\d*\.?\d+$', then='RateFraude'),
            #default=Value(None),
            #output_field=FloatField()
        #)
    #).filter(
        #Date_création__gte=fifty_days_ago,
        #Date_création__isnull=False
    #).exclude(
        #Statut="Changement de procédure"
    #)

    # Filtrer pour "Attente photos Avant"
    #list_Veo_recente |= Veoservices.objects.annotate(
        #safe_rate_fraude=Case(
            #When(RateFraude__regex=r'^\d*\.?\d+$', then='RateFraude'),
            #default=Value(None),
            #output_field=FloatField()
        #)
    #).filter(
        #Date_création__gte=fifty_days_ago,
        #Date_création__isnull=False,
        #statutdoute="Attente photos Avant",
        #Photos_Avant__isnull=False
    #).exclude(
        #Photos_Avant="",
        #Statut="Changement de procédure"
    #)

    #return list(list_Veo_recente)

def DosAff():
    # Calculer la date d'il y a 50 jours
    fifty_days_ago = now() - timedelta(days=50)

    # Filtrer les enregistrements récents et exclure certains statuts et valeurs non numériques de RateFraude
    list_Veo_recente = Veoservices.objects.filter(
        Date_création__gte=fifty_days_ago,
        Date_création__isnull=False
    ).exclude(
        Statut="Changement de procédure"
    ).annotate(
        safe_rate_fraude=Cast('RateFraude', FloatField())
    ).filter(
        Q(statutdoute="Non traité") |
        (Q(statutdoute="Attente photos Avant") & ~Q(Photos_Avant="") & Q(Photos_Avant__isnull=False))
    ).exclude(
        safe_rate_fraude__in=[0.0, '0.0', None]
    )

    return list(list_Veo_recente)

#def DosAT():
    #Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    #Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    #twenty_five_days_ago = timezone.now() - datetime.timedelta(days=25)

    # Filtrer les Veoservices créés dans les 25 derniers jours, sans "Changement de procédure"
    #list_Veo_recente = Veoservices.objects.annotate(
        #safe_rate_fraude=Case(
            #When(RateFraude__regex=r'^\d*\.?\d+$', then='RateFraude'),
            #default=Value(None),
            #output_field=FloatField()
        #)
    #).filter(
        #Date_création__gte=twenty_five_days_ago,
        #Date_création__isnull=False
    #).exclude(
        #Statut="Changement de procédure"
    #)

    # Ajouter un filtre pour "Attente photos Avant" 
    #list_Veo_recente |= Veoservices.objects.annotate(
        #safe_rate_fraude=Case(
            #When(RateFraude__regex=r'^\d*\.?\d+$', then='RateFraude'),
            #default=Value(None),
            #output_field=FloatField()
        #)
    #).filter(
        #Date_création__gte=twenty_five_days_ago,
        #Date_création__isnull=False,
        #statutdoute="Attente photos Avant",
        #Photos_Avant__isnull=False
    #).exclude(
        #Photos_Avant="",
        #Statut="Changement de procédure"
    #)

    #return list(list_Veo_recente)
def safe_convert_to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None  


def DosAT():
    twenty_five_days_ago = now() - timedelta(days=5)
    list_Veo_recente = Veoservices.objects.filter(
        Date_création__gte=twenty_five_days_ago,
        Date_création__isnull=False
    ).exclude(
        Statut="Changement de procédure"
    ).filter(
        Q(statutdoute="Non traité") |
        (Q(statutdoute="Attente photos Avant") & ~Q(Photos_Avant="") & Q(Photos_Avant__isnull=False))
    ).annotate(
        numeric_rate_fraude=Cast('RateFraude', output_field=FloatField(default=None, null=True))
    ).exclude(
        numeric_rate_fraude__in=[0, 0.0, None]  
    )

    
    results = list(list_Veo_recente)
    results = [item for item in results if safe_convert_to_float(item.RateFraude) not in [0, 0.0, 5.0, 10.0, None]]
    
    return results

def DosAffdout():
    # Filtrer les objets où le statutdoute est "Doute confirmé"
    list_Veo_recente = Veoservices.objects.filter(statutdoute="Doute confirmé")

    return list(list_Veo_recente)

def filtre(request):
    id=request.GET.get('filtre')
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    if (id=="Date_creation"):
        list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    elif (id=="Date_sinistre"):
        list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    else:
        for i in list_Veo_recente:
            i.RateFraude=str_to_float(i.RateFraude)
        list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
   # paginator = Paginator(list_Veo_recente,9)
   # page = request.GET.get('page')
   # veopg = paginator.get_page(page)
    #veopg.sort(key=lambda r: r.RateFraude,reverse=True)
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": list_Veo_recente}
    return render(request,"home.html",context)
    
    # Vérifier  si  l'utilisateur  connecter  est  un  admin
def SupUse(request):
    if request.user.is_superuser:
        SupUse = True
    else:
        SupUse = False
    return SupUse

def TrDos(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=1
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg ,"tri":tri}
    return render(request,"home.html",context)

def TrImmat(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=2
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrDsin(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=3
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrDcr(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=4
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrType(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=5
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrStat(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=6
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrExp(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=7
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrIAdv(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=8
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)


def TrRF(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=9
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrStatDoute(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=10
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def Trobs(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=11
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg , "tri":tri}
    return render(request,"home.html",context)


def TrDosI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=12
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg, "tri":tri}
    return render(request,"home.html",context)

def TrImmatI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=13
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrDsinI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrDcrI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrTypeI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=16
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrStatI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=17
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrExpI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=18
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)

def TrIAdvI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=19
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)
def TrRFI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=20
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)
def TrStatDouteI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=21
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)
def TrobsI(request):
    list_Veo_recente=DosAff()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=22
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)



def TrDosAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=1
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg ,"tri":tri}
    return render(request,"dossieratrait.html",context)

def TrImmatAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=2
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrDsinAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=3
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrDcrAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=4
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)

def TrTypeAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=5
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrStatAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=6
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrExpAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=7
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)

def TrIAdvAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=8
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrRFAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=9
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrStatDouteAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=10
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrobsAT(request):

    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=11
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg , "tri":tri}
    return render(request,"dossieratrait.html",context)


def TrDosIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=12
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)

def TrImmatIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=13
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrDsinIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)

def TrDcrIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrTypeIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=16
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrStatIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=17
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrExpIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=18
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)

def TrIAdvIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=19
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrRFIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=20
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home.html",context)
def TrStatDouteIAT(request):
    
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=21
    context={"SupUse":SupUse(request),"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait.html",context)
def TrobsIAT(request):
    list_Veo_recente=DosAT()
    nbr=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=22
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri,"NBDT":NBDT}
    return render(request,"dossieratrait.html",context)


def TrDosT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=1
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrImmatT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=2
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrDsinT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=3
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrDcrT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=4
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrTypeT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=5
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrStatT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=6
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
     
def TrExpT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=7
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrIAdvT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=8
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrRFT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=9
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrStatDouteT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=10
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrobsT(request):

    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=11
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)


def TrDosIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=12
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrImmatIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=13
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrDsinIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrDcrIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrDsinIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrDcrIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrTypeIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=16
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrStatIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=17
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrExpIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=18
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrIAdvIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=19
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrRFIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
        
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=20
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrStatDouteIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=21
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrobsIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=22
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)

def TrdateIT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r:  r.date_obs,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=24
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
def TrdateT(request):
    list_Veo_recente=DosTAff()
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r:  r.date_obs,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=23
    Veoservice=Veoservices.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait.html",context)
@login_required
def filterDos(request):
    today = datetime.datetime.now()  
    if is_aware(today):
        today = make_naive(today, get_current_timezone())

    NBD = nbrDAT()
    NBDT = nbrDT()
    query = request.GET.get('search', '')

    liste1 = Veoservices.objects.filter(Dossier__icontains=query)
    liste2 = Veoservices.objects.filter(Immatriculation__icontains=query)
    liste = liste1 | liste2

    list_Veo_recente = [
        i for i in liste if i.Date_création and
        (today - datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')).days <= 5 and
        i.RateFraude not in [0, '0.0', None, '5.0', '10.0', '15.0']
    ]

    for item in list_Veo_recente:
        item.RateFraude = str_to_float(item.RateFraude)

    list_Veo_recente.sort(key=lambda r: r.RateFraude if r.RateFraude is not None else 0, reverse=True)
    paginator = Paginator(list_Veo_recente, 9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {
        "SupUse": SupUse(request),
        "list_Veo_recente": veopg,
        "NBDossiers": NBD,
        "NBDT": NBDT
    }
    return render(request, "home.html", context)
@login_required
def filterDosAT(request):
    Today_DateVeo = datetime.datetime.today()
    NBD = nbrDAT()
    NBDT = nbrDT()

    query = request.GET.get('search', '')
    if query:
      
        liste = Veoservices.objects.filter(
            Q(Dossier__icontains=query) | 
            Q(Immatriculation__icontains=query)
        )
        liste = [i for i in liste if i.Date_création and (Today_DateVeo - datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')).days <= 5 and i.statutdoute in ["Non traité", "Attente photos Avant"] and i.Statut != "Changement de procédure" and i.RateFraude not in [0, '0.0', None, '5.0', '10.0']]
    else:
        liste = []

    for item in liste:
        item.RateFraude = str_to_float(item.RateFraude)

    liste.sort(key=lambda r: r.RateFraude, reverse=True)
    paginator = Paginator(liste, 9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {
        "SupUse": SupUse(request),
        "list_Veo_recente": veopg,
        "NBDossiers": NBD,
        "NBDT": NBDT
    }
    return render(request, "dossieratrait.html", context)
@login_required
def filterDosT(request):
    today = datetime.datetime.now()  
    query = request.GET.get('search', '')
    NBD = nbrDAT()  
    NBDT = nbrDT()  

    dossiers = Veoservices.objects.filter(
        Q(Dossier__icontains=query) | Q(Immatriculation__icontains=query),
        Date_création__isnull=False
    )

    list_Veo_recente = [
        i for i in dossiers
        if i.Date_création and datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M') <= today - timedelta(days=5) and
           i.statutdoute in ["Doute confirmé", "Doute rejeté"] and
           i.Statut not in ["Changement de procédure", "Dossier sans suite"] and
           i.RateFraude not in [0, '0.0', None, '5.0', '10.0']
    ]

    list_Veo_recente.sort(key=lambda r: float(r.RateFraude) if r.RateFraude else 0, reverse=True)
    paginator = Paginator(list_Veo_recente, 9)
    veopg = paginator.get_page(request.GET.get('page'))

    list_Veo_Doute = dossiers.filter(statutdoute="Doute confirmé").order_by('-RateFraude')
    paginatorD = Paginator(list_Veo_Doute, 9)
    veoD = paginatorD.get_page(request.GET.get('pageD'))

    context = {
        "SupUse": SupUse(request), 
        "list_Veo_recente": veopg,
        "list_Veo_Doute": veoD,
        "NBDossiers": NBD,
        "NBDT": NBDT
    }
    return render(request, "dossiertrait.html", context)

@login_required
def dossierstrait(request):
    NBD = nbrDAT()
    NBDT = nbrDT()
    total_a_traiter = nbrDAT()
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    ten_days_ago_start_of_day = datetime.datetime.now() - datetime.timedelta(days=380)

    list_Veo_recente = Veoservices.objects.filter(
        date_creation_nv__gte=ten_days_ago_start_of_day
    ).filter(
        Q(statutdoute__in=["Doute confirmé", "Doute rejeté"]) &
        ~Q(Statut__in=["Changement de procédure", "Dossier sans suite"])
    )
    

    
    list_Veo_recente = [veo for veo in list_Veo_recente if veo.RateFraude not in [None, '']]
    list_Veo_recente.sort(key=lambda x: float(x.RateFraude), reverse=True)

    paginator = Paginator(list_Veo_recente, 7)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    

    
    list_Veo_Doute = Veoservices.objects.filter(
        statutdoute="Doute confirmé"
    ).filter(
        date_creation_nv__gte=ten_days_ago_start_of_day
    )

    list_Veo_Doute = [veo for veo in list_Veo_Doute if veo.RateFraude not in [None, '']]
    list_Veo_Doute.sort(key=lambda x: float(x.RateFraude), reverse=True)
    paginator = Paginator(list_Veo_recente, 7)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {
        "SupUse": SupUse(request),  
        "total_a_traiter": total_a_traiter,
        "list_Veo_recente": veopg,
        "list_Veo_Doute": list_Veo_Doute,
        "NBDossiers": NBD,
        'user_name': user_name,
        "NBDT": NBDT
    }

    return render(request, "dossiertrait.html", context)

@login_required
def dossiersAtrait(request):
    NBD = nbrDAT()
    NBDT = nbrDT()
    user_name = f"{request.user.first_name} {request.user.last_name}".strip()
    total_a_traiter = nbrDAT()
    ten_days_ago_start_of_day = datetime.datetime.now() - datetime.timedelta(days=6)
    list_inst = Veoservices.objects.filter(Statut="Dossier en instruction", Dossier__contains="D",
        date_creation_nv__gte=ten_days_ago_start_of_day)

    
    ten_days_ago_start_of_day = datetime.datetime.now() - datetime.timedelta(days=6)

    all_veoservices = Veoservices.objects.filter(
        Date_création__isnull=False,
        statutdoute="Non traité",
        date_creation_nv__gte=ten_days_ago_start_of_day
    ).exclude(
        Q(Statut="Changement de procédure") | Q(Expert="Expert Test") | Q(RateFraude__isnull=True) | Q(RateFraude=0.0) | Q(RateFraude=5.0) | Q(RateFraude=10.0)
    )

    
    additional_list = Veoservices.objects.filter(
        statutdoute="Attente photos Avant",
        date_creation_nv__gte=ten_days_ago_start_of_day,
        Photos_Avant__isnull=False
    ).exclude(
        Q(Photos_Avant="") | Q(Statut="Changement de procédure") | Q(Expert="Expert Test") | Q(RateFraude__isnull=True) | Q(RateFraude=0.0)| Q(RateFraude=10.0)
    )

    
    list_Veo_recente = sorted(
        list(all_veoservices) + list(additional_list), 
        key=lambda r: r.RateFraude or 0,  
        reverse=True
    )

    # Pagination des résultats
    paginator = Paginator(list_Veo_recente, 9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {
        "SupUse": SupUse(request),
        "total_a_traiter": total_a_traiter,
        "list_Veo_recente": veopg,
        "list_inst": list_inst,
        "NBDossiers": NBD,
        'user_name': user_name,
        "NBDT": NBDT
    }

    return render(request, "dossieratrait.html", context)

def DosTAff():
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    list_Veo_recente=[]
    list_Veoservices=Veoservices.objects.all()

    for i in list_Veoservices:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=8) and (i.Statut!= "Changement procédure") and  (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté"):
                list_Veo_recente.append(i)
    return  list_Veo_recente
def observation(request):
    obs=request.GET.get('statutdoute')
    query=request.GET.get('observation')
    utilisateur=request.user.first_name +" "+ request.user.last_name
    email_traitement=request.user.username.title
    dos=request.GET.get('dos')
    dateM = datetime.datetime.now()
    Veoservices.objects.filter(id=dos).update(utilisateur=utilisateur)
    Veoservices.objects.filter(id=dos).update(email_traitement=email_traitement)
    Veoservices.objects.filter(id=dos).update(date_obs=dateM)
    NBD=nbrDAT()
    NBDT=nbrDT()
    ls=[]
    if (obs=="confirme"):
        Veoservices.objects.filter(id=dos).update(statutdoute="Doute confirmé")
    elif (obs=="rejete"):
        Veoservices.objects.filter(id=dos).update(statutdoute="Doute rejeté")
    elif (obs=="Attente"):
        Veoservices.objects.filter(id=dos).update(statutdoute="Attente photos Avant")
    elif (obs=="Pas sur"):
        Veoservices.objects.filter(id=dos).update(statutdoute="Pas sur")
    else:
        Veoservices.objects.filter(id=dos).update(statutdoute="Non traité")
    if query not in [None,""]:
        Veoservices.objects.filter(id=dos).update(observation=query)
        #dateM=datetime.datetime.now()
        #ls=str(dateM).split('.')
       #dateM = ls[1]
        Veoservices.objects.filter(id=dos).update(date_obs=dateM)
    Veo=get_object_or_404(Veoservices,id=dos)
    Rate=Veo.RateFraude
    R1=round((Veo.Reg1()[0]*3/15),2)
    R1_P=Veo.Reg1()[1]
    R1_A=Veo.Reg1()[2]

    R2=round((Veo.Reg2()[0]*2)/15,2)
    R2_DDA=Veo.Reg2()[1]
    R2_DS=Veo.Reg2()[2]

    R3=round((Veo.Reg3()[0]*2)/15,2)
    R3_DDA=Veo.Reg3()[1]
    R3_DS=Veo.Reg3()[2]

    R4=round((Veo.Reg4()[0]*3)/15,2)
    R4_SP=Veo.Reg4()[1]
    R4_SA=Veo.Reg4()[2]

    R5=round((Veo.Reg5()[0]*2)/15,2)
    R5_Assis=Veo.Reg5()[1]

    R6=round((Veo.Reg6()[0]*2)/15,2)
    R6_Assis1=Veo.Reg6()[1]
    R6_Assis2=Veo.Reg6()[2]

    R7=Veo.Reg7()[0]
    R7_P=Veo.Reg7()[1]
    R7_A=Veo.Reg7()[2]

    R9=Veo.Reg9()[0]
    R9_DFP=Veo.Reg9()[1]
    R9_DS=Veo.Reg9()[2]


    R8=Veo.Reg8()

    R10=Veo.Reg10()[0]
    R10_Dos=Veo.Reg10()[1]
    
    R12=Veo.Reg12()[0]
    R12_Dos=Veo.Reg12()[1]

    R11=Veo.Reg11()

    R13=Veo.Reg13()[0]
    R13_Dos=Veo.Reg13()[1]

    R14=Veo.Reg14()


    #R15=Veo.Reg15()[0]
    #R15_CN=Veo.Reg15()[1]

    #R16=Veo.Reg16()[0]
    #R16_Dos=Veo.Reg16()[1]

    #R17=Veo.Reg17()[0]
    #R17_Int=Veo.Reg17()[1]

    context={"SupUse":SupUse(request),"NBDT":NBDT,"Veo":Veo,"Rate":Rate ,"R1": R1,"R1_P": R1_P, "R1_A":R1_A, "R2":R2, "R2_DDA":R2_DDA, "R2_DS":R2_DS,"R3":R3, "R3_DDA":R3_DDA, "R3_DS":R3_DS, "R4":R4, "R4_SP":R4_SP, "R4_SA":R4_SA,"R5":R5 ,"R5_Assis":R5_Assis ,"R6":R6,"R6_Assis1":R6_Assis1 ,"R6_Assis2":R6_Assis2,"R7":R7,"R7_P":R7_P,"R7_A":R7_A, "R9_DFP":R9_DFP, "R9_DS":R9_DS, "R9":R9,"R8":R8,"NBDossiers":NBD,"R11":R11, "R10_Dos":R10_Dos,"R10":R10 , "R12_Dos":R12_Dos,"R12":R12 , "R14":R14, "R13_Dos":R13_Dos,"R13":R13 }
    return render(request,"detail.html",context)


    
def filtre_reg(request):
    ch=request.GET.get('reg')
    
    liste=[]
    listedossiers =DosAff()
    if (ch=="R1"):
        for i in listedossiers:
            if i.R1 != None and i.R1 != "":
                liste.append(i)
    elif (ch =="R2"):
        for i in listedossiers:
            if i.R2 != None and i.R2 != "":
                liste.append(i)
    elif (ch =="R3"):
        for i in listedossiers:
            if i.R3 != None and i.R3 != "":
                liste.append(i)
        
    elif (ch =="R4"):
        for i in listedossiers:
            if i.R4 != None and i.R4 != "":
                liste.append(i)
    elif (ch =="R5"):
        for i in listedossiers:
            if i.R5 != None and i.R5 != "":
                liste.append(i)
    elif (ch =="R6"):
        for i in listedossiers:
            if i.R6 != None and i.R6 != "":
                liste.append(i)
    elif (ch =="R7"):
        for i in listedossiers:
            if i.R7 != None and i.R7 != "":
                liste.append(i)
    elif (ch =="R8"):
        for i in listedossiers:
            if i.R8 != None and i.R8 != "":
                liste.append(i)
    elif (ch =="R9"):
        for i in listedossiers:
            if i.R9 != None and i.R9 != "":
                liste.append(i)
    elif (ch =="R10"):
        for i in listedossiers:
            if i.R10 != None and i.R10 != "":
                liste.append(i)
    elif (ch =="R11"):
        for i in listedossiers:
            if i.R11 != None and i.R11 != "":
                liste.append(i)
    elif (ch =="R12"):
        for i in listedossiers:
            if i.R12 != None and i.R12 != "":
                liste.append(i)
    
    elif (ch =="R13_confirme"):
        for i in listedossiers:
            if i.R13 != None and "doute confirmé" in i.R13 :
                liste.append(i)

    elif (ch =="R13_rejete"):
        for i in listedossiers:
            if i.R13 != None and "doute rejeté" in i.R13 :
                liste.append(i)

                
    elif (ch =="R14"):
        for i in listedossiers:
            if i.R14 != None and i.R14 != "":
                liste.append(i)
    elif (ch =="R15"):
        for i in listedossiers:
            if i.R15 != None and i.R15 != "":
                liste.append(i)
    elif (ch =="R16"):
        for i in listedossiers:
            if i.R16 != None and i.R16 != "":
                liste.append(i)
    elif (ch =="R17"):
        for i in listedossiers:
            if i.R17 != None and i.R17 != "":
                liste.append(i)
    
    
    paginator = Paginator(liste,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    NBDAT=nbrDAT()    
    context={"SupUse":SupUse(request),"NBDossiers":NBDAT,"list_Veo_recente": veopg }
    return render(request,"home.html",context)





    
def filtre_regAT(request):
    ch=request.GET.get('reg')
    
    liste=[]
    listedossiers =DosAT()
    if (ch=="R1"):
        for i in listedossiers:
            if i.R1 != None and i.R1 != "":
                liste.append(i)
    elif (ch =="R2"):
        for i in listedossiers:
            if i.R2 != None and i.R2 != "":
                liste.append(i)
    elif (ch =="R3"):
        for i in listedossiers:
            if i.R3 != None and i.R3 != "":
                liste.append(i)
        
    elif (ch =="R4"):
        for i in listedossiers:
            if i.R4 != None and i.R4 != "":
                liste.append(i)
    elif (ch =="R5"):
        for i in listedossiers:
            if i.R5 != None and i.R5 != "":
                liste.append(i)
    elif (ch =="R6"):
        for i in listedossiers:
            if i.R6 != None and i.R6 != "":
                liste.append(i)
    elif (ch =="R7"):
        for i in listedossiers:
            if i.R7 != None and i.R7 != "":
                liste.append(i)
    elif (ch =="R8"):
        for i in listedossiers:
            if i.R8 != None and i.R8 != "":
                liste.append(i)
    elif (ch =="R9"):
        for i in listedossiers:
            if i.R9 != None and i.R9 != "":
                liste.append(i)
    elif (ch =="R10"):
        for i in listedossiers:
            if i.R10 != None and i.R10 != "":
                liste.append(i)
    elif (ch =="R11"):
        for i in listedossiers:
            if i.R11 != None and i.R11 != "":
                liste.append(i)
    elif (ch =="R12"):
        for i in listedossiers:
            if i.R12 != None and i.R12 != "":
                liste.append(i)
  
    elif (ch =="R13_confirme"):
        for i in listedossiers:
            if i.R13 != None and "doute confirmé" in i.R13 :
                liste.append(i)

    elif (ch =="R13_rejete"):
        for i in listedossiers:
            if i.R13 != None and "doute rejeté" in i.R13 :
                liste.append(i)

                
    elif (ch =="R14"):
        for i in listedossiers:
            if i.R14 != None and i.R14 != "":
                liste.append(i)
    elif (ch =="R15"):
        for i in listedossiers:
            if i.Reg15 != None and i.Reg15 != "":
                liste.append(i)
    elif (ch =="R16"):
        for i in listedossiers:
            if i.Reg16 != None and i.Reg16 != "":
                liste.append(i)
    elif (ch =="R17"):
        for i in listedossiers:
            if i.Reg17 != None and i.Reg17 != "":
                liste.append(i)

    paginator = Paginator(liste,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    NBD=nbrDAT()    
    
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBD}
    
    return render(request,"dossieratrait.html",context)


    
def filtre_regT(request):
    ch=request.GET.get('reg')
    
    liste=[]
    listedossiers =DosTAff()
    if (ch=="R1"):
        for i in listedossiers:
            if i.R1 != None and i.R1 != "":
                liste.append(i)
    elif (ch =="R2"):
        for i in listedossiers:
            if i.R2 != None and i.R2 != "":
                liste.append(i)
    elif (ch =="R3"):
        for i in listedossiers:
            if i.R3 != None and i.R3 != "":
                liste.append(i)
        
    elif (ch =="R4"):
        for i in listedossiers:
            if i.R4 != None and i.R4 != "":
                liste.append(i)
    elif (ch =="R5"):
        for i in listedossiers:
            if i.R5 != None and i.R5 != "":
                liste.append(i)
    elif (ch =="R6"):
        for i in listedossiers:
            if i.R6 != None and i.R6 != "":
                liste.append(i)
    elif (ch =="R7"):
        for i in listedossiers:
            if i.R7 != None and i.R7 != "":
                liste.append(i)
    elif (ch =="R8"):
        for i in listedossiers:
            if i.R8 != None and i.R8 != "":
                liste.append(i)
    elif (ch =="R9"):
        for i in listedossiers:
            if i.R9 != None and i.R9 != "":
                liste.append(i)
    elif (ch =="R10"):
        for i in listedossiers:
            if i.R10 != None and i.R10 != "":
                liste.append(i)
    elif (ch =="R11"):
        for i in listedossiers:
            if i.R11 != None and i.R11 != "":
                liste.append(i)
    elif (ch =="R12"):
        for i in listedossiers:
            if i.R12 != None and i.R12 != "":
                liste.append(i)
  
    elif (ch =="R13_confirme"):
        for i in listedossiers:
            if i.R13 != None and "doute confirmé" in i.R13 :
                liste.append(i)

    elif (ch =="R13_rejete"):
        for i in listedossiers:
            if i.R13 != None and "doute rejeté" in i.R13 :
                liste.append(i)

                
    elif (ch =="R14"):
        for i in listedossiers:
            if i.R14 != None and i.R14 != "":
                liste.append(i)
    elif (ch =="R15"):
        for i in listedossiers:
            if i.Reg15 != None and i.Reg15 != "":
                liste.append(i)
    elif (ch =="R16"):
        for i in listedossiers:
            if i.Reg16 != None and i.Reg16 != "":
                liste.append(i)
    elif (ch =="R17"):
        for i in listedossiers:
            if i.Reg17 != None and i.Reg17 != "":
                liste.append(i)
    paginator = Paginator(liste,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    NBDAT=nbrDAT()    
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": DosAffdout(),"NBDossiers":NBDAT}
    
    return render(request,"dossiertrait.html",context)


##################################################################################################################
##################################################################################################################
##################################################################################################################
#################################################################################################################


####################################################################################################################*
#################################################################################################################*#*
#####################################################################################################################*
####################################################################################################################"
# *
# 
# 
# 
# 
# 
# 
# 
# 
# 

def test_nbrDAT():
    NBD=0
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    list_veotest=veotest.objects.all()
    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            if (((Today_DateVeo-Date_création).days<=5) and i.statutdoute=="Non traité" and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) :
                NBD=NBD+1
    return NBD

def test_nbrDT():
    list_veotest=veotest.objects.all()
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    NBD=0
    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=10 and (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté")   and i.Statut!="Dossier sans suite" and i.Statut!="Changement de procédure") :
                NBD=NBD+1
    return NBD


@login_required
def test_inis(request):
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    NBDAT=test_nbrDAT()
    list_Veo_recente=[]
    NBD=0
    list_veotest=veotest.objects.all()
    Rate=0
    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            i.RateFraude = str_to_float(i.RateFraude)
        if (i.Statut!= "Changement procédure") and (i.RateFraude not in [0,0.0,None]):
            
            list_Veo_recente.append(i)
            
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBDAT}
    return render(request,"home_test.html",context)

@login_required
def test_details(request, Dossier):
    Veo=get_object_or_404(veotest,id=Dossier)
    Rate=Veo.RateFraude
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    R1=Veo.Reg1()[0]
    R1_P=Veo.Reg1()[1]
    R1_A=Veo.Reg1()[2]

    R2=Veo.Reg2()[0]
    R2_DDA=Veo.Reg2()[1]
    R2_DS=Veo.Reg2()[2]

    R3=Veo.Reg3()[0]
    R3_DDA=Veo.Reg3()[1]
    R3_DS=Veo.Reg3()[2]

    R4=Veo.Reg4()[0]
    R4_SP=Veo.Reg4()[1]
    R4_SA=Veo.Reg4()[2]

    R5=Veo.Reg5()[0]
    #Dossier assistance qui à la  date moins  de 7h et plus de 20h
    R5_Assis=Veo.Reg5()[1]

    R6=Veo.Reg6()[0]
    #Les  deux dossiers Assistance qui ne dépassent pas 3 mois
    R6_Assis1=Veo.Reg6()[1]
    R6_Assis2=Veo.Reg6()[2]

    R7=Veo.Reg7()[0]
    R7_P=Veo.Reg7()[1]
    R7_A=Veo.Reg7()[2]

    R9=Veo.Reg9()[0]
    R9_DFP=Veo.Reg9()[1]
    R9_DS=Veo.Reg9()[2]

    R8=Veo.Reg8()

    R10=Veo.Reg10()[0]
    R10_Dos=Veo.Reg10()[1]
    
    R12=Veo.Reg12()[0]
    R12_Dos=Veo.Reg12()[1]

    R11=Veo.Reg11()

    R13=Veo.Reg13()[0]
    R13_Dos=Veo.Reg13()[1]

    R14=Veo.Reg14()
    # Vérifier si c'est superuser
    if request.user.is_superuser:
        SupUse = True
    else:
        SupUse = False
    context={"SupUse":SupUse, "NBDT":NBDT,"NBDossiers":NBD,"Veo":Veo,"Rate":Rate ,"R1": R1,"R1_P": R1_P, "R1_A":R1_A, "R2":R2, "R2_DDA":R2_DDA, "R2_DS":R2_DS,"R3":R3, "R3_DDA":R3_DDA, "R3_DS":R3_DS, "R4":R4, "R4_SP":R4_SP, "R4_SA":R4_SA,"R5":R5 ,"R5_Assis":R5_Assis ,"R6":R6,"R6_Assis1":R6_Assis1 ,"R6_Assis2":R6_Assis2,"R7":R7,"R7_P":R7_P,"R7_A":R7_A, "R9_DFP":R9_DFP, "R9_DS":R9_DS, "R9":R9,"R8":R8,"R11":R11, "R10_Dos":R10_Dos,"R10":R10 , "R12_Dos":R12_Dos,"R12":R12 ,"R14":R14, "R13_Dos":R13_Dos,"R13":R13 }

    return render(request,"detail_test.html",context)
def test_test_nbrDAT():
    NBD=0
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    list_veotest=veotest.objects.all()
    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            if (((Today_DateVeo-Date_création).days<=5) and i.statutdoute=="Non traité" and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) :
                NBD=NBD+1
    return NBD

def test_nbrDT():
    list_veotest=veotest.objects.all()
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    NBD=0
    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=10 and (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté")   and i.Statut!="Dossier sans suite" and i.Statut!="Changement de procédure") :
                NBD=NBD+1
    return NBD

def test_DosAff():
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    list_Veo_recente=[]
    list_veotest=veotest.objects.all()

    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
            if ((((Today_DateVeo-Date_création).days<=5) and (i.Statut!= "Changement procédure")) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" ) )and i.RateFraude not in [0,"0.0","","'0.0'",0.0,None]:
                list_Veo_recente.append(i)
    return  list_Veo_recente

def test_DosAT():
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    list_Veo_recente=[]
    list_veotest=veotest.objects.all()

    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
            if ((((Today_DateVeo-Date_création).days<=5) and (i.Statut!= "Changement procédure")) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" ) )and i.RateFraude not in [0,"0.0","","'0.0'",0.0,0,'0.0',None,'5.0','10.0']:
                list_Veo_recente.append(i)
    return  list_Veo_recente

def test_DosAffdout():
    list_Veo_recente =[]
    list_veotest = veotest.objects.all()
    NBD=test_nbrDAT()
    for i in list_veotest:
        if i.statutdoute == "Doute confirmé":
            list_Veo_recente.append(i)
    return  list_Veo_recente
def test_filtre(request):
    id=request.GET.get('filtre')
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    if (id=="Date_creation"):
        list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    elif (id=="Date_sinistre"):
        list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    else:
        for i in list_Veo_recente:
            i.RateFraude=str_to_float(i.RateFraude)
        list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
   # paginator = Paginator(list_Veo_recente,9)
   # page = request.GET.get('page')
   # veopg = paginator.get_page(page)
    #veopg.sort(key=lambda r: r.RateFraude,reverse=True)
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": list_Veo_recente}
    return render(request,"home_test.html",context)
    # Vérifier  si  l'utilisateur  connecter  est  un  admin
def test_SupUse(request):
    if request.user.is_superuser:
        SupUse = True
    else:
        SupUse = False
    return SupUse

def test_TrDos(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=1
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg ,"tri":tri}
    return render(request,"home_test.html",context)

def test_TrImmat(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=2
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrDsin(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=3
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrDcr(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=4
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrType(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=5
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrStat(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=6
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrExp(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=7
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrIAdv(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=8
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrRF(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=9
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrStatDoute(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=10
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_Trobs(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=11
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg , "tri":tri}
    return render(request,"home_test.html",context)


def test_TrDosI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=12
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrImmatI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=13
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrDsinI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrDcrI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrTypeI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=16
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrStatI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=17
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrExpI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=18
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)

def test_TrIAdvI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=19
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)
def test_TrRFI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=20
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)
def test_TrStatDouteI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=21
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)
def test_TrobsI(request):
    list_Veo_recente=test_DosAff()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=22
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)



def test_TrDosAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=1
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg ,"tri":tri}
    return render(request,"dossieratrait_test.html",context)

def test_TrImmatAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=2
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrDsinAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=3
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrDcrAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=4
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)

def test_TrTypeAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=5
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrStatAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=6
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrExpAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=7
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)

def test_TrIAdvAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=8
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrRFAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=9
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrStatDouteAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=10
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrobsAT(request):

    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=11
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg , "tri":tri}
    return render(request,"dossieratrait_test.html",context)


def test_TrDosIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=12
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente":veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)

def test_TrImmatIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=13
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrDsinIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)

def test_TrDcrIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrTypeIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=16
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrStatIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=17
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrExpIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=18
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)

def test_TrIAdvIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=19
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrRFIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=20
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"home_test.html",context)
def test_TrStatDouteIAT(request):
    
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=21
    context={"SupUse":SupUse(request),"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri}
    return render(request,"dossieratrait_test.html",context)
def test_TrobsIAT(request):
    list_Veo_recente=test_DosAT()
    nbr=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=22
    context={"SupUse":SupUse(request),"NBDT":NBDT,"NBDossiers":nbr,"list_Veo_recente": veopg, "tri":tri,"NBDT":NBDT}
    return render(request,"dossieratrait_test.html",context)


def test_TrDosT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=1
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrImmatT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=2
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrDsinT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=3
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrDcrT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=4
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrTypeT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=5
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrStatT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=6
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrExpT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=7
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrIAdvT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=8
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrRFT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=9
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrStatDouteT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=10
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrobsT(request):

    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=11
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)


def test_TrDosIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.id,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=12
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrImmatIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Immatriculation,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=13
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrDsinIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrDcrIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrDsinIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_sinistre,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=14
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrDcrIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Date_création,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=15
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrTypeIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Procédure,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=16
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrStatIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Statut,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=17
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrExpIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.Expert,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=18
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrIAdvIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.ImmatriculationAdverse,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=19
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrRFIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    for i in list_Veo_recente:
        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
        
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=20
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrStatDouteIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.statutdoute,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=21
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrobsIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r: r.observation,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=22
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)

def test_TrdateIT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r:  r.date_obs,reverse=False)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=24
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
def test_TrdateT(request):
    list_Veo_recente=test_DosTAff()
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente.sort(key=lambda r:  r.date_obs,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    tri=23
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT, "tri":tri}
    return render(request,"dossiertrait_test.html",context)
@login_required
def test_filterDos(request):
    list_Veo_recente=[]
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    if request.method=='GET':
        query=request.GET.get('search')
    liste2=list(veotest.objects.filter(Dossier__icontains=query))
    liste1=list(veotest.objects.filter(Immatriculation__icontains=query))
    if liste1==None:
        liste=liste2
    elif liste2==None:
        liste=liste1
    else:
        liste=liste1+liste2
    for i in liste:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=100) and i.RateFraude not in [0,'0.0',None,'5.0','10.0','15.0'] and i not in list_Veo_recente:
                list_Veo_recente.append(i)
                i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBD,"NBDT":NBDT}
    return render(request,"home_test.html",context)
@login_required
def test_filterDosAT(request):
    list_Veo_recente=[]
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    if request.method=='GET':
        query=request.GET.get('search')
        liste2=list(veotest.objects.filter(Dossier__icontains=query))
        liste1=list(veotest.objects.filter(Immatriculation__icontains=query))
        if liste1==None:
            liste=liste2
        elif liste2==None:
            liste=liste1
        else:
            liste=liste1+liste2
        for i in liste:
            if i.Date_création!=None:
                Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
                if ((Today_DateVeo-Date_création).days<=100):
                    if (i.statutdoute=="Non traité" and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) and i not in list_Veo_recente:
                        list_Veo_recente.append(i)
                        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBD,"NBDT":NBDT}
    return render(request,"dossieratrait_test.html",context)
@login_required
def test_filterDosT(request):
    list_Veo_recente=[]
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    if request.method=='GET':
        query=request.GET.get('search')
        liste2=list(veotest.objects.filter(Dossier__icontains=query))
        liste1=list(veotest.objects.filter(Immatriculation__icontains=query))
        if liste1==None:
            liste=liste2
        elif liste2==None:
            liste=liste1
        else:
            liste=liste1+liste2
        for i in liste:
            if i.Date_création!=None:
                Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
                if ((Today_DateVeo-Date_création).days<=100):
                    if (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté") and i.Statut!="Changement de procédure" and  i.Statut!="Dossier sans suite" and i.RateFraude not in [0,'0.0',None,'5.0','10.0'] and i not in list_Veo_recente:
                        list_Veo_recente.append(i)
                        i.RateFraude=str_to_float(i.RateFraude)
    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    
    Veoservice=veotest.objects.all()
    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT}
    return render(request,"dossiertrait_test.html",context)

@login_required
def test_dossierstrait(request):
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente=[]
    list_veotest=test_DosTAff()
    Veoservice=veotest.objects.all()
    for i in list_veotest:
        if (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté") and i.Statut!="Changement de procédure" and  i.Statut!="Dossier sans suite" :
            i.RateFraude = str_to_float(i.RateFraude)
            list_Veo_recente.append(i)

    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    list_Veo_Doute =[]
    for i in Veoservice:
        if i.statutdoute == "Doute confirmé":
            list_Veo_Doute.append(i)
    list_Veo_Doute.sort(key=lambda r: r.RateFraude,reverse=True)
    paginatorD = Paginator(list_Veo_Doute,9)
    pageD = request.GET.get('pageD')
    veoD = paginator.get_page(pageD)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBD,"NBDT":NBDT}
    return render(request,"dossiertrait_test.html",context)
@login_required
def test_dossiersAtrait(request):
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente=[]
    list_inst=[]
    list_veotest=test_DosAff()
    list_veotestall= veotest.objects.all()
    for i in list_veotestall:
        if i.Statut =="Dossier en instruction" and "D" in i.Dossier:
            list_inst.append(i)
    for i in list_veotest:
        
        if (i.statutdoute=="Non traité" and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) :
            i.RateFraude = str_to_float(i.RateFraude)
            list_Veo_recente.append(i)


    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
   # veopg.sort(key=lambda r: r.RateFraude,reverse=True)
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBD,"NBDT":NBDT ,"list_inst": list_inst}
    return render(request,"dossieratrait_test.html",context) 

def test_DosTAff():
    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo,'%d/%m/%Y %H:%M')
    list_Veo_recente=[]
    list_veotest=veotest.objects.all()

    for i in list_veotest:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création,'%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=8) and (i.Statut!= "Changement procédure") and  (i.statutdoute=="Doute confirmé" or i.statutdoute=="Doute rejeté"):
                list_Veo_recente.append(i)
    return  list_Veo_recente
def test_observation(request):
    obs=request.GET.get('statutdoute')
    query=request.GET.get('observation')
    utilisateur=request.user.first_name +" "+ request.user.last_name
    email_traitement=request.user.username.title
    dos=request.GET.get('dos')
    veotest.objects.filter(id=dos).update(utilisateur=utilisateur)
    veotest.objects.filter(id=dos).update(email_traitement=email_traitement)
    NBD=test_nbrDAT()
    NBDT=nbrDT()
    ls=[]
    if (obs=="confirme"):
        veotest.objects.filter(id=dos).update(statutdoute="Doute confirmé")
    elif (obs=="rejete"):
        veotest.objects.filter(id=dos).update(statutdoute="Doute rejeté")
    elif (obs=="Attente"):
        veotest.objects.filter(id=dos).update(statutdoute="Attente photos Avant")
    elif (obs=="Pas sur"):
        veotest.objects.filter(id=dos).update(statutdoute="Pas sur")
    else:
        veotest.objects.filter(id=dos).update(statutdoute="Non traité")
    if query not in [None,""]:
        veotest.objects.filter(id=dos).update(observation=query)
        dateM=datetime.datetime.now()
        #ls=str(dateM).split('.')
       #dateM = ls[1]
        veotest.objects.filter(id=dos).update(date_obs=dateM)
    Veo=get_object_or_404(veotest,id=dos)
    Rate=Veo.RateFraude
    R1=round((Veo.Reg1()[0]*3/15),2)
    R1_P=Veo.Reg1()[1]
    R1_A=Veo.Reg1()[2]

    R2=round((Veo.Reg2()[0]*2)/15,2)
    R2_DDA=Veo.Reg2()[1]
    R2_DS=Veo.Reg2()[2]

    R3=round((Veo.Reg3()[0]*2)/15,2)
    R3_DDA=Veo.Reg3()[1]
    R3_DS=Veo.Reg3()[2]

    R4=round((Veo.Reg4()[0]*3)/15,2)
    R4_SP=Veo.Reg4()[1]
    R4_SA=Veo.Reg4()[2]

    R5=round((Veo.Reg5()[0]*2)/15,2)
    R5_Assis=Veo.Reg5()[1]

    R6=round((Veo.Reg6()[0]*2)/15,2)
    R6_Assis1=Veo.Reg6()[1]
    R6_Assis2=Veo.Reg6()[2]

    R7=Veo.Reg7()[0]
    R7_P=Veo.Reg7()[1]
    R7_A=Veo.Reg7()[2]

    R9=Veo.Reg9()[0]
    R9_DFP=Veo.Reg9()[1]
    R9_DS=Veo.Reg9()[2]


    R8=Veo.Reg8()

    R10=Veo.Reg10()[0]
    R10_Dos=Veo.Reg10()[1]
    
    R12=Veo.Reg12()[0]
    R12_Dos=Veo.Reg12()[1]

    R11=Veo.Reg11()

    R13=Veo.Reg13()[0]
    R13_Dos=Veo.Reg13()[1]

    R14=Veo.Reg14()

    context={"SupUse":SupUse(request),"NBDT":NBDT,"Veo":Veo,"Rate":Rate ,"R1": R1,"R1_P": R1_P, "R1_A":R1_A, "R2":R2, "R2_DDA":R2_DDA, "R2_DS":R2_DS,"R3":R3, "R3_DDA":R3_DDA, "R3_DS":R3_DS, "R4":R4, "R4_SP":R4_SP, "R4_SA":R4_SA,"R5":R5 ,"R5_Assis":R5_Assis ,"R6":R6,"R6_Assis1":R6_Assis1 ,"R6_Assis2":R6_Assis2,"R7":R7,"R7_P":R7_P,"R7_A":R7_A, "R9_DFP":R9_DFP, "R9_DS":R9_DS, "R9":R9,"R8":R8,"NBDossiers":NBD,"R11":R11, "R10_Dos":R10_Dos,"R10":R10 , "R12_Dos":R12_Dos,"R12":R12,"R14":R14, "R13_Dos":R13_Dos,"R13":R13 }
    return render(request,"detail_test.html",context)


def test_filtre_reg(request):
    ch=request.GET.get('reg')
    
    liste=[]
    listedossiers =test_DosAff()
    if (ch=="R1"):
        for i in listedossiers:
            if i.R1 != None and i.R1 != "":
                liste.append(i)
    elif (ch =="R2"):
        for i in listedossiers:
            if i.R2 != None and i.R2 != "":
                liste.append(i)
    elif (ch =="R3"):
        for i in listedossiers:
            if i.R3 != None and i.R3 != "":
                liste.append(i)
        
    elif (ch =="R4"):
        for i in listedossiers:
            if i.R4 != None and i.R4 != "":
                liste.append(i)
    elif (ch =="R5"):
        for i in listedossiers:
            if i.R5 != None and i.R5 != "":
                liste.append(i)
    elif (ch =="R6"):
        for i in listedossiers:
            if i.R6 != None and i.R6 != "":
                liste.append(i)
    elif (ch =="R7"):
        for i in listedossiers:
            if i.R7 != None and i.R7 != "":
                liste.append(i)
    elif (ch =="R8"):
        for i in listedossiers:
            if i.R8 != None and i.R8 != "":
                liste.append(i)
    elif (ch =="R9"):
        for i in listedossiers:
            if i.R9 != None and i.R9 != "":
                liste.append(i)
    elif (ch =="R10"):
        for i in listedossiers:
            if i.R10 != None and i.R10 != "":
                liste.append(i)
    elif (ch =="R11"):
        for i in listedossiers:
            if i.R11 != None and i.R11 != "":
                liste.append(i)
    elif (ch =="R12"):
        for i in listedossiers:
            if i.R12 != None and i.R12 != "":
                liste.append(i)
    
    elif (ch =="R13_confirme"):
        for i in listedossiers:
            if i.R13 != None and "doute confirmé" in i.R13 :
                liste.append(i)

    elif (ch =="R13_rejete"):
        for i in listedossiers:
            if i.R13 != None and "doute rejeté" in i.R13 :
                liste.append(i)

                
    elif (ch =="R14"):
        for i in listedossiers:
            if i.R14 != None and i.R14 != "":
                liste.append(i)
    paginator = Paginator(liste,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    NBDAT=test_nbrDAT()    
    context={"SupUse":SupUse(request),"NBDossiers":NBDAT,"list_Veo_recente": veopg }
    return render(request,"home_test.html",context)





    
def test_filtre_regAT(request):
    ch=request.GET.get('reg')
    
    liste=[]
    listedossiers =test_DosAT()
    if (ch=="R1"):
        for i in listedossiers:
            if i.R1 != None and i.R1 != "":
                liste.append(i)
    elif (ch =="R2"):
        for i in listedossiers:
            if i.R2 != None and i.R2 != "":
                liste.append(i)
    elif (ch =="R3"):
        for i in listedossiers:
            if i.R3 != None and i.R3 != "":
                liste.append(i)
        
    elif (ch =="R4"):
        for i in listedossiers:
            if i.R4 != None and i.R4 != "":
                liste.append(i)
    elif (ch =="R5"):
        for i in listedossiers:
            if i.R5 != None and i.R5 != "":
                liste.append(i)
    elif (ch =="R6"):
        for i in listedossiers:
            if i.R6 != None and i.R6 != "":
                liste.append(i)
    elif (ch =="R7"):
        for i in listedossiers:
            if i.R7 != None and i.R7 != "":
                liste.append(i)
    elif (ch =="R8"):
        for i in listedossiers:
            if i.R8 != None and i.R8 != "":
                liste.append(i)
    elif (ch =="R9"):
        for i in listedossiers:
            if i.R9 != None and i.R9 != "":
                liste.append(i)
    elif (ch =="R10"):
        for i in listedossiers:
            if i.R10 != None and i.R10 != "":
                liste.append(i)
    elif (ch =="R11"):
        for i in listedossiers:
            if i.R11 != None and i.R11 != "":
                liste.append(i)
    elif (ch =="R12"):
        for i in listedossiers:
            if i.R12 != None and i.R12 != "":
                liste.append(i)
  
    elif (ch =="R13_confirme"):
        for i in listedossiers:
            if i.R13 != None and "doute confirmé" in i.R13 :
                liste.append(i)
    elif (ch =="R13_rejete"):
        for i in listedossiers:
            if i.R13 != None and "doute rejeté" in i.R13 :
                liste.append(i)
    elif (ch =="R14"):
        for i in listedossiers:
            if i.R14 != None and i.R14 != "":
                liste.append(i)
    paginator = Paginator(liste,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    NBD=test_nbrDAT()        
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBD}
    return render(request,"dossieratrait_test.html",context)
    
def test_filtre_regT(request):
    ch=request.GET.get('reg')    
    liste=[]
    listedossiers =test_DosTAff()
    if (ch=="R1"):
        for i in listedossiers:
            if i.R1 != None and i.R1 != "":
                liste.append(i)
    elif (ch =="R2"):
        for i in listedossiers:
            if i.R2 != None and i.R2 != "":
                liste.append(i)
    elif (ch =="R3"):
        for i in listedossiers:
            if i.R3 != None and i.R3 != "":
                liste.append(i)        
    elif (ch =="R4"):
        for i in listedossiers:
            if i.R4 != None and i.R4 != "":
                liste.append(i)
    elif (ch =="R5"):
        for i in listedossiers:
            if i.R5 != None and i.R5 != "":
                liste.append(i)
    elif (ch =="R6"):
        for i in listedossiers:
            if i.R6 != None and i.R6 != "":
                liste.append(i)
    elif (ch =="R7"):
        for i in listedossiers:
            if i.R7 != None and i.R7 != "":
                liste.append(i)
    elif (ch =="R8"):
        for i in listedossiers:
            if i.R8 != None and i.R8 != "":
                liste.append(i)
    elif (ch =="R9"):
        for i in listedossiers:
            if i.R9 != None and i.R9 != "":
                liste.append(i)
    elif (ch =="R10"):
        for i in listedossiers:
            if i.R10 != None and i.R10 != "":
                liste.append(i)
    elif (ch =="R11"):
        for i in listedossiers:
            if i.R11 != None and i.R11 != "":
                liste.append(i)
    elif (ch =="R12"):
        for i in listedossiers:
            if i.R12 != None and i.R12 != "":
                liste.append(i)  
    elif (ch =="R13_confirme"):
        for i in listedossiers:
            if i.R13 != None and "doute confirmé" in i.R13 :
                liste.append(i)
    elif (ch =="R13_rejete"):
        for i in listedossiers:
            if i.R13 != None and "doute rejeté" in i.R13 :
                liste.append(i)                
    elif (ch =="R14"):
        for i in listedossiers:
            if i.R14 != None and i.R14 != "":
                liste.append(i)
    paginator = Paginator(liste,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
    NBDAT=test_nbrDAT()    
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"list_Veo_Doute": test_DosAffdout(),"NBDossiers":NBDAT}    
    return render(request,"dossiertrait_test.html",context)
################## Affichage du  templates  ##############"##############"

def template(request):
    return render(request,"index.html")



def get_veoservices(request,Dossier):
    veoservice=Veoservices.objects.all()
    veo=None
    if request.method == 'GET':
        
       
        for i in  veoservice:
            if i.Dossier == Dossier:
                veo = i
                response = json.dumps([{'Dossier':Dossier,'Immatriculation':veo.Immatriculation,'Pourcentage Fraude':veo.RateFraude,'Procédure':veo.Procédure,'Statut':veo.Statut,'Date Création':veo.Date_création,'Statut doute':veo.statutdoute}])
                break
            if veo == None:

                response =  json.dumps([{'Error':Dossier}])
    response = json.loads(response)
    return HttpResponse(response, content_type='text/json')

"""def get_dossiers(request):
    veoservice=Veoservices.objects.all()
    ls=[]
    jsls=[]
    N=2
    for i in  veoservice:
        if i.RateFraude not in ["0.0",0.0,None,"0",0,"5.0",5.0,5,"10.0",10.0,10,"15.0",15.0,15]:
            ls.append(i)
    k=ls[0]
          
    l=ls[len(ls)-1]  
    jsls.append('[')  
    jsls.append({'Dossier':k.Dossier,'Pourcentage Fraude':k.RateFraude,'Procédure':k.Procédure,'Statut':k.Statut,'Date Création':k.Date_création,'Statut doute':k.statutdoute}) 
    for j  in  ls:
      
        if  j != k and j != l and N<1001:
            N=N+1
            jsls.append(",")
            js={'Dossier':j.Dossier,'Pourcentage Fraude':j.RateFraude,'Procédure':j.Procédure,'Statut':j.Statut,'Date Création':j.Date_création,'Statut doute':j.statutdoute}
            jsls.append(js)  
    jsls.append(",")  
    jsls.append({'Dossier':l.Dossier,'Pourcentage Fraude':l.RateFraude,'Procédure':l.Procédure,'Statut':l.Statut,'Date Création':l.Date_création,'Statut doute':l.statutdoute}) 
    jsls.append(']')
    #jsls = json.dumps(jsls)
    #jsls = json.loads(jsls)
    #jsl = [line for line in jsls]
    response = jsls
    return HttpResponse(response, content_type='text/json')"""
def  getVeos(request):
    veoservice=Veoservices.objects.all()
    #ls =[]
    
    #for i in  veoservice:
        
        #ls.append(i)
    ls = serialize('json', Veoservices.objects.all())
    response=ls
    
    return HttpResponse(response, content_type='text/json')


def get_dossiers(request):
    
    veoservice=Veoservices.objects.all()
    ls=[]
    jsls=[]
    N=2

    Today_DateVeo=datetime.datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.datetime.strptime(Today_DateVeo, '%d/%m/%Y %H:%M')
    NBD=0
    list_Veoservices=Veoservices.objects.all()
    Rate=0
    for i in list_Veoservices:
        if i.Date_création!=None:
            Date_création=datetime.datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
            if ((Today_DateVeo-Date_création).days<=15) and i.RateFraude not in [0,'0.0',None]:
                ls.append(i)
    k=ls[0]
          
    l=ls[len(ls)-1]  
    jsls.append('[')  
    jsls.append({'Dossier':k.Dossier,'Pourcentage Fraude':k.RateFraude,'Procédure':k.Procédure,'Statut':k.Statut,'Date Création':k.Date_création,'Statut doute':k.statutdoute}) 
    for j  in  ls:
      
        if  j != k and j != l and N<1001:
            N=N+1
            jsls.append(",")
            js={'Dossier':j.Dossier,'Pourcentage Fraude':j.RateFraude,'Procédure':j.Procédure,'Statut':j.Statut,'Date Création':j.Date_création,'Statut doute':j.statutdoute}
            jsls.append(js)  
    jsls.append(",")  
    jsls.append({'Dossier':l.Dossier,'Pourcentage Fraude':l.RateFraude,'Procédure':l.Procédure,'Statut':l.Statut,'Date Création':l.Date_création,'Statut doute':l.statutdoute}) 
    jsls.append(']')
    #jsls = json.dumps(jsls)
    #jsls = json.loads(jsls)
    #jsl = [line for line in jsls]
    
    """if 'authorization' in request.headers and request.headers['authorization'] == 'Basic VeosmartAyODkwNUUteWx1LTIwTEM5RzRNQFZFT1NNQVJUV0FGQQ==':
        response = jsls
    else:
        response = json.dumps([{'Error':'Invalid Token'}])"""
    response = jsls
    return HttpResponse(response, content_type='text/json')



