#!/bin/bash
# Script de entrada principal para Crontab
# Ejemplo de configuración crontab (ejecutar todos los días a las 2 AM):
# 0 2 * * * /ruta/absoluta/al/proyecto/run.sh >> /var/log/callqa-batch.log 2>&1

# 1. Posicionarse en el directorio del proyecto
cd "$(dirname "$0")" || exit 1

echo "========================================================"
echo "Iniciando CallQA Batch - $(date)"
echo "========================================================"

# 2. Cargar entorno virtual
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Error: Entorno virtual no encontrado en .venv/"
    exit 1
fi

# 3. Limpiar variables globales que interfieren y exportar PYTHONPATH
unset UPLOAD_DIRECTORY
unset CLIPS_OUTPUT_DIRECTORY
unset TEMP_DIRECTORY
export PYTHONPATH=$(pwd)

# 4. Ejecutar el script batch en Python
python src/worker.py

# 5. Capturar código de salida
EXIT_CODE=$?
echo "Proceso finalizado con código: $EXIT_CODE"
echo "========================================================"

exit $EXIT_CODE
