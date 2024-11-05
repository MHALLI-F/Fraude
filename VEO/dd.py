@login_required
def dossiersAtrait(request):
    NBD = nbrDAT()  
    NBDT = nbrDT() 

    list_inst = Veoservices.objects.filter(Statut="Dossier en instruction", Dossier__contains="D")
    
  
    list_Veo_recente = Veoservices.objects.annotate(
        clean_rate=Coalesce(Cast('RateFraude', FloatField()), Value(0.0))
    ).filter(
        (Q(statutdoute="Non traité") | Q(statutdoute="Attente photos Avant", Photos_Avant__isnull=False)) &
        ~Q(Statut="Changement de procédure") &
        ~Q(clean_rate__in=[0.0, 5.0]) 
    ).order_by('-clean_rate')  

    paginator = Paginator(list_Veo_recente, 9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)

    context = {
        "SupUse": SupUse(request), 
        "list_Veo_recente": veopg,
        "NBDossiers": NBD,
        "NBDT": NBDT,
        "list_inst": list_inst
    }

    return render(request, "dossieratrait.html", context)
    ######################################################
@login_required
def dossiersAtrait(request):
    NBD=nbrDAT()
    NBDT=nbrDT()
    list_Veo_recente=[]
    list_inst=[]
    list_Veoservices=DosAff()
    list_Veoservicesall= Veoservices.objects.all()
    for i in list_Veoservicesall:
        if i.Statut =="Dossier en instruction" and "D" in i.Dossier:
            list_inst.append(i)
    for i in list_Veoservices:
        
        if (i.statutdoute=="Non traité" and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) or (i.statutdoute=="Attente photos Avant" and i.Photos_Avant!="" and i.Photos_Avant!=None and i.Statut!="Changement de procédure" and i.RateFraude not in [0,'0.0',None,'5.0','10.0']) :
            i.RateFraude = str_to_float(i.RateFraude)
            list_Veo_recente.append(i)


    list_Veo_recente.sort(key=lambda r: r.RateFraude,reverse=True)
    paginator = Paginator(list_Veo_recente,9)
    page = request.GET.get('page')
    veopg = paginator.get_page(page)
   # veopg.sort(key=lambda r: r.RateFraude,reverse=True)
   
    context={"SupUse":SupUse(request),"list_Veo_recente": veopg,"NBDossiers":NBD,"NBDT":NBDT ,"list_inst": list_inst}
    return render(request,"dossieratrait.html",context) 



<form action="{% url 'filter_dossiertrait' %}" method="get" style="display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 10px 0;">
    <div class="form-group" style="margin-right: 20px; flex: 1; display: flex; align-items: center;">
        <div style="white-space: nowrap; margin-right: 10px;">Date de création :</div>
        <div class="input-group" style="flex-grow: 1; display: flex; align-items: center;">
            <input type="date" id="fixed_date" name="fixed_date" class="form-control" style="flex-grow: 1;">
            <button type="button" class="btn btn-light" onclick="clearField('fixed_date')" style="width: 40px; margin-left: 5px;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
    <div class="form-group" style="flex: 1; display: flex; align-items: center;">
        <div style="white-space: nowrap; margin-right: 10px;">Statut:</div>
        <div class="input-group" style="flex-grow: 1; display: flex; align-items: center;">
            <select id="statut" name="statut" class="form-control" style="flex-grow: 1;">
                <option value="">Sélectionner un statut</option>
                 <option value="">Sélectionner un statut</option>
                <option value="">Sélectionner un statut</option>
                <option value="">Sélectionner un statut</option>
                <option value="Dossier créé">Dossier créé</option>
                <option value="Dossier envoyé">Dossier envoyé</option>
                <option value="Rdv replanifié">Rdv replanifié</option>
                <option value="CDC envoyé au garage">CDC envoyé au garage</option>
                <option value="Photos Avant">Photos Avant</option>
                <option value="Offre communiquée">Offre communiquée</option>
                <option value="Devis envoyé par le garage">Devis envoyé par le garage</option>
                <option value="Instance Accord compagnie">Instance Accord compagnie</option>
                <option value="Instance Accord Expert2">Instance Accord Expert2</option>
                <option value="Accord à modifier">Accord à modifier</option>
                <option value="Accord à envoyer">Accord à envoyer</option>
                <option value="Devis validé">Devis validé</option>
                <option value="Demande 2e accord">Demande 2e accord</option>
                <option value="Attente facture">Attente facture</option>
                <option value="Instance FFT/rapport">Instance FFT/rapport</option>
                <option value="Instance RDV Client ">Instance RDV Client</option>
                <option value="Instance publication rapport">Instance publication rapport</option>
                <option value="Dossier complété">Dossier complété</option>
                <option value="Dossier réglé">Dossier réglé</option>
                <option value="Dossier sans suite">Dossier sans suite</option>
                <option value="Dossier sans suite après expertise">Dossier sans suite après expertise</option>
                <option value="Annulé par l'expert">Annulé par l'expert</option>
                <option value="Dossier traité en Hifad">Dossier traité en Hifad</option>
                <option value="Rapport rejeté">Rapport rejeté</option>
                <option value="Changement procédure">Changement procédure</option>
                <option value="Dossier en instruction">Dossier en instruction</option>
                <option value="Dossier rejeté">Dossier rejeté</option>
            </select>
            <button type="button" class="btn btn-light" onclick="clearField('statut')" style="width: 40px; margin-left: 5px;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
    <button type="submit" class="btn btn-primary" style="white-space: nowrap;">Filtrer</button>
</form>
----------------------------
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

        # Calcul des totaux et moyennes
        if total_dossiers > 0:
            total_traite = Veoservices.objects.filter(statutdoute__in=['Doute confirmé', 'Doute rejeté']).count()
            total_doute_confirme = Veoservices.objects.filter(statutdoute='Doute confirmé').count()
            
            rate_fraude_values = Veoservices.objects.values_list('RateFraude', flat=True).exclude(RateFraude=None)
            if rate_fraude_values:
                total_rate_fraude = sum(rate_fraude_values)
                moyenne_doute = total_rate_fraude / len(rate_fraude_values)
            else:
                moyenne_doute = 0

        # Définir le début de la journée il y a cinq jours
        five_days_ago_start_of_day = datetime.datetime.now() - datetime.timedelta(days=5)

        # Conversion en datetime dans la requête Django
        list_veo_recente = Veoservices.objects.filter(
            date_creation_nv__gte=five_days_ago_start_of_day
        ).exclude(
            Statut="Changement de procédure",
        RateFraude__in=[None,0,0.0, 5.0, 10.0]
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


