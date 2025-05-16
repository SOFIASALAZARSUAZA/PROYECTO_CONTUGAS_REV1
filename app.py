import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px

# Leer CSV 
#sheet_id = "1DtvLWWRj01lXN050djKPfbPfMElM_dqx" prueba
#csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv" otra prueba
df = pd.read_pickle("resultado_modelo_2023.pkl")

# Crear columnas de fecha adicionales si no existen
df['Año'] = df['Fecha'].dt.year
df['Mes'] = df['Fecha'].dt.month
df['Dia'] = df['Fecha'].dt.day

# Clasificación del tipo de alerta según el error
def clasificar_alerta(e):
    if e > 40:
        return "Crítica"
    elif e > 20:
        return "Grave"
    elif e > 10:
        return "Leve"
    else:
        return "Sin alerta"

# Asegurar columna 'Error'
if 'Error' not in df.columns:
    df['Error'] = np.abs(df['Volumen'] - df['Volumen_Predicho'])

# Asegurar columna 'Tipo'
if 'Tipo' not in df.columns:
    df['Tipo'] = df['Error'].apply(clasificar_alerta)

# Inicialización de la app
app = Dash(__name__)
server = app.server  # Para Railway

app.layout = html.Div([
    html.Div([
        html.Img(src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Escudo_Uniandes.svg/1200px-Escudo_Uniandes.svg.png", style={"height": "50px"}),
        html.Img(src="https://www.contugas.com.pe/wp-content/uploads/2021/03/logo-contugas.png", style={"height": "50px", "float": "right"})
    ], style={"display": "flex", "justify-content": "space-between", "padding": "10px 30px"}),

    html.H2("DETECCIÓN DE OUTLIERS EN EL CONSUMO DE GAS", style={"textAlign": "center", "marginTop": "10px"}),

    html.Div([
        html.Div([html.H3(f"{df['Numero_Cliente'].nunique()}", style={"marginBottom": "0px"}), html.P("Clientes")], className="card"),
        html.Div([html.H3(f"{df[df['Tipo'] != 'Sin alerta'].shape[0]}", style={"marginBottom": "0px"}), html.P("Outliers")], className="card"),
        html.Div([html.H3(f"{df[df['Tipo'] == 'Crítica'].shape[0]}", style={"marginBottom": "0px"}), html.P("Alarmas críticas")], className="card"),
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
                placeholder="Todos"
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
                {"name": "Tipo", "id": "Tipo"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center"},
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
    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen_Predicho'], mode='lines+markers', name='Valores predichos'))
    fig.add_trace(go.Scatter(x=df_filtrado['Fecha'], y=df_filtrado['Volumen'], mode='markers', name='Error', marker=dict(color='red')))

    fig.update_layout(title='Comparación de consumo de gas', xaxis_title='Comparación de consumo', yaxis_title='Volumen (m3)', template='plotly_white')

    tabla_data = df_filtrado[['Fecha', 'Volumen', 'Volumen_Predicho', 'Error', 'Tipo']].copy()
    tabla_data['Fecha'] = tabla_data['Fecha'].dt.strftime('%d/%m/%Y')

    return fig, tabla_data.to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)
