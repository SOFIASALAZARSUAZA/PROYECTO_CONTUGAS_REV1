import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import mean_squared_error


def modelo_hibrido_svr_dbscan_2(df, usar_temperatura=True, usar_presion=True, median_factor=1.5, max_iter=5, min_samples=8):
    df = df.copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.set_index('Fecha')
    df['Mes'] = df.index.month
    df['Dia_Semana'] = df.index.dayofweek

    resultados = []

    for cliente_id, grupo in df.groupby("Numero_Cliente"):
        grupo = grupo.sort_index()

        for var in ["Temperatura", "Presion"]:
            if var in grupo.columns:
                max_val = grupo[var].max(skipna=True)
                grupo[var] = grupo[var].fillna(100 * max_val)

        grupo['Volumen'] = grupo['Volumen'].fillna(100 * grupo['Volumen'].max(skipna=True))
        grupo['x_seq'] = np.arange(len(grupo))

        features = ['x_seq', 'Mes', 'Dia_Semana']
        if usar_temperatura and 'Temperatura' in grupo.columns:
            features.insert(0, 'Temperatura')
        if usar_presion and 'Presion' in grupo.columns:
            features.insert(0, 'Presion')

        X_base = grupo[features]
        Y = grupo['Volumen'].copy()

        SVR_features = [col for col in features if col != 'x_seq']
        X_base_SVR = grupo[SVR_features]
        clustering_features = ['x_seq', 'Mes', 'Dia_Semana']
        X_base_dbscan = grupo[clustering_features]

        outlier_filamentos_idx = set()
        final_labels = pd.Series(index=grupo.index, data=np.nan)
        umbral_residual = 0.05 * Y.max()

        for _ in range(max_iter):
            if Y.isna().any():
                max_y = Y.max(skipna=True)
                Y = Y.fillna(100 * max_y if not pd.isna(max_y) else 1e6)

            scaler_X = StandardScaler()
            X_scaled = scaler_X.fit_transform(X_base_dbscan)

            scaler_Y = StandardScaler()
            Y_scaled = scaler_Y.fit_transform(Y.values.reshape(-1, 1))

            XY_scaled = np.hstack([X_scaled, Y_scaled])

            k = min(20, len(XY_scaled) - 1)
            neighbors = NearestNeighbors(n_neighbors=k)
            distances, _ = neighbors.fit(XY_scaled).kneighbors(XY_scaled)
            distances_k = np.sort(distances[:, k - 1])
            eps = np.percentile(distances_k, 95)

            db = DBSCAN(eps=eps, min_samples=min_samples)
            labels = db.fit_predict(XY_scaled)

            inliers_mask = labels != -1
            if inliers_mask.sum() < 5:
                break

            X_train = X_base_SVR[inliers_mask]
            Y_train = Y[inliers_mask]
            svr = SVR()
            svr.fit(X_train, Y_train)
            Y_pred = svr.predict(X_train)
            residuals = np.abs(Y_train - Y_pred)

            df_temp = pd.DataFrame({'label': labels[inliers_mask], 'residual': residuals})
            cluster_residual_mean = df_temp.groupby('label')['residual'].mean()

            if cluster_residual_mean.empty:
                break

            top_cluster = cluster_residual_mean.idxmax()
            top_residual = cluster_residual_mean.max()
            if top_residual < umbral_residual:
                break

            cluster_mask = (labels == top_cluster)
            cluster_idx = grupo.index[cluster_mask]
            outlier_filamentos_idx.update(cluster_idx)
            Y.loc[cluster_idx] = np.nan

        X_final_train = X_base_SVR.drop(index=outlier_filamentos_idx)
        Y_final_train = Y.drop(index=outlier_filamentos_idx)
        modelo_final = SVR()
        modelo_final.fit(X_final_train, Y_final_train)

        X_to_predict = X_base_SVR.copy()
        Y_filled = Y.copy()
        if Y_filled.isna().any():
            max_y = Y_filled.max(skipna=True)
            Y_filled = Y_filled.fillna(100 * max_y if not pd.isna(max_y) else 1e6)

        Y_pred_final = modelo_final.predict(X_to_predict)
        mse = mean_squared_error(Y_filled, Y_pred_final)

        grupo_resultado = grupo.copy()
        grupo_resultado['Volumen_Predicho'] = Y_pred_final
        grupo_resultado['MSE'] = mse
        grupo_resultado['outlier'] = False
        grupo_resultado.loc[list(outlier_filamentos_idx), 'outlier'] = True

        val_mask = X_to_predict.notnull().all(axis=1) & Y_filled.notnull()
        X_valid_dbscan = grupo.loc[val_mask, clustering_features]
        Y_valid = Y_filled[val_mask]

        XY_scaled_pred = np.hstack([
            scaler_X.transform(X_valid_dbscan),
            scaler_Y.transform(Y_valid.values.reshape(-1, 1))
        ])
        labels_pred = db.fit_predict(XY_scaled_pred)
        final_labels_partial = pd.Series(index=X_valid_dbscan.index, data=labels_pred)
        final_labels.update(final_labels_partial)

        grupo_resultado['cluster_dbscan'] = final_labels
        resultados.append(grupo_resultado)
        print(f"CLIENTE {cliente_id} -> DONE")

    return pd.concat(resultados)


def riesgo_cluster(df):
    df_outliers = df[df['outlier'] == 1].copy()
    resumen = (
        df_outliers.groupby(['Numero_Cliente', 'cluster_dbscan'])['Residual']
        .apply(lambda x: np.mean(np.abs(x)))
        .reset_index(name='Residual_Promedio_Abs')
    )

    def asignar_riesgo(grupo):
        p33 = grupo['Residual_Promedio_Abs'].quantile(0.33)
        p66 = grupo['Residual_Promedio_Abs'].quantile(0.66)
        grupo = grupo.copy()
        grupo['Riesgo'] = grupo['Residual_Promedio_Abs'].apply(
            lambda valor: 'Bajo' if valor <= p33 else 'Medio' if valor <= p66 else 'Alto'
        )
        return grupo

    resultado = (
        resumen.groupby('Numero_Cliente', group_keys=False)
        .apply(asignar_riesgo)
        .reset_index(drop=True)
    )

    df = df.merge(
        resultado[['Numero_Cliente', 'cluster_dbscan', 'Riesgo', 'Residual_Promedio_Abs']],
        on=['Numero_Cliente', 'cluster_dbscan'],
        how='left'
    )
    df['Riesgo'] = df['Riesgo'].fillna("Sin riesgo")
    return df