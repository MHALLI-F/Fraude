"""VEOsmart URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include
from VEO.views import *

from django_plotly_dash.views import add_to_session
from VEO import views  



from accounts.views import login_view ,deconnexion
#pour que  les  images  s'affiches
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [

# API Urls
    path('django_plotly_dash/', include('django_plotly_dash.urls')),

    path('get_dossier/<str:Dossier>/',get_veoservices,name="get_veoservices"),
    path('get_dossiers/',get_dossiers,name="get_dossiers"),
    path('getVeos/',getVeos,name="getVeos"),
    path('extraction_traitement/',extraction_traitement,name="extraction_traitement"),

    path('admin/', admin.site.urls),   
    path('home/', inis,name="inis"),
    path('details/<str:Dossier>/',details,name="details"),
    path('filtre/',filtre,name="filtre"),
    path('send-test-email/', send_test_email, name='send_test_email'),

     #path('statutdoute/',statutdoute,name="statutdoute"),
    path('filtre_regT/',filtre_regT,name="filtre_regT"),
    path('filtre_regAT/',filtre_regAT,name="filtre_regAT"),
    path('filtre_reg/',filtre_reg,name="filtre_reg"),
    path('dt/',dossiersAtrait,name="dossiersAtrait"),
    path('dtraités/',dossierstrait,name="dossierstrait1"),
    path('filterDos/',filterDos,name="filterDos"),
    path('filterDosAT/',filterDosAT,name="filterDosAT"),
    path('filterDosT/',filterDosT,name="filterDosT"),
    path('dossieratrait/', filter_by_rate_fraude, name='filter_by_rate_fraude'),

    path('filter_veoservices_by_date_and_status/',filter_veoservices_by_date_and_status,name="filter_veoservices_by_date_and_status"),
    path('filter_veoservices_by_date_and_statusAT/',filter_veoservices_by_date_and_statusAT,name="filter_veoservices_by_date_and_statusAT"),
    path('filter_veoservices_by_date_and_statusT/',filter_veoservices_by_date_and_statusT,name="filter_veoservices_by_date_and_statusT"),


    path('filter/home/', lambda request: filter_veoservices_by_date_and_status(request, 'home.html'), name='filter_home'),
    path('filter/dossieratrait/', lambda request: filter_veoservices_by_date_and_status(request, 'dossieratrait.html'), name='filter_dossieratrait'),
    path('filter/dossiertrait/', lambda request: filter_veoservices_by_date_and_status(request, 'dossiertrait.html'), name='filter_dossiertrait'),

    path('filter/home/', filter_veoservices_by_date_and_status, name='filter_home'),
    path('filter/dossieratrait/', filter_veoservices_by_date_and_statusAT, name='filter_dossieratrait'),
    path('filter/dossiertrait/', filter_veoservices_by_date_and_statusT, name='filter_dossiertrait'),


 
    path('home/login/', login_view),
    path('login/', login_view),
    path('logout/', deconnexion),
    path('observation/',observation,name="observation"),

    path('TrDos/',TrDos,name="TrDos"),
    path('TrImmat/',TrImmat,name="TrImmat"),
    path('TrDsin/',TrDsin,name="TrDsin"),
    path('TrDcr/',TrDcr,name="TrDcr"),
    path('TrType/',TrType,name="TrType"),
    path('TrStat/',TrStat,name="TrStat"),
    path('TrExp/',TrExp,name="TrExp"),
    path('TrIAdv/',TrIAdv,name="TrIAdv"),
    path('TrRF/',TrRF,name="TrRF"),
    path('TrStatDoute/',TrStatDoute,name="TrStatDoute"),
    path('Trobs/',Trobs,name="Trobs"),
    path('TrDosI/',TrDosI,name="TrDosI"),
    path('TrImmatI/',TrImmatI,name="TrImmatI"),
    path('TrDsinI/',TrDsinI,name="TrDsinI"),
    path('TrDcrI/',TrDcrI,name="TrDcrI"),
    path('TrTypeI/',TrTypeI,name="TrTypeI"),
    path('TrStatI/',TrStatI,name="TrStatI"),
    path('TrExpI/',TrExpI,name="TrExpI"),
    path('TrIAdvI/',TrIAdvI,name="TrIAdvI"),
    path('TrRFI/',TrRFI,name="TrRFI"),
    path('TrStatDouteI/',TrStatDouteI,name="TrStatDouteI"),
    path('TrobsI/',TrobsI,name="TrobsI"),
    
    path('TrDosT/',TrDosT,name="TrDosT"),
    path('TrImmatT/',TrImmatT,name="TrImmatT"),
    path('TrDsinT/',TrDsinT,name="TrDsinT"),
    path('TrDcrT/',TrDcrT,name="TrDcrT"),
    path('TrTypeT/',TrTypeT,name="TrTypeT"),
    path('TrStatT/',TrStatT,name="TrStatT"),
    path('TrExpT/',TrExpT,name="TrExpT"),
    path('TrIAdvT/',TrIAdvT,name="TrIAdvT"),
    path('TrRFT/',TrRFT,name="TrRFT"),
    path('TrStatDouteT/',TrStatDouteT,name="TrStatDouteT"),
    path('TrobsT/',TrobsT,name="TrobsT"),
    path('TrDosIT/',TrDosIT,name="TrDosIT"),
    path('TrImmatIT/',TrImmatIT,name="TrImmatIT"),
    path('TrDsinIT/',TrDsinIT,name="TrDsinIT"),
    path('TrDcrIT/',TrDcrIT,name="TrDcrIT"),
    path('TrTypeIT/',TrTypeIT,name="TrTypeIT"),
    path('TrStatIT/',TrStatT,name="TrStatIT"),
    path('TrExpIT/',TrExpIT,name="TrExpIT"),
    path('TrIAdvIT/',TrIAdvIT,name="TrIAdvIT"),
    path('TrRFIT/',TrRFIT,name="TrRFIT"),
    path('TrStatDouteIT/',TrStatDouteIT,name="TrStatDouteIT"),
    path('TrobsIT/',TrobsIT,name="TrobsIT"),


    path('TrDosAT/',TrDosAT,name="TrDosAT"),
    path('TrImmatAT/',TrImmatAT,name="TrImmatAT"),
    path('TrDsinAT/',TrDsinAT,name="TrDsinAT"),
    path('TrDcrAT/',TrDcrAT,name="TrDcrAT"),
    path('TrTypeAT/',TrTypeAT,name="TrTypeAT"),
    path('TrStatAT/',TrStatAT,name="TrStatAT"),
    path('TrExpAT/',TrExpAT,name="TrExpAT"),
    path('TrIAdvAT/',TrIAdvAT,name="TrIAdvAT"),
    path('TrRFAT/',TrRFAT,name="TrRFAT"),
    path('TrStatDouteAT/',TrStatDouteAT,name="TrStatDouteAT"),
    path('TrobsAT/',TrobsAT,name="TrobsAT"),
    path('TrDosIAT/',TrDosIAT,name="TrDosIAT"),
    path('TrImmatIAT/',TrImmatIAT,name="TrImmatIAT"),
    path('TrDsinIAT/',TrDsinIAT,name="TrDsinIAT"),
    path('TrDcrIAT/',TrDcrIAT,name="TrDcrIAT"),
    path('TrTypeIAT/',TrTypeIAT,name="TrTypeIAT"),
    path('TrStatIAT/',TrStatIAT,name="TrStatIAT"),
    path('TrExpIAT/',TrExpIAT,name="TrExpIAT"),
    path('TrIAdvIAT/',TrIAdvIAT,name="TrIAdvIAT"),
    path('TrRFIAT/',TrRFIAT,name="TrRFIAT"),
    path('TrStatDouteIAT/',TrStatDouteIAT,name="TrStatDouteIAT"),
    path('TrobsIAT/',TrobsIAT,name="TrobsIAT"),
    path('TrdateT/',TrdateT,name="TrdateT"),
    path('TrdateIT/',TrdateIT,name="TrdateIT"),
    #path('', include("django.contrib.auth.urls")),
    path('', login_view),
   # path('apis/', include("apis.urls"))
   ###############################################################################

   ####################       Espace  recette        #############################

   ###############################################################################
    path('template/', template,name="template"),
    path('home_test/', test_inis,name="test_inis"),
    path('details_test/<str:Dossier>/',test_details,name="test_details"),
    path('filtre_test/',test_filtre,name="test_filtre"),

     #path('statutdoute/',statutdoute,name="statutdoute"),
    path('test_filtre_regT/',test_filtre_regT,name="test_filtre_regT"),
    path('test_filtre_regAT/',test_filtre_regAT,name="test_filtre_regAT"),
    path('test_filtre_reg/',test_filtre_reg,name="test_filtre_reg"),
    path('dt_test/',test_dossiersAtrait,name="test_dossiersAtrait"),
    path('dtraités_test/',test_dossierstrait,name="test_dossierstrait"),
    path('filterDos_test/',test_filterDos,name="test_filterDos"),
    path('filterDosAT_test/',test_filterDosAT,name="test_filterDosAT"),
    path('filterDosT_test/',test_filterDosT,name="test_filterDosT"),
    path('observation_test/',test_observation,name="test_observation"),

# **************   Tri dossiers Home "Espace Recette"     ***************#

    path('TrDos_test/',test_TrDos,name="test_TrDos"),
    path('TrImmat_test/',test_TrImmat,name="test_TrImmat"),
    path('TrDsin_test/',test_TrDsin,name="test_TrDsin"),
    path('TrDcr_test/',test_TrDcr,name="test_TrDcr"),
    path('TrType_test/',test_TrType,name="test_TrType"),
    path('TrStat_test/',test_TrStat,name="test_TrStat"),
    path('TrExp_test/',test_TrExp,name="test_TrExp"),
    path('TrIAdv_test/',test_TrIAdv,name="test_TrIAdv"),
    path('TrRF_test/',test_TrRF,name="test_TrRF"),
    path('TrStatDoute_test/',test_TrStatDoute,name="test_TrStatDoute"),
    path('Trobs_test/',test_Trobs,name="test_Trobs"),
    path('TrDosI_test/',test_TrDosI,name="test_TrDosI"),
    path('TrImmatI_test/',test_TrImmatI,name="test_TrImmatI"),
    path('TrDsinI_test/',test_TrDsinI,name="test_TrDsinI"),
    path('TrDcrI_test/',test_TrDcrI,name="test_TrDcrI"),
    path('TrTypeI_test/',test_TrTypeI,name="test_TrTypeI"),
    path('TrStatI_test/',test_TrStatI,name="test_TrStatI"),
    path('TrExpI_test/',test_TrExpI,name="test_TrExpI"),
    path('TrIAdvI_test/',test_TrIAdvI,name="test_TrIAdvI"),
    path('TrRFI_test/',test_TrRFI,name="test_TrRFI"),
    path('TrStatDouteI_test/',test_TrStatDouteI,name="test_TrStatDouteI"),
    path('TrobsI_test/',test_TrobsI,name="test_TrobsI"),
    
    # **************   Tri dossiers traités "Espace Recette"     ***************#


    path('TrDosT_test/',test_TrDosT,name="test_TrDosT"),
    path('TrImmatT_test/',test_TrImmatT,name="test_TrImmatT"),
    path('TrDsinT_test/',test_TrDsinT,name="test_TrDsinT"),
    path('TrDcrT_test/',test_TrDcrT,name="test_TrDcrT"),
    path('TrTypeT_test/',test_TrTypeT,name="test_TrTypeT"),
    path('TrStatT_test/',test_TrStatT,name="test_TrStatT"),
    path('TrExpT_test/',test_TrExpT,name="test_TrExpT"),
    path('TrIAdvT_test/',test_TrIAdvT,name="test_TrIAdvT"),
    path('TrRFT_test/',test_TrRFT,name="test_TrRFT"),
    path('TrStatDouteT_test/',test_TrStatDouteT,name="test_TrStatDouteT"),
    path('TrobsT_test/',test_TrobsT,name="test_TrobsT"),
    path('TrDosIT_test/',test_TrDosIT,name="test_TrDosIT"),
    path('TrImmatIT_test/',test_TrImmatIT,name="test_TrImmatIT"),
    path('TrDsinIT_test/',test_TrDsinIT,name="test_TrDsinIT"),
    path('TrDcrIT_test/',test_TrDcrIT,name="test_TrDcrIT"),
    path('TrTypeIT_test/',test_TrTypeIT,name="test_TrTypeIT"),
    path('TrStatIT_test/',test_TrStatT,name="test_TrStatIT"),
    path('TrExpIT_test/',test_TrExpIT,name="test_TrExpIT"),
    path('TrIAdvIT_test/',test_TrIAdvIT,name="test_TrIAdvIT"),
    path('TrRFIT_test/',test_TrRFIT,name="test_TrRFIT"),
    path('TrStatDouteIT_test/',test_TrStatDouteIT,name="test_TrStatDouteIT"),
    path('TrobsIT_test/',test_TrobsIT,name="test_TrobsIT"),


# **************   Tri dossiers à traiter "Espace Recette"     ***************#

    path('TrDosAT_test/',test_TrDosAT,name="test_TrDosAT"),
    path('TrImmatAT_test/',test_TrImmatAT,name="test_TrImmatAT"),
    path('TrDsinAT_test/',test_TrDsinAT,name="test_TrDsinAT"),
    path('TrDcrAT_test/',test_TrDcrAT,name="test_TrDcrAT"),
    path('TrTypeAT_test/',test_TrTypeAT,name="test_TrTypeAT"),
    path('TrStatAT_test/',test_TrStatAT,name="test_TrStatAT"),
    path('TrExpAT_test/',test_TrExpAT,name="test_TrExpAT"),
    path('TrIAdvAT_test/',test_TrIAdvAT,name="test_TrIAdvAT"),
    path('TrRFAT_test/',test_TrRFAT,name="test_TrRFAT"),
    path('TrStatDouteAT_test/',test_TrStatDouteAT,name="test_TrStatDouteAT"),
    path('TrobsAT_test/',test_TrobsAT,name="test_TrobsAT"),
    path('TrDosIAT_test/',test_TrDosIAT,name="test_TrDosIAT"),
    path('TrImmatIAT_test/',test_TrImmatIAT,name="test_TrImmatIAT"),
    path('TrDsinIAT_test/',test_TrDsinIAT,name="test_TrDsinIAT"),
    path('TrDcrIAT_test/',test_TrDcrIAT,name="test_TrDcrIAT"),
    path('TrTypeIAT_test/',test_TrTypeIAT,name="test_TrTypeIAT"),
    path('TrStatIAT_test/',test_TrStatIAT,name="test_TrStatIAT"),
    path('TrExpIAT_test/',test_TrExpIAT,name="test_TrExpIAT"),
    path('TrIAdvIAT_test/',test_TrIAdvIAT,name="test_TrIAdvIAT"),
    path('TrRFIAT_test/',test_TrRFIAT,name="test_TrRFIAT"),
    path('TrStatDouteIAT_test/',test_TrStatDouteIAT,name="test_TrStatDouteIAT"),
    path('TrobsIAT_test/',test_TrobsIAT,name="test_TrobsIAT"),
    path('TrdateT_test/',test_TrdateT,name="test_TrdateT"),
    path('TrdateIT_test/',test_TrdateIT,name="test_TrdateIT"),

    path('chart/',chart,name="chart"),
    path('dashboard/', dashboard_data, name='dashboard_data'),
    path('test-fraud-alert/',test_fraud_alert, name='test_fraud_alert'),


  
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#+static   pour  les images
