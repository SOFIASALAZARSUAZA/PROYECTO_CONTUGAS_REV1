import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.graph_objects as go

# Cargar datos
df = pd.read_pickle("resultado_modelo_2023.pkl")
df['Año'] = df['Fecha'].dt.year

# Clasificación del tipo de alerta
def clasificar_alerta(e):
    if e > 40:
        return "🔴 Crítica"
    elif e > 20:
        return "🟠 Grave"
    elif e > 10:
        return "🟡 Leve"
    else:
        return "🟢 Sin alerta"

if 'Error' not in df.columns:
    df['Error'] = np.abs(df['Volumen'] - df['Volumen_Predicho'])
if 'Tipo' not in df.columns:
    df['Tipo'] = df['Error'].apply(clasificar_alerta)

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        html.Img(src="/assets/uniandes_logo.png", style={"height": "60px"}),
        html.Img(src="/assets/contugas_logo.png", style={"height": "60px", "float": "right"})
    ], style={"display": "flex", "justify-content": "space-between", "padding": "10px 30px"}),

    html.H2("DETECCIÓN DE OUTLIERS EN EL CONSUMO DE GAS", style={"textAlign": "center"}),

    html.Div(id="tarjetas-indicadores", style={"display": "flex", "justifyContent": "space-around", "padding": "10px"}),

    html.Div([
        dcc.Graph(id='grafico_comparacion')
    ], style={"padding": "0px 30px"}),

    html.Div([
        html.Div([
            html.Label("📅 Rango de fechas"),
            dcc.DatePickerRange(
                id='rango_fechas',
                start_date=df['Fecha'].min(),
                end_date=df['Fecha'].max(),
                display_format='DD/MM/YYYY'
            )
        ], style={"display": "inline-block", "marginRight": "40px"}),

        html.Div([
            html.Label("👤 Cliente"),
            dcc.Dropdown(
                id='filtro_cliente',
                options=[{"label": c, "value": c} for c in sorted(df['Numero_Cliente'].unique())],
                value=None,
                placeholder="Todos",
                style={"width": "300px"}
            )
        ], style={"display": "inline-block"})
    ], style={"padding": "20px 30px"}),

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
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "fontSize": 14},
            page_size=10
        )
    ], style={"padding": "0px 30px 30px 30px"})
])

@app.callback(
    [Output("grafico_comparacion", "figure"),
     Output("tabla_detalle", "data"),
     Output("tarjetas-indicadores", "children")],
    [Input("rango_fechas", "start_date"),
     Input("rango_fechas", "end_date"),
     Input("filtro_cliente", "value")]
)
def actualizar_vista(start_date, end_date, cliente):
    df_filtrado = df[(df['Fecha'] >= pd.to_datetime(start_date)) & (df['Fecha'] <= pd.to_datetime(end_date))]
    if cliente:
        df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]

    fig = go.Figure()
    yref = df_filtrado['Volumen_Predicho']

    for signo in [1, -1]:
        fig.add_trace(go.Scatter(
            x=df_filtrado['Fecha'],
            y=yref * (1 + signo * 0.30),
            mode="lines",
            line=dict(color="rgba(0,0,255,0.3)", dash="dot"),
            showlegend=False
        ))

    niveles = [
        {"inf": 0.30, "sup": 0.60, "color": "rgba(200, 220, 255, 0.3)"},
        {"inf": 0.60, "sup": 0.80, "color": "rgba(255, 230, 180, 0.4)"},
        {"inf": 0.80, "sup": 1.00, "color": "rgba(255, 150, 150, 0.4)"},
    ]

    for banda in niveles:
        for signo in [1, -1]:
            y0 = yref * (1 + signo * banda["inf"])
            y1 = yref * (1 + signo * banda["sup"])
            fig.add_trace(go.Scatter(
                x=pd.concat([df_filtrado["Fecha"], df_filtrado["Fecha"][::-1]]),
                y=pd.concat([y0, y1[::-1]]),
                fill="toself",
                fillcolor=banda["color"],
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=False
            ))

    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen_Predicho'], mode='lines+markers', name='Valores predichos'))
    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen'], mode='markers', name='Error', marker=dict(color='red')))

    fig.update_layout(title='Comparación de consumo de gas con bandas de alerta', xaxis_title='Fecha', yaxis_title='Volumen (m3)', template='plotly_white', height=600)

    tabla_data = df_filtrado[['Fecha', 'Volumen', 'Volumen_Predicho', 'Error', 'Tipo']].copy()
    tabla_data['Fecha'] = tabla_data['Fecha'].dt.strftime('%d/%m/%Y')

    tarjetas = [
        html.Div([html.H3(f"{df_filtrado['Numero_Cliente'].nunique()}"), html.P("Clientes")], className="card"),
        html.Div([html.H3(f"{df_filtrado[df_filtrado['Tipo'] != '🟢 Sin alerta'].shape[0]}", style={"color": "red"}), html.P("Outliers")], className="card"),
        html.Div([html.H3(f"{df_filtrado[df_filtrado['Tipo'].str.contains('🔴')].shape[0]}", style={"color": "orange"}), html.P("Alarmas críticas")], className="card"),
    ]

    return fig, tabla_data.to_dict('records'), tarjetas

if __name__ == '__main__':
    app.run_server(debug=True)
