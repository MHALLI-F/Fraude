from django.db import models
from datetime import datetime
from django.db.models import Q


# nettoyage  de  numéro de  chassis
def net_numch(a):
    a=a.replace(' ','').replace('-','').replace('_','').replace(',','').replace('.','').replace('*','')
    return a


def str_to_float(stri):
    if stri == "" or stri == "'0.0'" or stri  == None:
        stri=0.0
    else:
        stri=float(stri)
    return stri




# Create your models here.
def inter_dt(dtV , dtE):  
    if (dtV and dtE):  
        dtV = datetime.strptime(dtV, "%d/%m/%Y").date()
        dtE = datetime.strptime(dtE, "%d/%m/%Y").date()
        return abs(dtV - dtE).days 
def inter_dt2(dtV,dtE):  
    if (dtV and dtE):  
        dtV= datetime.strptime(dtV, "%d/%m/%Y").date()
        dtE = datetime.strptime(dtE, "%d/%m/%Y").date()
        return abs(dtE- dtV).days 

############################################################### Nettoyage des immatriculations
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
            # cette fonction élimine les immatriculation qui sont tous des zéros et qui sont tous des lettres 
            #a=test(a)
            return a

class Collaborateur(models.Model):
    id = models.TextField(primary_key=True)
    email = models.EmailField(max_length=254, unique=True)
    nom = models.TextField(max_length=100)

    def __str__(self):
        return self.nom

class Veodata(models.Model):
    id = models.TextField(primary_key=True)
    Collaborateur = models.ForeignKey(Collaborateur, on_delete=models.SET_NULL, null=True, related_name='veodata')
    Type=models.TextField()
    ContactName=models.TextField()
    Immatriculation=models.TextField()
    ImmatriculationAdverse=models.TextField()
    Okpoursouscription=models.TextField()
    Statutgarage=models.TextField()
    CreatedDate=models.TextField()
    Datesinistre=models.TextField()
    Nomintermédiairecp=models.TextField()
    Assigned_ID=models.TextField(null=True)
    Garage = models.TextField(null=True) 
    def strtodate(self):
        if self.CreatedDate!=None and self.CreatedDate!="":
            self.CreatedDate=datetime.strptime(self.CreatedDate, "%Y-%m-%d %H:%M:%S")
        if self.Datesinistre!="" and self.Datesinistre!=None:
            
            self.Datesinistre=datetime.strptime(self.Datesinistre, "%Y-%m-%d")
        return self


class Assistance(models.Model):
    id = models.TextField(primary_key=True)
    Type=models.TextField()
    Prestataire=models.TextField()

    Statut=models.TextField()
#    RéférenceVeo=models.TextField()
    Intervention=models.TextField()
    Immatriculation=models.TextField()
    Nomclient=models.TextField(null=True)
    PhotosRemorquage=models.TextField(null=True)
    PhotosConstat=models.TextField(null=True)
    DateRemorquage=models.TextField(null=True)
    DateConstat=models.TextField(null=True)
    Ref_knk=models.TextField(null=True)   
    
    def strtodate(self):
        if self.DateAssistance!=None:
            self.DateAssistance=datetime.strptime(self.DateAssistance, "%d/%m/%Y")
        return self

class Bris_De_Glace(models.Model):
    id = models.AutoField(primary_key=True)
    Type=models.TextField()
    Référencedossier=models.TextField()
    Immatriculation=models.TextField()
    Datesinistre=models.TextField()
    NomAssuré_souscripteur=models.TextField()
    PhotosAvant=models.TextField()
    PhotosAprès=models.TextField()
    Statut=models.TextField()
    Datedecréation=models.TextField()


    def strtodate(self):
        if self.Datedecréation!=None and self.Datesinistre!=None:
            self.Datedecréation=datetime.strptime(self.Datedecréation, "%d/%m/%Y %H:%M")
            self.Datesinistre=datetime.strptime(self.Datesinistre, "%d/%m/%Y")
        return self

   
class Veoservices(models.Model):
    id = models.TextField(primary_key=True)
    Ref_knk=models.TextField(null=True)
    Dossier=models.TextField(null=True)
    Statut=models.TextField(null=True)
    GaragePN=models.TextField(null=True)
    Date_sinistre=models.TextField(null=True)
    Garantie=models.TextField(null=True)
    Procédure=models.TextField(null=True)
    Expert=models.TextField(null=True)
    Immatriculation=models.TextField(null=True)
    Date_création=models.TextField(null=True)
    Date_validité_début=models.TextField(null=True)
    Date_validité_fin=models.TextField(null=True)	
    Date_validité_début_Adv=models.TextField(null=True)	
    Date_validité_fin_Adv=models.TextField(null=True)	
    RateFraude = models.FloatField(null=True, blank=True)
    Photos_Avant=models.TextField(null=True)	
    Photos_en_cours=models.TextField(null=True)	
    Photos_après_réparation=models.TextField(null=True)
    ImmatriculationAdverse=models.TextField(null=True)
    calcul=models.TextField(null=True)
    R1=models.TextField(null=True)
    R2=models.TextField(null=True)
    R3=models.TextField(null=True)
    R4=models.TextField(null=True)
    R5=models.TextField(null=True)
    R6=models.TextField(null=True)
    R7=models.TextField(null=True)
    R8=models.TextField(null=True)
    R9=models.TextField(null=True)
    R10=models.TextField(null=True)
    R11=models.TextField(null=True)
    R12=models.TextField(null=True)
    R13=models.TextField(null=True)
    R14=models.TextField(null=True)
    
    R15=models.TextField(null=True)
    R16=models.TextField(null=True)
    R17=models.TextField(null=True)

    
    date_obs=models.DateTimeField(null=True)
    observation=models.TextField(null=True)
    statutdoute=models.TextField(null=True)
    statutdt_omega=models.TextField(null=True)
    num_chassis=models.TextField(null=True)
    date_accord=models.TextField(null=True)
    montant_devis=models.TextField(null=True)
    utilisateur=models.TextField(null=True)
    email_traitement=models.TextField(null=True)
    accord=models.TextField(null=True)
    Dossier_douteux=models.TextField(null=True)
    Dossier_ass=models.TextField(null=True)
    Dossier_ass3=models.TextField(null=True)
    Dossier_sous=models.TextField(null=True)
    Dossier_12Mois=models.TextField(null=True)
    Dossier_MMchassis=models.TextField(null=True)
    Dossier_MMImmats=models.TextField(null=True)

