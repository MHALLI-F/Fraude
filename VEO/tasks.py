from __future__ import absolute_import, unicode_literals
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
from django.core.mail import send_mail
from .views import send_fraud_alert
#from django.contrib.auth.models import User

@shared_task
def scheduledTask():
    diff = 30
    Today_DateVeo = datetime.today().strftime('%d/%m/%Y %H:%M')
    Today_DateVeo = datetime.strptime(str(Today_DateVeo), '%d/%m/%Y %H:%M')
    list_Veoservices = Veoservices.objects.exclude(Statut="Changement procédure").exclude(Date_création=None)
    Rate = 0

    for i in list_Veoservices:
        if i.Date_création is not None:
            Date_création = datetime.strptime(i.Date_création, '%d/%m/%Y %H:%M')

        if i.date_accord is not None and i.date_accord != "":
            date_accord = datetime.strptime(i.date_accord, '%d/%m/%Y %H:%M')
            diff = abs(Today_DateVeo - date_accord).days
        else:
            diff = 30

        if ((Today_DateVeo-Date_création).days<=5) and i.statutdoute == None and i.Statut !="Changement procédure" and i.Statut !="Dossier sans suite" and i.Statut !="Dossier sans suite après expertise":
            if i.Reg1() is not None:
                R1 = i.Reg1()[0]
                R1_P = i.Reg1()[1]
                R1_A = i.Reg1()[2]
            else:
                R1 = 0
                R1_P = None
                R1_A = None

            if i.Reg2() is not None:
                R2 = i.Reg2()[0]
                R2_DDA = i.Reg2()[1]
                R2_DS = i.Reg2()[2]
            else:
                R2 = 0
                R2_DDA = None
                R2_DS = None

            if i.Reg3() is not None:
                R3 = i.Reg3()[0]
                R3_DDA = i.Reg3()[1]
                R3_DS = i.Reg3()[2]
            else:
                R3 = 0
                R3_DDA = None
                R3_DS = None

            if i.Reg4() is not None:
                R4 = i.Reg4()[0]
            else:
                R4 = 0

            if i.Reg5() is not None:
                R5 = i.Reg5()[0]
                R5_Assis = i.Reg5()[1]
            else:
                R5 = 0
                R5_Assis = None

            if i.Reg6() is not None:
                R6 = i.Reg6()[0]
                R6_Assis1 = i.Reg6()[1]
                R6_Assis2 = i.Reg6()[2]
            else:
                R6 = 0
                R6_Assis1 = None
                R6_Assis2 = None

            if i.Reg7() is not None:
                R7 = i.Reg7()[0]
                R7_P = i.Reg7()[1]
                R7_A = i.Reg7()[2]
            else:
                R7 = 0
                R7_P = None
                R7_A = None

            if i.Reg9() is not None:
                R9 = i.Reg9()[0]
                R9_DFP = i.Reg9()[1]
                R9_DS = i.Reg9()[2]
            else:
                R9 = 0
                R9_DFP = None
                R9_DS = None

            if i.Reg8() is not None:
                R8 = i.Reg8()
            else:
                R8 = 0

            if i.Reg10() is not None:
                R10 = i.Reg10()[0]
                R10_Dos = i.Reg10()[1]
            else:
                R10 = 0
                R10_Dos = None

            if i.Reg11() is not None:
                R11 = i.Reg11()
            else:
                R11 = 0

            if i.Reg12() is not None:
                R12 = i.Reg12()[0]
                R12_Dos = i.Reg12()[1]
            else:
                R12 = 0
                R12_Dos = None

            if i.Reg13() is not None:
                R13 = i.Reg13()[0]
                R13_Dos = i.Reg13()[1]
            else:
                R13 = 0
                R13_Dos = None

            if i.Reg14() is not None:
                R14 = i.Reg14()
            else:
                R14 = 0

            #if i.Reg15() is not None:
                #R15 = i.Reg15()[0]
            #else:
                #R15 = 0

            #if i.Reg16() is not None:
             #   R16 = i.Reg16()[0]
            #else:
             #   R16 = 0

            #if i.Reg17() is not None:
                #R17 = i.Reg17()[0]
            #else:
                #R17 = 0

            # Calculer le taux total
            Rate = R1 + R2 + R3 + R4 + R5 + R6 + R7 + R8 + R9 + R10 + R11 + R12 + R13 + R14  
            # Appel à send_fraud_alert si Rate >=50
            #if Rate >= 50:
                #send_fraud_alert(i)

