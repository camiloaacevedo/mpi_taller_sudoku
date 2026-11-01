"""Ejecuta un comando 3 veces y reporta la mediana del 'Tiempo total'.

Uso (dentro del contenedor), ejemplo:
  python /app/medir.py -- python /app/baseline_secuencial.py --all
  python /app/medir.py -- mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 8 python /app/mpi_por_tableros/mpi_tableros.py --all
"""
import re, statistics, subprocess, sys

args = sys.argv[1:]
if args and args[0] == "--":
    args = args[1:]
if not args:
    sys.exit(__doc__)
tiempos = []
for i in range(1, 4):
    salida = subprocess.run(args, capture_output=True, text=True).stdout
    m = re.search(r"Tiempo total[^:]*:\s*([\d.]+)", salida)
    if not m:
        sys.exit("No se encontró 'Tiempo total' en la salida:\n" + salida[-500:])
    tiempos.append(float(m.group(1)))
    print(f"Repetición {i}: {tiempos[-1]:.3f} s", flush=True)
print(f"MEDIANA: {statistics.median(tiempos):.3f} s")
