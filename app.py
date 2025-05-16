import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.graph_objects as go

# Cargar los datos
df = pd.read_pickle("resultado_modelo_2023.pkl")
df['Año'] = df['Fecha'].dt.year

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

app.layout = html.Div(style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f8f9fa"}, children=[
    # Encabezado con logos y título
    html.Div([
        html.Img(src="/assets/uniandes_logo.png", style={"height": "60px"}),
        html.H2("DETECCIÓN DE OUTLIERS EN EL CONSUMO DE GAS", style={"margin": "0 auto", "textAlign": "center"}),
        html.Img(src="/assets/contugas_logo.png", style={"height": "60px"})
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
              "backgroundColor": "#ececec", "padding": "10px 40px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),

    # Tarjetas
    html.Div(id="indicadores", style={"display": "flex", "justifyContent": "space-around",
                                      "padding": "20px 10px"}),

    # Gráfico
    dcc.Graph(id='grafico_comparacion', style={"padding": "0px 20px"}),

    # Filtros
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
    ], style={"padding": "10px 30px"}),

    # Tabla
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
            style_cell={"textAlign": "center", "fontSize": 14, "padding": "5px"},
            style_header={"backgroundColor": "#eaeaea", "fontWeight": "bold"},
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

    # Indicadores
    tarjetas = [
        html.Div([
            html.H3(f"{df_filtrado['Numero_Cliente'].nunique()}", style={"marginBottom": "0px"}),
            html.P("Clientes")
        ], style=card_style),

        html.Div([
            html.H3(f"{df_filtrado[df_filtrado['Tipo'] != '🟢 Sin alerta'].shape[0]}", style={"marginBottom": "0px", "color": "red"}),
            html.P("Outliers")
        ], style=card_style),

        html.Div([
            html.H3(f"{df_filtrado[df_filtrado['Tipo'].str.contains('🔴')].shape[0]}", style={"marginBottom": "0px", "color": "#FFA500"}),
            html.P("Alarmas críticas")
        ], style=card_style),
    ]

    # Gráfico
    fig = go.Figure()
    yref = df_filtrado['Volumen_Predicho']

    # Bandas escalonadas
    escalones = [
        (0.0, 0.30, "rgba(173,216,230,0.2)"),  # azul claro
        (0.30, 0.60, "rgba(255,255,153,0.3)"),  # amarillo
        (0.60, 0.80, "rgba(255,204,153,0.3)"),  # naranja
        (0.80, 1.00, "rgba(255,102,102,0.3)")   # rojo claro
    ]

    for inf, sup, color in escalones:
        fig.add_trace(go.Scatter(
            x=pd.concat([df_filtrado["Fecha"], df_filtrado["Fecha"][::-1]]),
            y=pd.concat([yref * (1 + inf), yref[::-1] * (1 + sup)]),
            fill="toself", fillcolor=color,
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip", showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=pd.concat([df_filtrado["Fecha"], df_filtrado["Fecha"][::-1]]),
            y=pd.concat([yref * (1 - inf), yref[::-1] * (1 - sup)]),
            fill="toself", fillcolor=color,
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip", showlegend=False
        ))

    # Series principales
    fig.add_trace(go.Scatter(
        x=df_filtrado['Fecha'],
        y=df_filtrado['Volumen_Predicho'],
        mode='lines+markers',
        name='Valores predichos',
        line=dict(color="blue")
    ))

    fig.add_trace(go.Scatter(
        x=df_filtrado['Fecha'],
        y=df_filtrado['Volumen'],
        mode='markers',
        name='Error',
        marker=dict(color='red', size=4)
    ))

    fig.update_layout(
        title='Comparación de consumo de gas con bandas de alerta',
        xaxis_title='Fecha',
        yaxis_title='Volumen (m3)',
        template='plotly_white',
        height=550,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    tabla_data = df_filtrado[['Fecha', 'Volumen', 'Volumen_Predicho', 'Error', 'Tipo']].copy()
    tabla_data['Fecha'] = tabla_data['Fecha'].dt.strftime('%d/%m/%Y')

    return fig, tabla_data.to_dict('records'), tarjetas


# Estilo para las tarjetas
card_style = {
    "backgroundColor": "white",
    "padding": "20px",
    "borderRadius": "10px",
    "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
    "textAlign": "center",
    "width": "200px"
}

if __name__ == '__main__':
    app.run_server(debug=True)

