from flask import Flask, jsonify, request
from flask import send_from_directory
from flask_cors import CORS
import pandas as pd
import os

# ------------------------------------------------------
# 19/05 12:25 SE REALIZA CAMBIO PARA PODER UTILIZAR 
# RAILWAY CAMBIO REALIZADO POR SOFIA SALAZAR 
# ------------------------------------------------------
app = Flask(__name__)
server = app  # Necesario para Gunicorn y Railway
CORS(app)

# Cargar el archivo 
ruta_excel = os.path.join(os.path.dirname(__file__), 'data', 'resultado_modelo_actual.xlsx')
df = pd.read_excel(ruta_excel)

# Limpiar y convertir columnas relevantes
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
df['Volumen'] = pd.to_numeric(df['Volumen'], errors='coerce')
df['Presion'] = pd.to_numeric(df['Presion'], errors='coerce')
df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce')
df = df.dropna(subset=['Fecha'])

# Agrupar por cliente y fecha para series temporales
# ------------------------------------------------------
# 19/05 12:25 SE REALIZA CAMBIO EN LAS COLUMNAS DADO QUE 
# SE AJUSTA ARCHIVO XLSX POR TAMAÑO PARA LOGRAR USAR LFS
# CAMBIO REALIZADO POR SOFIA SALAZAR 
# ------------------------------------------------------
df_grouped = df.groupby(['Numero_Cliente', 'Fecha']).agg({
    'Volumen': 'mean',
    'Presion': 'mean',
    'Temperatura': 'mean',
    'Volumen_Predicho': 'mean',
    'Residual': 'mean',
}).reset_index()

df_total_grouped = df.groupby('Fecha').agg({
    'Volumen': 'mean',
    'Presion': 'mean',
    'Temperatura': 'mean'
}).reset_index()

@app.route('/kpis', methods=['GET'])
def obtener_kpis():
    cliente = request.args.get('cliente')
    inicio = request.args.get('inicio')
    fin = request.args.get('fin')
    riesgos_param = request.args.get('riesgos')

    df_filtrado = df.copy()
    if cliente and cliente.lower() != 'todos':
        df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
    if inicio:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
    if fin:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
    if riesgos_param:
        riesgos_lista = riesgos_param.split(',')
        df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('').isin(riesgos_lista)]

    kpis = {
        'total_clientes': df_filtrado['Numero_Cliente'].nunique(),
        'total_anomalias': int(df_filtrado['outlier'].sum()) if 'outlier' in df_filtrado.columns else 0,
        'alertas_criticas': int(df_filtrado[df_filtrado['Riesgo'] == 'Alto'].shape[0]),
        'promedio_volumen': round(df_filtrado['Volumen'].mean(), 2),
        'promedio_presion': round(df_filtrado['Presion'].mean(), 2),
        'promedio_temperatura': round(df_filtrado['Temperatura'].mean(), 2)
    }
    return jsonify(kpis)

@app.route('/rangos_fechas', methods=['GET'])
def rangos_fechas():
    cliente = request.args.get('cliente')
    df_filtrado = df[df['Numero_Cliente'] == cliente] if cliente and cliente.lower() != 'todos' else df

    if df_filtrado.empty:
        return jsonify({"min_fecha": None, "max_fecha": None})

    return jsonify({
        "min_fecha": df_filtrado['Fecha'].min().strftime("%Y-%m-%d"),
        "max_fecha": df_filtrado['Fecha'].max().strftime("%Y-%m-%d")
    })
@app.route('/grafico_volumen', methods=['GET'])
def grafico_volumen():
    cliente = request.args.get('cliente')
    inicio = request.args.get('inicio')
    fin = request.args.get('fin')
    riesgos_param = request.args.get('riesgos')

    df_filtrado = df.copy()

    # Aplicar filtros
    if cliente and cliente.lower() != 'todos':
        df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
    if inicio:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
    if fin:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
    if riesgos_param:
        riesgos_lista = riesgos_param.split(',')
        df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('Sin riesgo').isin(riesgos_lista)]

    # Verificar si hay datos y si 'Riesgo' existe
    if df_filtrado.empty or 'Riesgo' not in df_filtrado.columns:
        return jsonify({"datos": []})

    # Función corregida para manejar Series
    def calcular_riesgo(grupo):
        if grupo.empty:
            return 'Sin riesgo'
        if (grupo == 'Alto').any():
            return 'Alto'
        elif (grupo == 'Medio').any():
            return 'Medio'
        elif (grupo == 'Bajo').any():
            return 'Bajo'
        return 'Sin riesgo'

    # Agrupar y calcular
    df_agrupado = df_filtrado.groupby('Fecha').agg({
        'Volumen': 'mean',
        'Presion': 'mean',
        'Temperatura': 'mean',
        'Riesgo': calcular_riesgo  # Usamos la función corregida
    }).reset_index()

    data = {
        "datos": [
            {
                "x": row['Fecha'].strftime("%Y-%m-%d"),
                "y": round(row['Volumen'], 2),
                "presion": round(row['Presion'], 2),
                "temperatura": round(row['Temperatura'], 2),
                "riesgo": row['Riesgo']
            }
            for _, row in df_agrupado.iterrows()
        ]
    }

    return jsonify(data)

