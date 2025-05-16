import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px

# Cargar dataset optimizado
df = pd.read_pickle("resultado_modelo_2023.pkl")

# Crear columnas de fecha adicionales
df['Año'] = df['Fecha'].dt.year
df['Mes'] = df['Fecha'].dt.month
df['Dia'] = df['Fecha'].dt.day

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        html.Img(src="/assets/uniandes_logo.png", style={"height": "90px"}),
        html.H1("DETECCIÓN DE OUTLIERS EN EL CONSUMO DE GAS", style={"margin": "0 auto", "fontWeight": "bold", "textAlign": "center"}),
        html.Img(src="/assets/contugas_logo.png", style={"height": "90px"})
    ], style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "backgroundColor": "#f8f9fa",
        "padding": "10px 30px",
        "borderBottom": "1px solid #ccc"
    }),

    html.Div(id="indicadores", style={"display": "flex", "justifyContent": "space-around", "padding": "30px"}),

    html.Div([
        dcc.Graph(id='grafico_comparacion', style={"height": "800px"})
    ], style={"padding": "0px 30px"}),

    html.Div([
        html.Div([
            html.Label("📅 Rango de fechas", style={"fontWeight": "bold"}),
            dcc.DatePickerRange(
                id='rango_fechas',
                start_date=df['Fecha'].min(),
                end_date=df['Fecha'].max(),
                display_format='DD/MM/YYYY'
            )
        ], style={"marginRight": "40px"}),

        html.Div([
            html.Label("👤 Cliente", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id='filtro_cliente',
                options=[{"label": c, "value": c} for c in df['Numero_Cliente'].unique()],
                value=None,
                placeholder="Todos"
            )
        ], style={"minWidth": "300px"})
    ], style={"display": "flex", "gap": "40px", "padding": "20px 30px"}),

    html.Div([
        dash_table.DataTable(
            id='tabla_detalle',
            columns=[
                {"name": "Fecha", "id": "Fecha"},
                {"name": "Volumen observado", "id": "Volumen"},
                {"name": "Volumen predicho", "id": "Volumen_Predicho"},
                {"name": "Error", "id": "Error"},
                {"name": "Tipo", "id": "Tipo"},
            ],
            style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
            style_data={"backgroundColor": "#ffffff", "color": "#000000"},
            style_table={"border": "1px solid #ccc", "overflowX": "auto"},
            style_cell={"textAlign": "center"},
            page_size=10
        )
    ], style={"padding": "0px 30px 30px 30px"})
])

@app.callback(
    [Output("grafico_comparacion", "figure"),
     Output("tabla_detalle", "data"),
     Output("indicadores", "children")],
    [Input("rango_fechas", "start_date"),
     Input("rango_fechas", "end_date"),
     Input("filtro_cliente", "value")]
)
def actualizar_vista(start_date, end_date, cliente):
    df_filtrado = df[(df['Fecha'] >= pd.to_datetime(start_date)) & (df['Fecha'] <= pd.to_datetime(end_date))]
    if cliente:
        df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen_Predicho'], mode='lines+markers', name='Valores predichos'))
    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen'], mode='markers', name='Error', marker=dict(color='red')))

    fig.update_layout(title='📈 Comparación de consumo de gas', xaxis_title='Comparación de consumo', yaxis_title='Volumen (m3)', template='plotly_white')

    tabla_data = df_filtrado[['Fecha', 'Volumen', 'Volumen_Predicho', 'Error', 'Tipo']].copy()
    tabla_data['Fecha'] = tabla_data['Fecha'].dt.strftime('%d/%m/%Y')

    tarjetas = [
        html.Div([html.H3(f"{df_filtrado['Numero_Cliente'].nunique()}", style={"margin": "0", "color": "#007bff"}), html.P("Clientes")],
                 style={"backgroundColor": "#ffffff", "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "padding": "20px", "textAlign": "center", "width": "30%"}),
        html.Div([html.H3(f"{df_filtrado[df_filtrado['Tipo'] != 'Sin alerta'].shape[0]}", style={"margin": "0", "color": "#dc3545"}), html.P("Outliers")],
                 style={"backgroundColor": "#ffffff", "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "padding": "20px", "textAlign": "center", "width": "30%"}),
        html.Div([html.H3(f"{df_filtrado[df_filtrado['Tipo'] == 'Crítica'].shape[0]}", style={"margin": "0", "color": "#ffc107"}), html.P("Alarmas críticas")],
                 style={"backgroundColor": "#ffffff", "borderRadius": "10px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "padding": "20px", "textAlign": "center", "width": "30%"})
    ]

    return fig, tabla_data.to_dict('records'), tarjetas

if __name__ == '__main__':
    app.run_server(debug=True)
