from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
server = app  # Necesario para Gunicorn y Railway
CORS(app)

# Cargar el archivo
ruta_excel = os.path.join(os.path.dirname(__file__), 'data', 'resultado_modelo_actual.xlsx')
df = pd.read_excel(ruta_excel)

# Procesamiento de datos

if 'Fecha' in df.columns:
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df = df.dropna(subset=['Fecha'])

for col in ['Volumen', 'Presion', 'Temperatura']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

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
        'alertas_criticas': int(df_filtrado[df_filtrado['Riesgo'] == 'Alto'].shape[0]) if 'Riesgo' in df_filtrado.columns else 0,
        'promedio_volumen': round(df_filtrado['Volumen'].mean(), 2) if 'Volumen' in df_filtrado.columns else 0,
        'promedio_presion': round(df_filtrado['Presion'].mean(), 2) if 'Presion' in df_filtrado.columns else 0,
        'promedio_temperatura': round(df_filtrado['Temperatura'].mean(), 2) if 'Temperatura' in df_filtrado.columns else 0
    }
    return jsonify(kpis)

@app.route('/anomalias_por_dia_hora', methods=['GET'])
def anomalias_por_dia_hora():
    try:
        cliente = request.args.get('cliente')
        inicio = request.args.get('inicio')
        fin = request.args.get('fin')
        riesgos_param = request.args.get('riesgos')

        if 'outlier' not in df.columns:
            return jsonify({"dias": [], "horas": [], "matriz": []})

        df_filtrado = df[df['outlier'] == True]

        if cliente and cliente.lower() != 'todos':
            df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
        if inicio:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
        if fin:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
        if riesgos_param:
            riesgos_lista = riesgos_param.split(',')
            df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('').isin(riesgos_lista)]

        if df_filtrado.empty:
            return jsonify({"dias": [], "horas": [], "matriz": []})

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
            "matriz": heatmap.values.tolist()
        })

    except Exception as e:
        print(f"Error en /anomalias_por_dia_hora: {e}")
        return jsonify({"dias": [], "horas": [], "matriz": [], "error": str(e)}), 500

@app.route('/')
def dashboard():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def frontend_static_files(filename):
    return send_from_directory('frontend', filename)

if __name__ == '__main__':
    app.run(debug=True)
