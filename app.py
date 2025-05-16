import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.graph_objects as go

# Cargar datos
from datetime import datetime

df = pd.read_pickle("resultado_modelo_2023.pkl")
df['Año'] = df['Fecha'].dt.year

# Clasificación del tipo de alerta según el error
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
        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Escudo_Uniandes.svg/1200px-Escudo_Uniandes.svg.png", style={"height": "60px"}),
        html.Img(src="https://www.contugas.com.pe/wp-content/uploads/2021/03/logo-contugas.png", style={"height": "60px", "float": "right"})
    ], style={"display": "flex", "justify-content": "space-between", "padding": "10px 30px"}),

    html.H2("DETECCIÓN DE OUTLIERS EN EL CONSUMO DE GAS", style={"textAlign": "center", "marginTop": "10px"}),

    html.Div([
        html.Div([html.H3(f"{df['Numero_Cliente'].nunique()}", style={"marginBottom": "0px"}), html.P("Clientes")], className="card"),
        html.Div([html.H3(f"{df[df['Tipo'] != '🟢 Sin alerta'].shape[0]}", style={"marginBottom": "0px", "color": "red"}), html.P("Outliers")], className="card"),
        html.Div([html.H3(f"{df[df['Tipo'].str.contains('🔴')].shape[0]}", style={"marginBottom": "0px", "color": "orange"}), html.P("Alarmas críticas")], className="card"),
    ], style={"display": "flex", "justifyContent": "space-around", "padding": "20px"}),

    html.Div([
        dcc.Graph(id='grafico_comparacion')
    ], style={"padding": "0px 30px"}),

    html.Div([
        html.Div([
            html.Label("Rango de fechas"),
            dcc.DatePickerRange(
                id='rango_fechas',
                start_date=df['Fecha'].min(),
                end_date=df['Fecha'].max(),
                display_format='DD/MM/YYYY'
            )
        ], style={"display": "inline-block", "marginRight": "40px"}),

        html.Div([
            html.Label("Cliente"),
            dcc.Dropdown(
                id='filtro_cliente',
                options=[{"label": c, "value": c} for c in df['Numero_Cliente'].unique()],
                value=None,
                placeholder="Todos",
                style={"width": "300px"}
            )
        ], style={"display": "inline-block"}),
    ], style={"padding": "20px 30px"}),

    html.Div([
        dash_table.DataTable(
            id='tabla_detalle',
            columns=[
                {"name": "Fecha", "id": "Fecha"},
                {"name": "Volumen observado", "id": "Volumen"},
                {"name": "Volumen predicho", "id": "Volumen_Predicho"},
                {"name": "Error", "id": "Error"},
                {"name": "Alerta", "id": "Tipo"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "fontSize": 14},
            page_size=10
        )
    ], style={"padding": "0px 30px 30px 30px"})
])

@app.callback(
    [Output("grafico_comparacion", "figure"),
     Output("tabla_detalle", "data")],
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
        borde = yref * (1 + signo * 0.30)
        fig.add_trace(go.Scatter(
            x=df_filtrado['Fecha'],
            y=borde,
            mode="lines",
            line=dict(color="rgba(0,0,255,0.4)", dash="dot"),
            showlegend=False,
            hoverinfo="skip"
        ))

    niveles = [
        {"inf": 0.30, "sup": 0.60, "color": "rgba(230,240,250,0.3)"},
        {"inf": 0.60, "sup": 0.80, "color": "rgba(255, 225, 153, 0.3)"},
        {"inf": 0.80, "sup": 1.00, "color": "rgba(255, 204, 204, 0.3)"},
    ]

    for banda in niveles:
        y0 = yref * (1 + banda["inf"])
        y1 = yref * (1 + banda["sup"])
        fig.add_trace(go.Scatter(
            x=pd.concat([df_filtrado["Fecha"], df_filtrado["Fecha"][::-1]]),
            y=pd.concat([y0, y1[::-1]]),
            fill="toself",
            fillcolor=banda["color"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=False
        ))
        y0_inf = yref * (1 - banda["inf"])
        y1_sup = yref * (1 - banda["sup"])
        fig.add_trace(go.Scatter(
            x=pd.concat([df_filtrado["Fecha"], df_filtrado["Fecha"][::-1]]),
            y=pd.concat([y1_sup, y0_inf[::-1]]),
            fill="toself",
            fillcolor=banda["color"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=False
        ))

    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen_Predicho'], mode='lines+markers', name='Valores predichos'))
    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen'], mode='markers', name='Valores observados', marker=dict(color='red')))

    fig.update_layout(title='Comparación de consumo de gas con bandas de alerta', xaxis_title='Fecha', yaxis_title='Volumen (m3)', template='plotly_dark', height=600)

    tabla_data = df_filtrado[['Fecha', 'Volumen', 'Volumen_Predicho', 'Error', 'Tipo']].copy()
    tabla_data['Fecha'] = tabla_data['Fecha'].dt.strftime('%d/%m/%Y')

    return fig, tabla_data.to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)
