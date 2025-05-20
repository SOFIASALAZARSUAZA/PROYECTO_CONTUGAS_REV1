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

├── requirements.txt # Dependencias para desplegar
├── Railway.json # Archivo para ejecución en Railway
backend/
├── data/
│   ├── modelo_actual # Modelo con el cual se ejecuta la aplicación
│   ├── modelo_nuevo
├── input/
│   ├── Datos_Contugas # Datos de ingreso para el modelo
├── frontend/
│   ├── index.html
│   ├── style.css # Estilo visual del dashboard
│   ├── script.js  
├── app.py # Aplicación principal 
├── modelo.py # Modelo
├── entrenamiento_modelos.py # Entrenamiento del modelo
├── admin_modelos.py # Administración de modelos


##  Despliegue en Railway

La aplicación se encuentra desplegada en Railway con el siguiente link: https://web-production-e3288.up.railway.app/

##  Autores
