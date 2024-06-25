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