#ce champs = OK si le calcul est fait après la synchronisation du detail ou avant
    sync=models.TextField(null=True)
    # pourcentage de règle 1 (prc=pourcentage)
    
    def strtodate(self):
        if self.Date_création!=None and self.Date_sinistre!=None and self.Date_validité_début_Adv!=None and self.Date_validité_fin_Adv!=None and self.Date_validité_fin!=None and self.Date_validité_début!=None:        
            self.Date_création=datetime.strptime(self.Date_création, "%Y-%m-%d %H:%M:%S")
            self.Date_sinistre=datetime.strptime(self.Date_sinistre, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_début=datetime.strptime(self.Date_validité_début, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_fin=datetime.strptime(self.Date_validité_fin, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_début_Adv=datetime.strptime(self.Date_validité_début_Adv, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_fin_Adv=datetime.strptime(self.Date_validité_fin_Adv, "%Y-%m-%d %H:%M:%S")     
        return self
    
    def convert_to_datetime(self, date_str):
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
        return None 


    def Reg1(self):
    
        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        Rate, R, doute_Princ, doute_Adv = 0, None, None, None


        q_main = Q(Statutgarage="Cas douteux", Immatriculation=processed_immatriculation) if processed_immatriculation else Q()
        q_adverse = Q(Statutgarage="Cas douteux", ImmatriculationAdverse=processed_immatriculation_adverse) if processed_immatriculation_adverse else Q()


        if q_main:
            doute_Princ = Veodata.objects.filter(q_main).first()
            if doute_Princ:
                Rate = 30
                R = f"30%: l'immatriculation principale a déjà été impliquée dans un dossier historique signalé douteux: {doute_Princ.id}"

        if not Rate and q_adverse:
            doute_Adv = Veodata.objects.filter(q_adverse).first()
            if doute_Adv:
                Rate = 30
                R = f"30%: l'immatriculation adverse a déjà été impliquée dans un dossier historique signalé douteux: {doute_Adv.id}"


        Veoservices.objects.filter(id=self.id).update(R1=R)
        return [Rate, doute_Princ, doute_Adv]

        
    def Reg2(self):

        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        Rate = 0
        R = None

        immatriculation_ww_check = (processed_immatriculation and processed_immatriculation.startswith('WW')) == (processed_immatriculation_adverse and processed_immatriculation_adverse.startswith('WW'))

        if immatriculation_ww_check and (processed_immatriculation or processed_immatriculation_adverse) and self.Date_validité_début and self.Date_sinistre:

            date_validité_début = datetime.strptime(self.Date_validité_début, "%d/%m/%Y")
            date_sinistre = datetime.strptime(self.Date_sinistre, "%d/%m/%Y")

            diff_sous_sinis = (date_sinistre - date_validité_début).days

            if 0 <= diff_sous_sinis <= 2:
                Rate = 20
                R = f"20%: Ce sinistre est survenu moins d'un mois après la date début d'assurance: {date_validité_début.strftime('%d/%m/%Y')}"
            elif 2 <= diff_sous_sinis <= 30:
                Rate = 10
                R = f"10%: Ce sinistre est survenu moins de 2 jours après la date début d'assurance: {date_validité_début.strftime('%d/%m/%Y')}"

        if R:
            Veoservices.objects.filter(id=self.id).update(R2=R)

        return [Rate, self.Date_validité_début, self.Date_sinistre]
    
    def  Reg3(self):
        R=None
        R=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        Rate=0      
        #self.strtodate()
        DDA=self.Date_validité_début_Adv
        date_sinis=self.Date_sinistre
        if date_sinis!=None or date_sinis!="":
            if DDA!=None:
                diff_sous_sinis=inter_dt2(date_sinis, DDA)
                if diff_sous_sinis!=None  and 0<=diff_sous_sinis<=2:
                    Rate=20  
                    R="20%: sinistre survenu moins d'un mois après date début d'assurance de la partie adverse: "+self.Date_validité_début_Adv
                elif diff_sous_sinis!=None  and 2<diff_sous_sinis<=30:
                    Rate=10
                    R="10%: Ce sinistre survenu moins de 2 jours après la début d'assurance: "+self.Date_validité_début_Adv
                else:
                    DDA=None
                    date_sinis=None      
        else:
            DDA=None
            date_sinis=None     
        Veoservices.objects.filter(id=self.id).update(R3=R)   
        return [Rate,DDA,date_sinis]
        
        
    def Reg4(self):
        Rate = 0
        R = None
        A = None
        P = None


        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        if processed_immatriculation:
            dossiers_principaux = Veodata.objects.filter(
                Type__icontains="Souscription",
                Okpoursouscription="NOK",
                Immatriculation=processed_immatriculation
            )

            for dossier in dossiers_principaux:
                Rate = 15
                R = f"15%: l'immatriculation adverse a été signalée comme souscription NOK voir le dossier {dossier.id}"
                A = dossier
                break  

        #  vérifier les immatriculations adverses
        if not Rate and processed_immatriculation_adverse:
            dossiers_adverses = Veodata.objects.filter(
                Type__icontains="Souscription",
                Okpoursouscription="NOK",
                Immatriculation=processed_immatriculation_adverse
            )

            for dossier in dossiers_adverses:
                Rate = 15
                R = f"15%: l'immatriculation principale a été signalée comme souscription NOK voir le dossier {dossier.id}"
                P = dossier
                break  

  
        Veoservices.objects.filter(id=self.id).update(R4=R)

        return [Rate, P, A]


    def Reg5(self):
        Rate = 0
        A = None
        R = None


        Date_création = datetime.strptime(self.Date_sinistre, "%d/%m/%Y")

        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None

        if processed_immatriculation:

            assistances = Assistance.objects.filter(
                Immatriculation=processed_immatriculation,
                DateConstat__isnull=False
            ).filter(
                PhotosConstat__isnull=False
            ) | Assistance.objects.filter(
                Immatriculation=processed_immatriculation,
                DateRemorquage__isnull=False
            ).filter(
                PhotosRemorquage__isnull=False
            )

   
            for assistance in assistances:
                if assistance.Intervention == "Remorquage" and assistance.DateRemorquage:
                    DateAssistance = datetime.strptime(assistance.DateRemorquage, "%d/%m/%Y %H:%M")
                    if 0 <= (DateAssistance - Date_création).days <= 5 and (DateAssistance.hour < 7 or DateAssistance.hour >= 20):
                        Rate = 10
                        R = f"10%: La date assistance du dossier: {assistance.id} est après 20h ou avant 7h du matin"
                        A = assistance
                        break
                elif assistance.DateConstat:
                    DateAssistance = datetime.strptime(assistance.DateConstat, "%d/%m/%Y %H:%M")
                    if 0 <= (DateAssistance - Date_création).days <= 5 and (DateAssistance.hour < 7 or DateAssistance.hour >= 20):
                        Rate = 10
                        R = f"10%: La date assistance du dossier: {assistance.id} est après 20h ou avant 7h du matin"
                        A = assistance
                        break

        Veoservices.objects.filter(id=self.id).update(R5=R)

        return [Rate, A]


    def Reg6(self):
        Rate = 0
        R = None
        A1 = None
        A2 = None

        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        assistances_constat = Assistance.objects.filter(
            Q(Immatriculation=processed_immatriculation) | Q(Immatriculation=processed_immatriculation_adverse),
            PhotosConstat__isnull=False,
            DateConstat__isnull=False
        )

        assistances_remorquage = Assistance.objects.filter(
            Q(Immatriculation=processed_immatriculation) | Q(Immatriculation=processed_immatriculation_adverse),
            PhotosRemorquage__isnull=False,
            DateRemorquage__isnull=False
        )

        for assistances in [assistances_constat, assistances_remorquage]:
            for i, assistance1 in enumerate(assistances):
                for assistance2 in assistances[i + 1:]:
                    
                    date_str1 = assistance1.DateConstat if assistance1 in assistances_constat else assistance1.DateRemorquage
                    date_str2 = assistance2.DateConstat if assistance2 in assistances_constat else assistance2.DateRemorquage

                    if date_str1 and date_str2: 
                        try:
                            date_assistance1 = datetime.strptime(date_str1, "%d/%m/%Y %H:%M")
                            date_assistance2 = datetime.strptime(date_str2, "%d/%m/%Y %H:%M")
                            # Calcul de la différence de jours et mise à jour du taux si nécessaire
                            if 1 < abs((date_assistance2 - date_assistance1).days) <= 90:
                                Rate = 5
                                R = f"5%: les 2 dossiers {assistance2.id} et {assistance1.id} ont moins de 3 mois de distance"
                                A1, A2 = assistance1, assistance2
                                break
                        except ValueError as e:
                            print(f"Erreur de format de date: {e}")
                    if Rate:
                        break
        Veoservices.objects.filter(id=self.id).update(R6=R)
        return [Rate, A1, A2]

    def Reg7(self):
        if self.Procédure and "Souscription" not in self.Procédure:
            Rate = 0
            R = None
            A = None
            P = None

            
            processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
            processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

            date_sinistre_self = datetime.strptime(self.Date_sinistre, "%d/%m/%Y")


            if processed_immatriculation:
                sinistres_principal = Veoservices.objects.filter(
                    Immatriculation=processed_immatriculation
                ).exclude(
                    Date_sinistre=self.Date_sinistre
                ).exclude(
                    Statut="Changement de procédure"
                )

                for sinistre in sinistres_principal:
                    date_sinistre_sinistre = datetime.strptime(sinistre.Date_sinistre, "%d/%m/%Y")
                    diff = abs((date_sinistre_self - date_sinistre_sinistre).days)
                    if 1 < diff <= 365:
                        Rate = 5
                        R = f"5%: l'immatriculation principale a déjà fait l'objet d'un sinistre il y'a moins de 12 mois {sinistre.Dossier}"
                        P = sinistre
                        break

            if not Rate and processed_immatriculation_adverse:
                sinistres_adverse = Veoservices.objects.filter(
                    Immatriculation=processed_immatriculation_adverse
                ).exclude(
                    Date_sinistre=self.Date_sinistre
                ).exclude(
                    Statut="Changement de procédure"
                )

                for sinistre in sinistres_adverse:
                    date_sinistre_sinistre = datetime.strptime(sinistre.Date_sinistre, "%d/%m/%Y")
                    diff = abs((date_sinistre_self - date_sinistre_sinistre).days)
                    if 1 < diff <= 365:
                        Rate = 5
                        R = f"5%: l'immatriculation adverse a déjà fait l'objet d'un sinistre il y'a moins de 12 mois {sinistre.Dossier}"
                        A = sinistre
                        break

            Veoservices.objects.filter(id=self.id).update(R7=R)

            return [Rate, P, A]


    def Reg9(self):
        R = None
        Rate = 0
        DFP = self.Date_validité_fin
        date_sinis = self.Date_sinistre

        if self.Garantie and date_sinis and "tierce" in self.Garantie.lower():
            if DFP:

                date_sinis_dt = datetime.strptime(date_sinis, "%d/%m/%Y")
                DFP_dt = datetime.strptime(DFP, "%d/%m/%Y")
                
                diff_sous_sinis = (DFP_dt - date_sinis_dt).days

                if 0 < diff_sous_sinis <= 30:
                    Rate = 5
                    R = f"5%: La garantie est Tierce et il reste moins d'un mois avant la fin de validité de contrat: {self.Date_validité_fin}"

        Veoservices.objects.filter(id=self.id).update(R9=R)
        return [Rate, DFP, date_sinis]


        
    def Reg8(self):
        R = None
        Rate = 0


        if self.Immatriculation and len(self.Immatriculation) > 3:
            self.Immatriculation = Preprocessing_Imm(self.Immatriculation)

        if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3:
            self.ImmatriculationAdverse = Preprocessing_Imm(self.ImmatriculationAdverse)

        if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) >= 12:
            Rate = 10
            R = f"10%: La partie adverse est un cyclo: {self.ImmatriculationAdverse}"
        elif self.Immatriculation and len(self.Immatriculation) >= 12:
            Rate = 10
            R = f"10%: La partie principale est un cyclo: {self.Immatriculation}"

        Veoservices.objects.filter(id=self.id).update(R8=R)
        
        return Rate


    def Reg10(self):
        R = None
        Rate = 0
        Doss = None

        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_num_chassis = net_numch(self.num_chassis) if self.num_chassis and len(self.num_chassis) > 3 else None

        if processed_num_chassis:

            sinistres = Veoservices.objects.filter(
                num_chassis=processed_num_chassis
            ).exclude(
                Immatriculation__in=["WW", "XXXXXX", "aaaaa", "xxxxx"]
            ).exclude(
                num_chassis__in=["", "XXXXXX", "aaaaa", "xxxxx"]
            )

            for sinistre in sinistres:
                sinistre_immatriculation = Preprocessing_Imm(sinistre.Immatriculation) if sinistre.Immatriculation and len(sinistre.Immatriculation) > 3 else None
                if sinistre_immatriculation and sinistre_immatriculation != processed_immatriculation:
                    Rate = 30
                    R = f"Ce véhicule a une déclaration avec Immatriculation différente et même numéro de chassis: {sinistre.Dossier}"
                    Doss = sinistre
                    break

        Veoservices.objects.filter(id=self.id).update(R10=R)
        
        return [Rate, Doss]


    def Reg11(self):
        R = None
        Rate = 0
        if self.montant_devis is not None:
            montant_devis_str = str(self.montant_devis).replace(' Dhs', '').replace(',', '.').replace(' ', '')
            montant_devis = str_to_float(montant_devis_str)

            if 18000.00 <= montant_devis < 20000.00:
                Rate = 10
                R = f"Le montant de devis est entre 18000 et 20000: {montant_devis}"
        Veoservices.objects.filter(id=self.id).update(R11=R)

        return Rate


    def Reg12(self):
        R = None
        Rate = 0
        Doss = None


        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        if processed_immatriculation and processed_immatriculation_adverse:

            sinistres = Veoservices.objects.exclude(
                Statut="Changement procédure"
            ).exclude(
                Dossier=self.Dossier
            ).exclude(
                Date_sinistre=self.Date_sinistre
            ).filter(
                Immatriculation=processed_immatriculation,
                ImmatriculationAdverse=processed_immatriculation_adverse
            )

            for sinistre in sinistres:
                Rate = 30
                R = f"Il y a un autre sinistre avec la même Immatriculation Principale et Adverse: {sinistre.Dossier}"
                Doss = sinistre
                break

            if not Rate:

                sinistres_inverses = Veoservices.objects.exclude(
                    Statut="Changement procédure"
                ).exclude(
                    Dossier=self.Dossier
                ).exclude(
                    Date_sinistre=self.Date_sinistre
                ).filter(
                    Immatriculation=processed_immatriculation_adverse,
                    ImmatriculationAdverse=processed_immatriculation
                )

                for sinistre in sinistres_inverses:
                    Rate = 30
                    R = f"Il y a un autre sinistre avec la même Immatriculation Principale et Adverse: {sinistre.Dossier}"
                    Doss = sinistre
                    break


        Veoservices.objects.filter(id=self.id).update(R12=R)

        return [Rate, Doss]


    def Reg13(self):
        R = None
        Rate = 0
        Doss = None

  
        processed_immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        processed_immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        if processed_immatriculation or processed_immatriculation_adverse:
            sinistres = Veoservices.objects.exclude(
                Dossier=self.Dossier
            ).filter(
                Q(Immatriculation=processed_immatriculation) |
                Q(ImmatriculationAdverse=processed_immatriculation_adverse) |
                Q(Immatriculation=processed_immatriculation_adverse) |
                Q(ImmatriculationAdverse=processed_immatriculation)
            ).filter(
                ~Q(Statut="Changement de procédure")
            )

            for sinistre in sinistres:
                if processed_immatriculation and sinistre.Immatriculation == processed_immatriculation and sinistre.statutdt_omega in ["Doute confirmé", "Doute confirmé RMAA"]:
                    Rate = 30
                    R = f"l'immatriculation principale a déjà été impliquée dans un dossier historique doute confirmé : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation_adverse and sinistre.Immatriculation == processed_immatriculation_adverse and sinistre.statutdt_omega in ["Doute confirmé", "Doute confirmé RMAA"]:
                    Rate = 30
                    R = f"l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute confirmé : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation and sinistre.ImmatriculationAdverse == processed_immatriculation and sinistre.statutdt_omega in ["Doute confirmé", "Doute confirmé RMAA"]:
                    Rate = 30
                    R = f"l'immatriculation principale a déjà été impliquée dans un dossier historique doute confirmé : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation_adverse and sinistre.ImmatriculationAdverse == processed_immatriculation_adverse and sinistre.statutdt_omega in ["Doute confirmé", "Doute confirmé RMAA"]:
                    Rate = 30
                    R = f"l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute confirmé : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation and sinistre.Immatriculation == processed_immatriculation and sinistre.statutdt_omega not in ["Doute rejeté", "Doute rejeté RMAA"]:
                    Rate = 15
                    R = f"l'immatriculation principale a déjà été impliquée dans un dossier historique doute rejeté : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation_adverse and sinistre.ImmatriculationAdverse == processed_immatriculation_adverse and sinistre.statutdt_omega not in ["Doute rejeté", "Doute rejeté RMAA"]:
                    Rate = 15
                    R = f"l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute rejeté : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation and sinistre.ImmatriculationAdverse == processed_immatriculation and sinistre.statutdt_omega not in ["Doute rejeté", "Doute rejeté RMAA"]:
                    Rate = 15
                    R = f"l'immatriculation principale a déjà été impliquée dans un dossier historique doute rejeté : {sinistre.Dossier}"
                    Doss = sinistre
                    break
                elif processed_immatriculation_adverse and sinistre.Immatriculation == processed_immatriculation_adverse and sinistre.statutdt_omega not in ["Doute rejeté", "Doute rejeté RMAA"]:
                    Rate = 15
                    R = f"l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute rejeté : {sinistre.Dossier}"
                    Doss = sinistre
                    break

        Veoservices.objects.filter(id=self.id).update(R13=R)
        return [Rate, Doss]


    def Reg14(self):
        R=None
        Rate=0
        if (self.statutdt_omega == "Dossier initié" or self.statutdt_omega == "Dossier initié RMAA" or self.statutdt_omega == "Doute créé" or self.statutdt_omega == "Dossier envoyé"  or self.statutdt_omega == "Affecté expert" or self.statutdt_omega == "Retour expert" or self.statutdt_omega == "Attente photos avant")  :    
            Rate=15
            R="Ce sinistre est en  instruction "
        Veoservices.objects.filter(id=self.id).update(R14=R) 
        return Rate

    def Reg15(self):
        Rate = 0
        R = None
        common_contact = None  

        immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        common_contacts = set()  

        if immatriculation and immatriculation_adverse:
            primary_contacts = Veodata.objects.filter(Immatriculation=immatriculation).values_list('ContactName', flat=True).distinct()
            adverse_contacts = Veodata.objects.filter(Immatriculation=immatriculation_adverse).values_list('ContactName', flat=True).distinct()

            common_contacts = set(primary_contacts).intersection(adverse_contacts)

            if common_contacts:
                Rate = 5
                common_contact = list(common_contacts)[0]  
                R = f"5%: Le même nom '{common_contact}' est associé aux deux immatriculations impliquées dans le dossier."

        Veoservices.objects.filter(id=self.id).update(R15=R)
        return [Rate, common_contact]  




    def Reg16(self):
        Rate = 0
        R = None
        doute_Princ = None
        doute_Adv = None
        i = None  

        immatriculation = Preprocessing_Imm(self.Immatriculation) if self.Immatriculation and len(self.Immatriculation) > 3 else None
        immatriculation_adverse = Preprocessing_Imm(self.ImmatriculationAdverse) if self.ImmatriculationAdverse and len(self.ImmatriculationAdverse) > 3 else None

        garage_pn = self.GaragePN

        Liste = Veodata.objects.all()

        for j in Liste:
            if (immatriculation and (Preprocessing_Imm(j.Immatriculation) == immatriculation or Preprocessing_Imm(j.ImmatriculationAdverse) == immatriculation)) and (j.Garage == garage_pn) and (j.Statutgarage.lower() == "cas douteux"):
                Rate = 30
                R = f"30%: l'immatriculation principale et son garage ont déjà été impliqués dans un dossier historique signalé douteux: {j.id}"
                doute_Princ = j
                i = j  
                break

        if not Rate:
            for i in Liste:
                if (immatriculation_adverse and (Preprocessing_Imm(i.Immatriculation) == immatriculation_adverse or Preprocessing_Imm(i.ImmatriculationAdverse) == immatriculation_adverse)) and (i.Garage == garage_pn) and (i.Statutgarage.lower() == "cas douteux"):
                    Rate = 30
                    R = f"30%: l'immatriculation adverse et son garage ont déjà été impliqués dans un dossier historique signalé douteux: {i.id}"
                    doute_Adv = i
                    break

        self.R16 = R
        self.save()
        return [Rate, i.id if i else None]



    def Reg17(self):
        Rate = 0
        R = None
        intermediaire_principal = None

        veodata = Veodata.objects.filter(Immatriculation=self.Immatriculation).first()

        if veodata:
            intermediaire_principal = veodata.Nomintermédiairecp.strip().lower() if veodata.Nomintermédiairecp else ''
            intermediaire_adverse = veodata.Nomintermédiairecp.strip().lower() if veodata.Nomintermédiairecp else ''

            # Vérifier si le même intermédiaire est impliqué des deux côtés
            if intermediaire_principal and intermediaire_principal == intermediaire_adverse:
                Rate = 5
                R = f"5%: Le même intermédiaire '{intermediaire_principal}' est impliqué des deux côtés du sinistre."

        self.R17 = R 
        self.save()
        return [Rate, intermediaire_principal]

    


class veotest(models.Model):
    id = models.TextField(primary_key=True)
    Ref_knk=models.TextField()
    Dossier=models.TextField()
    Statut=models.TextField()
    Date_sinistre=models.TextField()
    Garantie=models.TextField()
    Procédure=models.TextField()
    Expert=models.TextField()
    Immatriculation=models.TextField()
    Date_création=models.TextField()
    Date_validité_début=models.TextField()
    Date_validité_fin=models.TextField()	
    Date_validité_début_Adv=models.TextField()	
    Date_validité_fin_Adv=models.TextField()	
    RateFraude=models.FloatField()
    Photos_Avant=models.TextField()	
    Photos_en_cours=models.TextField()	
    Photos_après_réparation=models.TextField()
    ImmatriculationAdverse=models.TextField()
    calcul=models.TextField()
    R1=models.TextField()
    R2=models.TextField()
    R3=models.TextField()
    R4=models.TextField()
    R5=models.TextField()
    R6=models.TextField()
    R7=models.TextField()
    R8=models.TextField()
    R9=models.TextField()
    R10=models.TextField()
    R11=models.TextField()
    R12=models.TextField()
    R13=models.TextField()
    R14=models.TextField()
    date_obs=models.DateTimeField()
    observation=models.TextField()
    statutdoute=models.TextField()
    statutdt_omega=models.TextField()
    num_chassis=models.TextField()
    date_accord=models.TextField()
    montant_devis=models.TextField()
    utilisateur=models.TextField()
    email_traitement=models.TextField()
    accord=models.TextField()
    Dossier_douteux=models.TextField()
    Dossier_ass=models.TextField()
    Dossier_ass3=models.TextField()
    Dossier_sous=models.TextField()
    Dossier_12Mois=models.TextField()
    Dossier_MMchassis=models.TextField()
    Dossier_MMImmats=models.TextField()
    
#ce champs = OK si le calcul est fait après la synchronisation du detail ou avant
    sync=models.TextField()
    # pourcentage de règle 1 (prc=pourcentage)
    class Meta:
        managed = False

    def strtodate(self):
        if self.Date_création!=None and self.Date_sinistre!=None and self.Date_validité_début_Adv!=None and self.Date_validité_fin_Adv!=None and self.Date_validité_fin!=None and self.Date_validité_début!=None:        
            self.Date_création=datetime.strptime(self.Date_création, "%Y-%m-%d %H:%M:%S")
            self.Date_sinistre=datetime.strptime(self.Date_sinistre, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_début=datetime.strptime(self.Date_validité_début, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_fin=datetime.strptime(self.Date_validité_fin, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_début_Adv=datetime.strptime(self.Date_validité_début_Adv, "%Y-%m-%d %H:%M:%S")
            self.Date_validité_fin_Adv=datetime.strptime(self.Date_validité_fin_Adv, "%Y-%m-%d %H:%M:%S")     
        return self

    def convert_to_datetime(self, date_str):
        """Convertit une chaîne de date au format 'YYYY-MM-DD HH:MM:SS' en objet datetime."""
        if date_str:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return None  

    def Reg1(self):
        R=None
        Rate=0
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        Liste=list(Veodata.objects.all())

        for j in Liste:
              #Eviter  les  cas  douteux  avec la  mm  ref  dossier   
           # if (self.Dossier != j.id) and (self.Immatriculation not in [None,""] and len(j.Immatriculation) not in [1,2,3]) and (Preprocessing_Imm(j.Immatriculation) == self.Immatriculation or Preprocessing_Imm(j.ImmatriculationAdverse) == self.Immatriculation) and ((j.Statutgarage is not  None) and (j.Statutgarage.lower()=="cas douteux")):
            if   (self.Immatriculation not in [None,""] and len(j.Immatriculation) not in [1,2,3]) and (Preprocessing_Imm(j.Immatriculation) == self.Immatriculation or Preprocessing_Imm(j.ImmatriculationAdverse) == self.Immatriculation) and ((j.Statutgarage is not  None) and (j.Statutgarage.lower()=="cas douteux")):
                
                Rate=30
                R="30%: l'immatriculation principale a déjà été impliquée dans un dossier historique signalé douteux "+str(j.id)
                #La declaration douteux pour  afficher le  détail
                doute_Princ=j
                break
            else:
                doute_Princ=None
        for i in Liste:
           # if (self.Dossier != i.id) and  (self.ImmatriculationAdverse not in [None,""] and len(i.Immatriculation) not in [1,2,3]) and( Preprocessing_Imm(i.Immatriculation) == self.ImmatriculationAdverse or Preprocessing_Imm(i.ImmatriculationAdverse) == self.ImmatriculationAdverse) and ((i.Statutgarage is not  None) and (i.Statutgarage.lower()=="cas douteux")):
            if (self.ImmatriculationAdverse not in [None,""] and len(i.Immatriculation) not in [1,2,3]) and( Preprocessing_Imm(i.Immatriculation) == self.ImmatriculationAdverse or Preprocessing_Imm(i.ImmatriculationAdverse) == self.ImmatriculationAdverse) and ((i.Statutgarage is not  None) and (i.Statutgarage.lower()=="cas douteux")):
                    
                Rate=30
                R="30%: l'immatriculation adverse a déjà été impliquée dans un dossier historique signalé douteux: "+str(i.id)
                #La declaration douteux pour  afficher le  détail
                doute_Adv=i
                break 
            else:
                doute_Adv=None
        veotest.objects.filter(id=self.id).update(R1=R)       
        return [Rate,doute_Princ,doute_Adv]

    def Reg2(self):
        R=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        Rate=0
        #self.strtodate()
        DDP=self.Date_validité_début
        date_sinis=self.Date_sinistre
        if date_sinis!=None or date_sinis!="":
            if DDP!=None:
                diff_sous_sinis=inter_dt2(date_sinis, DDP)
                if diff_sous_sinis!=None  and 0<=diff_sous_sinis<=2:
                    Rate=20  
                    R="20%: Ce sinistre survenu moins d'un mois après la date début d'assurance: "+self.Date_validité_début
                elif diff_sous_sinis!=None  and  2<diff_sous_sinis<=30:
                    Rate=10
                    R="10%: Ce sinistre survenu moins de 2 jours après la début d'assurance: "+self.Date_validité_début
                else:
                    DDP=None
                    date_sinis=None
        veotest.objects.filter(id=self.id).update(R2=R)   
        return [Rate,DDP,date_sinis]
    
    def  Reg3(self):
        R=None
        R=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        Rate=0      
        #self.strtodate()
        DDA=self.Date_validité_début_Adv
        date_sinis=self.Date_sinistre
        if date_sinis!=None or date_sinis!="":
            if DDA!=None:
                diff_sous_sinis=inter_dt2(date_sinis, DDA)
                if diff_sous_sinis!=None  and 0<=diff_sous_sinis<=2:
                    Rate=20  
                    R="20%: sinistre survenu moins d'un mois après date début d'assurance de la partie adverse: "+self.Date_validité_début_Adv
                elif diff_sous_sinis!=None  and 2<diff_sous_sinis<=30:
                    Rate=10
                    R="10%: Ce sinistre survenu moins de 2 jours après la début d'assurance: "+self.Date_validité_début_Adv
                else:
                    DDA=None
                    date_sinis=None      
        else:
            DDA=None
            date_sinis=None     
        veotest.objects.filter(id=self.id).update(R3=R)   
        return [Rate,DDA,date_sinis]
        
        

    def Reg4(self):
        Rate=0
        R=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
         

        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        Liste=list(Veodata.objects.filter( Type__icontains="Souscription"))
        for A in Liste:
            if self.Immatriculation not in [None,""] and Preprocessing_Imm(A.Immatriculation) == self.Immatriculation and A.Okpoursouscription=="NOK":
                Rate=15
                R="15%: l'immatriculation adverse a été signalée comme souscription NOK voir le dossier "+str(A.id)
                A=A
                break
            else:
                Rate=0
                A=None
        for A in  Liste:
            if self.ImmatriculationAdverse not in [None,""] and Preprocessing_Imm(A.Immatriculation) == self.ImmatriculationAdverse and A.Okpoursouscription=="NOK":
                Rate=15
                R="15%: l'immatriculation principale a été signalée comme souscription NOK voir le dossier "+str(A.id)
                P=A
                break
            else:
                Rate=0
                P=None
        veotest.objects.filter(id=self.id).update(R4=R)   
        return  [Rate,P,A]
    def  Reg5(self):
        Rate=0
        A=None
        R=None
        Liste2=[]
        Liste=[]
        Date_création=datetime.strptime(self.Date_sinistre, "%d/%m/%Y")
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
         

        
        Liste=list(Assistance.objects.all())
        for i in Liste:
            if (len(i.Immatriculation) not in [1,2,3] and self.Immatriculation not in [None,""] and Preprocessing_Imm(i.Immatriculation) == self.Immatriculation) and (i.DateConstat != None or i.DateRemorquage != None) and (i.PhotosConstat !=None or i.PhotosRemorquage != None):
                Liste2.append(i)
        if Liste2!=[]:
            for i in Liste2:
                if i.Intervention == "Remorquage" and i.DateRemorquage != None and i.DateRemorquage != '':
                    DateAssistance=datetime.strptime(i.DateRemorquage, "%d/%m/%Y %H:%M")
                    if  0<=((DateAssistance-Date_création).days)<=5:
                        if DateAssistance.hour<7  or DateAssistance.hour>=20:
                            Rate=10
                            R="10%: La date assistance du dossier: "+str(i.id)+" est après 20h ou avant 7h du matin"
                            A=i
                            break
                elif i.DateConstat != None and i.DateConstat != '':
                    DateAssistance=datetime.strptime(i.DateConstat, "%d/%m/%Y %H:%M")
                    if  0<=((DateAssistance-Date_création).days)<=5:
                        if DateAssistance.hour<7  or DateAssistance.hour>=20:
                            Rate=10
                            R="10%: La date assistance du dossier: "+str(i.id)+" est après 20h ou avant 7h du matin"
                            A=i
                            break
        veotest.objects.filter(id=self.id).update(R5=R)                       
        return [Rate,A]

    def  Reg6(self):
        Rate=0 
        R=None  
        A1=None
        A2=None 
        liste2=[]
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
         

        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)   
        Liste=list(Assistance.objects.all())
        DateAssistance1 = None
        DateAssistance2 = None
        for i in Liste:
            if (len(i.Immatriculation) not in [1,2,3] and len(i.Immatriculation) not in [1,2,3] and self.Immatriculation not in [None,""] and Preprocessing_Imm(i.Immatriculation) == self.Immatriculation) and (i.DateConstat != None or i.DateRemorquage != None) and (i.PhotosConstat !=None or i.PhotosRemorquage != None):
                liste2.append(i)
        for i in  liste2:
            if i.Intervention == "Remorquage" and i.DateRemorquage != None and i.DateRemorquage != '':
                DateAssistance1=datetime.strptime(i.DateRemorquage, "%d/%m/%Y %H:%M")
            elif i.DateConstat != None and i.DateConstat != '':
                    DateAssistance1=datetime.strptime(i.DateConstat, "%d/%m/%Y %H:%M")
           # else:
            #DateAssistance1=None
            for j in liste2:
                if i!=j:
                    if j.Intervention == "Remorquage" and j.DateRemorquage != None and j.DateRemorquage != '':
                                
                        DateAssistance2=datetime.strptime(j.DateRemorquage, "%d/%m/%Y %H:%M")
                        if DateAssistance1 != None and DateAssistance2 != None:
                            if 1<abs((DateAssistance2-DateAssistance1).days)<=90:
                                Rate=5
                                R="5%: les 2 dossiers "+str(j.id)+" et "+str(i.id)+" ont moins de 3 mois de distance"
                                A1=j
                                A2=i
                                break

                    elif j.DateConstat != None and j.DateConstat != '':
                        DateAssistance2=datetime.strptime(j.DateConstat, "%d/%m/%Y %H:%M")
                        if DateAssistance1 != None and DateAssistance2 !=None : 
                            if 1<abs((DateAssistance2-DateAssistance1).days)<=90:
                                Rate=5
                                R="5%: les 2 dossiers "+str(j.id)+" et "+str(i.id)+" ont moins de 3 mois de distance"
                                A1=j
                                A2=i
                                break
        veotest.objects.filter(id=self.id).update(R6=R)                   
        return [Rate,A1,A2]


    def Reg7(self):
        if ((self.Procédure is not None) and ("Souscription" not in self.Procédure)):
            Rate=0
            R=None
            A=None
            P=None
            liste2=[]
            liste1=[]
           
            Liste=list(veotest.objects.all())
            if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
                self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
         

        
            for i in Liste:
                
                if i.Date_sinistre != self.Date_sinistre and (len(i.Immatriculation) not in [1,2,3] and len(i.Immatriculation) not in [1,2,3] and self.Immatriculation not in [None,""] and Preprocessing_Imm(i.Immatriculation) == self.Immatriculation):
                        liste2.append(i)
            date_sinis1=self.Date_sinistre
            for j in liste2:
                date_sinis2=j.Date_sinistre
                if (date_sinis2!=None and date_sinis2!="")and (date_sinis1!=None and date_sinis1!=""):                   
                    diff=inter_dt(date_sinis1, date_sinis2)
                    if ((diff!=None) and (1<diff<=365)) and  j.Statut != "Changement de procédure":
                        
                        Rate=5
                        R="5%: l'immatriculation principale a déjà fait l'objet d'un sinistre il y'a moins de 12 mois " +str(j.Dossier)
                        P=j
                        break
            if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
                self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)       
            for i in Liste:
                
                if i.Date_sinistre != self.Date_sinistre and (len(i.Immatriculation) not in [1,2,3] and self.ImmatriculationAdverse not in [None,""] and Preprocessing_Imm(i.Immatriculation) == self.ImmatriculationAdverse):
                    liste1.append(i)
            date_sinis1=self.Date_sinistre
            for j in liste1:
                date_sinis2=j.Date_sinistre
                if (date_sinis2!=None and date_sinis2!="")and (date_sinis1!=None and date_sinis1!=""):                   
                    diff=inter_dt(date_sinis1, date_sinis2)
                    if ((diff!=None) and (1<diff<=365)) and j.Statut != "Changement de procédure":
                        Rate=5
                        A=j
                        R="5%: l'immatriculation adverse a déjà fait l'objet d'un sinistre il y'a moins de 12 mois "+str(j.Dossier)
                            
                        
                        break
                        
        veotest.objects.filter(id=self.id).update(R7=R)                   
        return  [Rate,P,A]
        
        
    def  Reg9(self):
        R=None
        
        Rate=0
        #self.strtodate()
        DFP=self.Date_validité_fin
        date_sinis=self.Date_sinistre
        if self.Garantie != None:
            if (date_sinis!=None) and (date_sinis!="") and ("tierce" in self.Garantie.lower()):
                if DFP!=None:
                    diff_sous_sinis=inter_dt2(date_sinis,DFP)
                    if diff_sous_sinis!=None  and 0<diff_sous_sinis<=30:
                        Rate=5  
                        R="5%: La  garantie  est Tierce  et il reste moins  d'un mois avant la fin  de  validité  de  contrat: "+self.Date_validité_fin
                else:
                    DFP=None
                    date_sinis=None
        veotest.objects.filter(id=self.id).update(R9=R)   
        return [Rate,DFP,date_sinis]
        
    def  Reg8(self):
        R=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
         

        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        Rate=0
        #self.strtodate()
        
        if (self.ImmatriculationAdverse!=None) and (self.ImmatriculationAdverse!="") and (len(self.ImmatriculationAdverse)>=12):
            
            Rate=10 
            R="10%: La partie adverse est un cyclo: "+self.ImmatriculationAdverse
        if (self.Immatriculation!=None) and (self.Immatriculation!="") and (len(self.Immatriculation)>=12):
            
            Rate=10 
            R="10%: La partie principale est un cyclo: "+self.Immatriculation  
        veotest.objects.filter(id=self.id).update(R8=R)   
        return Rate


    def Reg10(self):
        R=None
        Rate=0
        Doss=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
         
        if self.num_chassis and self.num_chassis != None and len(self.num_chassis) not in [1,2,3]:
            self.num_chassis=net_numch(self.num_chassis)
       
        List=list(veotest.objects.all())

        for  i in List:
            if i.num_chassis != None and len(i.num_chassis) not in [1,2,3]:
                i.num_chassis=net_numch(i.num_chassis)
            

                

                if i.num_chassis != "" and i.num_chassis == self.num_chassis and i.Immatriculation != None and len(i.Immatriculation) not in [1,2,3] and "WW" not in i.Immatriculation and "WW" not in self.Immatriculation and "XXXXXX" not in i.num_chassis and  "aaaaa" not in i.num_chassis and  "xxxxx" not in i.num_chassis:
                    i.Immatriculation=Preprocessing_Imm(i.Immatriculation)
                    if  i.Immatriculation != "" and i.Immatriculation != self.Immatriculation :
                        Rate=30
                        R="ce véhicule a une déclaration avec Immatriculation differente et même numéro de chassis: "+str(i.Dossier)
                        Doss=i
        veotest.objects.filter(id=self.id).update(R10=R) 
        return [Rate,Doss]

    def Reg11(self):
        R=None
        Rate=0
        if self.montant_devis !=  None:
            self.montant_devis=str(self.montant_devis).replace(' Dhs','').replace(',','.').replace(' ','')
            self.montant_devis=str_to_float(self.montant_devis)

            if 18000.00<=self.montant_devis<20000.00 :
                Rate=10
                R="Le montant de  devis est  entre 18000 et  20000: " + str(self.montant_devis)
        veotest.objects.filter(id=self.id).update(R11=R) 
        return Rate
    def Reg12(self):
        R=None
        Rate=0
        Doss=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        List=list(veotest.objects.all())
        for  i in List:
            if i.Immatriculation != None and len(i.Immatriculation) not in [1,2,3]:
                i.Immatriculation=Preprocessing_Imm(i.Immatriculation)
            if i.ImmatriculationAdverse != None and len(i.ImmatriculationAdverse) not in [1,2,3]:
                i.ImmatriculationAdverse=Preprocessing_Imm(i.ImmatriculationAdverse)
            if i.Immatriculation != "" and i.Immatriculation == self.Immatriculation and self.Immatriculation != "" and self.ImmatriculationAdverse != "" and i.ImmatriculationAdverse != "" and i.ImmatriculationAdverse == self.ImmatriculationAdverse and i.Dossier != self.Dossier and i.Statut !="Changement procédure" and self.Statut !="Changement procédure" and i.Date_sinistre != self.Date_sinistre:    
                    
                    Rate=30
                    R="Il y a un autre  sinistre avec  la même Immatriculation Pricipale et Adverse: "+str(i.Dossier)
                    Doss=i
            elif i.Immatriculation != "" and self.Immatriculation != "" and self.ImmatriculationAdverse != "" and  i.Immatriculation == self.ImmatriculationAdverse and i.ImmatriculationAdverse != "" and i.ImmatriculationAdverse == self.Immatriculation and i.Dossier != self.Dossier and i.Statut !="Changement procédure" and self.Statut !="Changement procédure" and i.Date_sinistre != self.Date_sinistre:
                    
                    
                    Rate=30
                    R="Il y a un  autre  sinistre avec  la même Immatriculation Pricipale et Adverse: "+str(i.Dossier)
                    Doss=i
        veotest.objects.filter(id=self.id).update(R12=R) 
        return [Rate,Doss]

    def Reg13(self):
        R=None
        Rate=0
        Doss=None
        if self.Immatriculation != None and len(self.Immatriculation) not in [1,2,3]:
            self.Immatriculation=Preprocessing_Imm(self.Immatriculation)
        if self.ImmatriculationAdverse != None and len(self.ImmatriculationAdverse) not in [1,2,3]:
            self.ImmatriculationAdverse=Preprocessing_Imm(self.ImmatriculationAdverse)
        List=list(veotest.objects.all())

        for  i in List:
            if i.Immatriculation != None and len(i.Immatriculation) not in [1,2,3]:
                i.Immatriculation=Preprocessing_Imm(i.Immatriculation)
            if i.ImmatriculationAdverse != None and len(i.ImmatriculationAdverse) not in [1,2,3]:
                i.ImmatriculationAdverse=Preprocessing_Imm(i.ImmatriculationAdverse)
            if i.Immatriculation != "" and self.Immatriculation != ""   and i.Immatriculation == self.Immatriculation and (i.statutdt_omega == "Doute confirmé" or i.statutdt_omega == "Doute confirmé RMAA" )  :    
                    
                Rate=30
                R="l'immatriculation principale a déjà été impliquée dans un dossier historique doute confirmé : "+str(i.Dossier)
                Doss=i


            elif i.Immatriculation != "" and self.Immatriculation != ""  and self.ImmatriculationAdverse != "" and i.Immatriculation == self.ImmatriculationAdverse and (i.statutdt_omega == "Doute confirmé" or i.statutdt_omega == "Doute confirmé RMAA" )  :    
                    
                Rate=30
                R="l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute confirmé : "+str(i.Dossier)
                Doss=i
            
            elif i.Immatriculation != "" and self.Immatriculation != ""  and i.ImmatriculationAdverse != "" and i.ImmatriculationAdverse == self.Immatriculation and (i.statutdt_omega == "Doute confirmé" or i.statutdt_omega == "Doute confirmé RMAA" )  :    
                    
                Rate=30
                R="l'immatriculation principale a déjà été impliquée dans un dossier historique doute confirmé : "+str(i.Dossier)
                Doss=i

            elif i.Immatriculation != "" and self.Immatriculation != ""  and i.ImmatriculationAdverse != "" and self.ImmatriculationAdverse != ""  and i.ImmatriculationAdverse == self.ImmatriculationAdverse and (i.statutdt_omega == "Doute confirmé" or i.statutdt_omega == "Doute confirmé RMAA" )  :    
                Rate=30
                R="l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute confirmé : "+str(i.Dossier)
                Doss=i
                     
            elif i.Immatriculation != "" and self.Immatriculation != ""  and  self.ImmatriculationAdverse != ""  and i.Immatriculation == self.ImmatriculationAdverse and (i.statutdt_omega != "Doute rejeté" or i.statutdt_omega != "Doute rejeté RMAA")  and i.statutdt_omega != None:

                Rate=15
                R="l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute rejeté : "+str(i.Dossier)
                Doss=i

            elif i.Immatriculation != "" and self.Immatriculation != "" and i.ImmatriculationAdverse != ""  and i.ImmatriculationAdverse == self.Immatriculation and (i.statutdt_omega != "Doute rejeté" or i.statutdt_omega != "Doute rejeté RMAA")  and i.statutdt_omega != None:

                Rate=15
                R="l'immatriculation principale a déjà été impliquée dans un dossier historique doute rejeté : "+str(i.Dossier)
                Doss=i
            
            elif i.Immatriculation != "" and self.Immatriculation != ""  and i.Immatriculation == self.Immatriculation and (i.statutdt_omega != "Doute rejeté" or i.statutdt_omega != "Doute rejeté RMAA")  and i.statutdt_omega != None:

                Rate=15
                R="l'immatriculation principale a déjà été impliquée dans un dossier historique doute rejeté : "+str(i.Dossier)
                Doss=i

            elif i.Immatriculation != "" and self.Immatriculation != "" and i.ImmatriculationAdverse != "" and self.ImmatriculationAdverse != "" and i.ImmatriculationAdverse == self.ImmatriculationAdverse and (i.statutdt_omega != "Doute rejeté" or i.statutdt_omega != "Doute rejeté RMAA")  and i.statutdt_omega != None:

                Rate=15
                R="l'immatriculation Adverse a déjà été impliquée dans un dossier historique doute rejeté : "+str(i.Dossier)
                Doss=i

            
            veotest.objects.filter(id=self.id).update(R13=R) 
            return [Rate,Doss]


    def Reg14(self):
        R=None
        Rate=0
        if (self.statutdt_omega == "Dossier initié" or self.statutdt_omega == "Dossier initié RMAA" or self.statutdt_omega == "Doute créé" or self.statutdt_omega == "Dossier envoyé"  or self.statutdt_omega == "Affecté expert" or self.statutdt_omega == "Retour expert" or self.statutdt_omega == "Attente photos avant")  :    
            Rate=15
            R="Ce sinistre est en instruction"
        veotest.objects.filter(id=self.id).update(R14=R) 
        return Rate

        
    


        
    