@app.route('/riesgo_por_cliente', methods=['GET'])
def riesgo_por_cliente():
    try:
        cliente = request.args.get('cliente')
        inicio = request.args.get('inicio')
        fin = request.args.get('fin')
        riesgos_param = request.args.get('riesgos')

        df_filtrado = df.copy()
        if cliente and cliente.lower() != 'todos':
            df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
        if inicio:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
        if fin:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
        if riesgos_param:
            riesgos_lista = riesgos_param.split(',')
            df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('').isin(riesgos_lista)]

        conteo = df_filtrado.groupby(['Numero_Cliente', 'Riesgo']).size().unstack(fill_value=0)

        return jsonify({
            "clientes": list(conteo.index),
            "riesgos": list(conteo.columns),
            "valores": conteo.to_dict(orient='list')
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/anomalias_por_dia_hora', methods=['GET'])
def anomalias_por_dia_hora():
    try:
        cliente = request.args.get('cliente')
        inicio = request.args.get('inicio')
        fin = request.args.get('fin')
        riesgos_param = request.args.get('riesgos')

        df_filtrado = df[df['outlier'] == True]  # Solo anomalías
        
        # Aplicar filtros
        if cliente and cliente.lower() != 'todos':
            df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
        if inicio:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
        if fin:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
        if riesgos_param:
            riesgos_lista = riesgos_param.split(',')
            df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('').isin(riesgos_lista)]

        # Resto del código original...
        df_filtrado['hora'] = df_filtrado['Fecha'].dt.hour
        df_filtrado['dia_nombre'] = df_filtrado['Fecha'].dt.day_name(locale='es')

        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        mapping_dias = dict(zip(dias_orden, dias_es))

        heatmap = df_filtrado.groupby(['dia_nombre', 'hora']).size().unstack(fill_value=0)
        heatmap.index = heatmap.index.map(lambda d: mapping_dias.get(d, d))
        heatmap = heatmap.reindex(dias_es)

        return jsonify({
            "dias": list(heatmap.index),
            "horas": [str(h).zfill(2) for h in heatmap.columns],
            "matriz": heatmap.fillna(0).values.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tabla_registros', methods=['GET'])
def tabla_registros():
    cliente = request.args.get('cliente')
    inicio = request.args.get('inicio')
    fin = request.args.get('fin')
    riesgos_param = request.args.get('riesgos')

    df_filtrado = df.copy()
    if cliente and cliente.lower() != 'todos':
        df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
    if inicio:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
    if fin:
        df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
    if riesgos_param:
        riesgos_lista = riesgos_param.split(',')
        df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('').isin(riesgos_lista)]

    columnas = ['Fecha', 'Presion', 'Temperatura', 'Volumen', 'Volumen_Predicho', 'Residual', 'Riesgo']
    df_filtrado = df_filtrado[columnas].copy()
    df_filtrado['Riesgo'] = df_filtrado['Riesgo'].fillna('')
    orden_riesgo = {'Alto': 1, 'Medio': 2, 'Bajo': 3, '': 4}
    df_filtrado['riesgo_orden'] = df_filtrado['Riesgo'].map(orden_riesgo)
    df_filtrado = df_filtrado.sort_values('riesgo_orden').drop(columns='riesgo_orden').head(30)
    df_filtrado['Fecha'] = pd.to_datetime(df_filtrado['Fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(df_filtrado.to_dict(orient='records'))
# ------------------------------------------------------
# 19/05 12:25 SE REALIZA CAMBIO PARA PODER UTILIZAR 
# DASHBOARD DESDE HTML
# ------------------------------------------------------
@app.route('/')
def dashboard():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def frontend_static_files(filename):
    return send_from_directory('frontend', filename)

if __name__ == '__main__':
    app.run(debug=True)