#            Veoservices.objects.filter(id=i.id).update(R1_prc=R1)
 #           Veoservices.objects.filter(id=i.id).update(R1_P=R1_P)
  #          Veoservices.objects.filter(id=i.id).update(R1_A=R1_A)
   #         Veoservices.objects.filter(id=i.id).update(R2_prc=R2)
    #        Veoservices.objects.filter(id=i.id).update(R2_DDA=R2_DDA)
     #       Veoservices.objects.filter(id=i.id).update(R2_DS=R2_DS)
      #      Veoservices.objects.filter(id=i.id).update(R3_prc=R3)
       #     Veoservices.objects.filter(id=i.id).update(R3_DDA=R3_DDA)
        #    Veoservices.objects.filter(id=i.id).update(R3_DS=R3_DS)
         #   Veoservices.objects.filter(id=i.id).update(R4_prc=R4)

          #  Veoservices.objects.filter(id=i.id).update(R4_SP=R4_SP)
           # Veoservices.objects.filter(id=i.id).update(R4_SA=R4_SA)
            #Veoservices.objects.filter(id=i.id).update(R5_prc=R5)
#            Veoservices.objects.filter(id=i.id).update(R5_Assis=R5_Assis)
#            Veoservices.objects.filter(id=i.id).update(R6_prc=R6)
 #           Veoservices.objects.filter(id=i.id).update(R6_Assis1=R6_Assis1)
  #          Veoservices.objects.filter(id=i.id).update(R6_Assis2=R6_Assis2)
   #         Veoservices.objects.filter(id=i.id).update(R7_prc=R7)
    #        Veoservices.objects.filter(id=i.id).update(R7_P=R7_P)
     #       Veoservices.objects.filter(id=i.id).update(R7_A=R7_A)
      #      Veoservices.objects.filter(id=i.id).update(R9_prc=R9)
       #     Veoservices.objects.filter(id=i.id).update(R9_DFP=R9_DFP)
        #    Veoservices.objects.filter(id=i.id).update(R9_DS=R9_DS)
         #   Veoservices.objects.filter(id=i.id).update(R8_prc=R8)
          #  Veoservices.objects.filter(id=i.id).update(R10_prc=R10)
           # Veoservices.objects.filter(id=i.id).update(R10_Dos=R10_Dos)
            #Veoservices.objects.filter(id=i.id).update(R12_prc=R12)
   #         Veoservices.objects.filter(id=i.id).update(R12_Dos=R12_Dos)
    #        Veoservices.objects.filter(id=i.id).update(R11_prc=R11)
     #       Veoservices.objects.filter(id=i.id).update(R13_prc=R13)
      #      Veoservices.objects.filter(id=i.id).update(R13_Dos=R13_Dos)
       #     Veoservices.objects.filter(id=i.id).update(R14_prc=R14)        

            if Rate<=100:  
                Veoservices.objects.filter(id=i.id).update(RateFraude=round(Rate,2))   
                Veoservices.objects.filter(id=i.id).update(statutdoute="Non traité")

# si le pourcentage est  supérieure à 100% -> 100%
            else:
                Rate>=100
                Veoservices.objects.filter(id=i.id).update(RateFraude=100)
                Veoservices.objects.filter(id=i.id).update(statutdoute="Non traité") 
   
# on met Sync = OK pour  vérifier si on  va utiliser le détail sync  ou l'ancien 
      #      veoservices.objects.filter(id=i.id).update(sync="OK") 

            break 


            # Appel à send_fraud_alert si Rate >= 50
            #if Rate >= 50:
                #send_fraud_alert(i)

    #veoservices = Veoservices.objects.exclude(Statut="Changement procédure").exclude(Date_création=None)
    #for service in veoservices:
        #if service.RateFraude > 50:
            #send_fraud_alert(service)
