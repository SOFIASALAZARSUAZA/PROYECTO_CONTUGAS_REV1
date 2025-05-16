# app.py
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px

# Cargar datos del modelo final
df = pd.read_excel("resultado_modelo_4.xlsx")
df['Fecha'] = pd.to_datetime(df['Fecha'])
df['Año'] = df['Fecha'].dt.year
df['Mes'] = df['Fecha'].dt.month
df['Dia'] = df['Fecha'].dt.day

# Clasificación de alertas por error
def clasificar_alerta(e):
    if e > 40:
        return "Crítica"
    elif e > 20:
        return "Grave"
    elif e > 10:
        return "Leve"
    else:
        return "Sin alerta"

df['Error'] = np.abs(df['Volumen'] - df['Volumen_Predicho'])
df['Tipo'] = df['Error'].apply(clasificar_alerta)

app = Dash(__name__)
server = app.server  # Railway usa esto

app.layout = html.Div([
    html.H2("Detección de Outliers en el Consumo de Gas", style={"textAlign": "center"}),

    html.Div([
        html.Div([html.H3(f"{df['Numero_Cliente'].nunique()}"), html.P("Clientes")]),
        html.Div([html.H3(f"{df[df['Tipo'] != 'Sin alerta'].shape[0]}"), html.P("Outliers")]),
        html.Div([html.H3(f"{df[df['Tipo'] == 'Crítica'].shape[0]}"), html.P("Alarmas Críticas")]),
    ], style={"display": "flex", "justifyContent": "space-around"}),

    dcc.Graph(id="grafico_comparacion"),

    html.Div([
        dcc.DatePickerRange(
            id='rango_fechas',
            start_date=df['Fecha'].min(),
            end_date=df['Fecha'].max(),
            display_format='DD/MM/YYYY'
        ),
        dcc.Dropdown(
            id='filtro_cliente',
            options=[{"label]()
