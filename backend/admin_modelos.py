import os
import pandas as pd
from modelo import modelo_hibrido_svr_dbscan_2, riesgo_cluster
import shutil

DATA_DIR = "data"
NUEVO = os.path.join(DATA_DIR, "resultado_modelo_nuevo.xlsx")
ACTUAL = os.path.join(DATA_DIR, "resultado_modelo_actual.xlsx")


def reentrenar_modelo():
    print("Reentrenando modelo...")
    # Leer datos originales
    file_name = 'Datos Contugas.xlsx'
    file_path = os.path.abspath(file_name)
    excel_data = pd.ExcelFile(file_path)

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

    df_resultado = modelo_hibrido_svr_dbscan_2(df_combined, usar_temperatura=True, usar_presion=False)
    df_resultado_riesgo = riesgo_cluster(df_resultado)

    df_resultado_riesgo.to_excel(NUEVO, index=False)
    print(f"Modelo reentrenado y guardado en: {NUEVO}")


def comparar_modelos():
    if not os.path.exists(NUEVO):
        print("Debes reentrenar el modelo primero.")
        return

    if not os.path.exists(ACTUAL):
        print("No hay modelo actual para comparar.")
        return

    print("Comparando modelos...")

    nuevo = pd.read_excel(NUEVO)
    viejo = pd.read_excel(ACTUAL)

    mse_nuevo = nuevo['Residual'].abs().mean()
    mse_viejo = viejo['Residual'].abs().mean()

    print(f"MSE del modelo nuevo : {mse_nuevo:.4f}")
    print(f"MSE del modelo actual: {mse_viejo:.4f}")

    if mse_nuevo < mse_viejo:
        print("El modelo NUEVO es mejor.")
    else:
        print("El modelo ACTUAL es mejor.")


def aplicar_nuevo_modelo():
    if not os.path.exists(NUEVO):
        print("No hay modelo nuevo entrenado.")
        return

    shutil.copyfile(NUEVO, ACTUAL)
    print(f"Modelo aplicado correctamente: {ACTUAL}")


def menu():
    while True:
        print("\n=== ADMINISTRADOR DE MODELOS ===")
        print("1.Reentrenar modelo")
        print("2.Comparar modelos")
        print("3.Aplicar modelo nuevo")
        print("4.Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            reentrenar_modelo()
        elif opcion == "2":
            comparar_modelos()
        elif opcion == "3":
            aplicar_nuevo_modelo()
        elif opcion == "4":
            break
        else:
            print("Opción inválida")


if __name__ == "__main__":
    menu()