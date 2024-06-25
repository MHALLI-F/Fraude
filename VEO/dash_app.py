import dash
from dash import html, dcc
import plotly.express as px
from .data import get_veoservices_for_dash
from flask_cors import CORS

# Création de l'application 
app = dash.Dash(__name__, url_base_pathname='/dashboard/')
CORS(app.server)

@app.server.after_request
def add_header(response):
    response.headers['Content-Security-Policy'] = "frame-ancestors http://92.222.221.200/"
    return response

# df_veoservices est le DataFrame retourné par get_veoservices_for_dash()
df_veoservices = get_veoservices_for_dash()

# Création du graphique barre
fig_veoservices = px.bar(df_veoservices, 
                         x='Procédure', 
                         y=['doute_general', 'doute_confirme', 'doute_rejete'],
                         title="Doutes par Procédure",
                         labels={'value': 'Nombre de Dossiers', 'variable': 'Catégorie'},
                         barmode='group')
#print(fig_veoservices)
# Configuration de l'application Dash pour afficher le graphique
app.layout = html.Div([
    html.H1('Tableau de bord VeoSmart'),
    dcc.Graph(id='veoservices-graph', figure=fig_veoservices)
])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=9009)