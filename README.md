# PROYECTO CONTUGAS - Detección de Outliers en Consumo de Gas

Este proyecto es un dashboard interactivo desarrollado con **Dash + Plotly** que implementa un sistema de detección de consumos anómalos de gas natural por cliente. Está basado en modelos de **clustering (DBSCAN)** y **regresión no lineal (SVR)**.

##  Funcionalidades principales

- Visualización comparativa entre consumo real y predicho por cliente.
- Detección de outliers clasificados por severidad (leve, grave, crítica).
- Filtros por cliente y rango de fechas.
- Tabla interactiva con detalle de anomalías.
- Despliegue en Railway para acceso web.

## Estructura del proyecto

PROYECTO_CONTUGAS_REV1/
├── app.py # Aplicación principal Dash
├── resultado_modelo_4.xlsx # Dataset generado por el modelo final
├── requirements.txt # Dependencias para desplegar
├── Procfile # Archivo para ejecución en Railway
└── assets/
└── styles.css # Estilo visual del dashboard

##  Despliegue en Railway

1. Crear un repositorio en GitHub con esta estructura.
2. Conectar Railway a tu cuenta GitHub.
3. Crear nuevo proyecto > Deploy from GitHub repo.
4. Railway detectará `Procfile` y desplegará automáticamente.

##  Autores
