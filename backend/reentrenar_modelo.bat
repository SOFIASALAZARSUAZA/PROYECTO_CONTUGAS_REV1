@echo off
cls
echo ========================================
echo  INICIANDO REENTRENAMIENTO DEL MODELO
echo  Fecha: %DATE% %TIME%
echo ========================================

:: Ejecutar el script de entrenamiento
python entrenamiento_modelo.py

IF EXIST data\resultado_modelo_nuevo.xlsx (
    echo Modelo entrenado correctamente.
) ELSE (
    echo ERROR: No se generó el archivo resultado_modelo_nuevo.xlsx
    pause
    exit /b 1
)

IF EXIST data\resultado_modelo_actual.xlsx (
    echo Comparando modelo nuevo con actual...
    python -c "from admin_modelos import comparar_modelos; comparar_modelos()"
) ELSE (
    echo No existe modelo actual para comparar.
)

set /p confirm="¿Deseas aplicar el modelo nuevo como oficial? (s/n): "
if "%confirm%"=="s" (
    copy /Y data\resultado_modelo_nuevo.xlsx data\resultado_modelo_actual.xlsx
    echo Modelo nuevo aplicado correctamente.
) else (
    echo El modelo nuevo NO fue aplicado.
)

echo Proceso finalizado.
pause