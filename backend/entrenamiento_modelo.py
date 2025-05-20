# entrenamiento_modelo.py
import os
import pandas as pd
from modelo import modelo_hibrido_svr_dbscan_2, riesgo_cluster

INPUT_PATH = os.path.join("input", "Datos Contugas.xlsx")
OUTPUT_PATH = os.path.join("data", "resultado_modelo_nuevo.xlsx")

# 1. Cargar datos
excel_data = pd.ExcelFile(INPUT_PATH)
df_combined = pd.DataFrame()
for i, sheet_name in enumerate(excel_data.sheet_names, start=1):
    df_temp = excel_data.parse(sheet_name)
    df_temp['Numero_Cliente'] = f'CLIENTE{i}'
    df_combined = pd.concat([df_combined, df_temp], ignore_index=True)

df_combined['Fecha'] = pd.to_datetime(df_combined['Fecha'])
df_combined['Mes'] = df_combined['Fecha'].dt.month
df_combined['dia_semana'] = df_combined['Fecha'].dt.dayofweek
df_combined['semana_anio'] = df_combined['Fecha'].dt.isocalendar().week
df_combined['es_fin_de_semana'] = df_combined['dia_semana'].apply(lambda x: 1 if x >= 5 else 0)

# 2. Aplicar modelo
df_resultado = modelo_hibrido_svr_dbscan_2(df_combined, usar_temperatura=True, usar_presion=False)

# 3. Clasificar riesgo
df_resultado_riesgo = riesgo_cluster(df_resultado)

# 4. Guardar el nuevo resultado
df_resultado_riesgo.to_excel(OUTPUT_PATH, index=False)
print(f"Archivo generado: {OUTPUT_PATH}")