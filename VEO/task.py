from __future__ import absolute_import, unicode_literals
#:wfrom celery import task
from celery import shared_task

from django.shortcuts import render, get_object_or_404
from .models import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
import datetime
from  datetime import datetime
from time import strftime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from .models import *
#from django.contrib.auth.models import User
@shared_task
def scheduledTask():
    Today_DateVeo=None
    Today_DateVeo=datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo=datetime.strptime(str(Today_DateVeo), '%d/%m/%Y %H:%M')
  #  Today_DateAss=datetime.datetime.today().strftime("%im/%d/%Y")
  #  Today_DateAss=datetime.datetime.strptime(Today_DateAss, "%m/%d/%Y")
   # Today_DateBDG=datetime.datetime.today().strftime("%m/%d/%Y %H:%M")
  #  Today_DateBDG=datetime.datetime.strptime(Today_DateBDG, "%m/%d/%Y %H:%M")
    list_Veo_recente=[]
    list_Veoservices=Veoservices.objects.filter(RateFraude=None).exclude(Statut= "Changement procédure").exclude(Date_création=None)
    Rate=0
    for i in list_Veoservices:
      #  if i.Date_création!=None:
        Date_création=datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')
        date_accord=datetime.strptime(i.date_accord, '%d/%m/%Y %H:%M')
        if (((Today_DateVeo-Date_création).days<=4) or i.statutdoute == None) or (Today_DateVeo-date_accord).days<=2 :
            if i.Reg1()!=None:
                R1=i.Reg1()[0] 
            else: 
                R1=0
            if i.Reg2()!=None:
                R2=i.Reg2()[0]
            else: 
                R2=0 
            if i.Reg3()!=None:
                R3=i.Reg3()[0] 
            else: 
                R3=0    
            if i.Reg4()!=None:
                R4=i.Reg4()[0]
            else: 
                R4=0 
            if i.Reg5()!=None:
                R5=i.Reg5()[0]
            else: 
                R5=0
            if i.Reg6()!=None:
                R6=i.Reg6()[0]
            else:
                R6=0
            if i.Reg7()!=None:
                R7=i.Reg7()[0] 
            else: 
                R7=0
            if i.Reg9()!=None:
                R9=i.Reg9()[0] 
            else: 
                R9=0
            if i.Reg8()!=None:
                R8=i.Reg8() 
            else: 
                R8=0

            if i.Reg10()!=None:
                R10=i.Reg10()[0]
            else: 
                R10=0
            
            if i.Reg11()!=None:
                R11=i.Reg11() 
            else: 
                R11=0

            
            Rate=R1+R2+R3+R4+R5+R6+R7+R9+R8+R10+R11
         #   Veoservices.objects.filter(id=i.id).update(calcul="oui")
            if Rate<=100:  
                Veoservices.objects.filter(id=i.id).update(RateFraude=round(Rate,2))   
                Veoservices.objects.filter(id=i.id).update(statutdoute="Non traité")
            else:
                Rate=100
                Veoservices.objects.filter(id=i.id).update(RateFraude=Rate)
                Veoservices.objects.filter(id=i.id).update(statutdoute="Non traité")    
            break 
            #Veoservices.objects.filter(Dossier=i.Dossier).update(calcul="oui")
        #list_Veoservices.sort(key=lambda r: r.RateFraude,reverse=True) 
        #list_Veo_recente=[list_Veodata[0],list_Veodata[1],list_Veodata[2],list_Veodata[3],list_Veodata[4]]
        #list_Assistance.sort(key=lambda r: r.RateFraude,reverse=True)
        #list_Assistance_recente=[list_Assistance[0],list_Assistance[1],list_Assistance[2],list_Assistance[3],list_Assistance[4]]
        #list_BDG.sort(key=lambda r: r.RateFraude,reverse=True)
        #list_BDG_recente=[list_BDG[0],list_BDG[1],list_BDG[2],list_BDG[3],list_BDG[4]]5 
