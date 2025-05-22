from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import os

# ------------------------------------------------------
# 19/05 12:25 CAMBIOS PARA SOPORTE EN RAILWAY - SOFIA SALAZAR
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

# Convertir columna 'outlier' a booleano si existe
if 'outlier' in df.columns:
    df['outlier'] = df['outlier'].astype(str).str.strip().str.upper().map({
        'VERDADERO': True, 'FALSO': False, 'TRUE': True, 'FALSE': False
    }).fillna(False)

# Eliminar registros sin fecha válida
df = df.dropna(subset=['Fecha'])

# Crear columna con formato detallado para graficar por fecha y hora
df['Fecha_redonda'] = df['Fecha'].dt.strftime('%Y-%m-%d %H:%M')

# Endpoint KPIs
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

# Endpoint rango fechas
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

# Endpoint gráfico volumen
@app.route('/grafico_volumen', methods=['GET'])
def grafico_volumen():
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
        df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('Sin riesgo').isin(riesgos_lista)]

    if df_filtrado.empty or 'Riesgo' not in df_filtrado.columns:
        return jsonify({"datos": []})

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

    df_agrupado = df_filtrado.groupby('Fecha_redonda').agg({
        'Volumen': 'mean',
        'Presion': 'mean',
        'Temperatura': 'mean',
        'Riesgo': calcular_riesgo
    }).reset_index()

    data = {
        "datos": [
            {
                "x": row['Fecha_redonda'],
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

        df_filtrado = df[df['outlier'] == True] if 'outlier' in df.columns else pd.DataFrame()

        # Aplicar filtros adicionales
        if cliente and cliente.lower() != 'todos':
            df_filtrado = df_filtrado[df_filtrado['Numero_Cliente'] == cliente]
        if inicio:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] >= pd.to_datetime(inicio)]
        if fin:
            df_filtrado = df_filtrado[df_filtrado['Fecha'] <= pd.to_datetime(fin)]
        if riesgos_param and 'Riesgo' in df_filtrado.columns:
            riesgos_lista = riesgos_param.split(',')
            df_filtrado = df_filtrado[df_filtrado['Riesgo'].fillna('').isin(riesgos_lista)]

        # ✅ Verificar si hay datos antes de continuar
        if df_filtrado.empty:
            return jsonify({"dias": [], "horas": [], "matriz": []})

        # Procesamiento
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
        print(f"Error en /anomalias_por_dia_hora: {e}")
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
