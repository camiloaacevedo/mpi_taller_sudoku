# Tarea 2: repartir ramas de cada tablero

`mpi_ramas.py`: los 30 IDs se procesan **en orden**. Para cada tablero, el proceso 0
expande las primeras casillas vacías (opciones válidas, en el mismo orden DFS del serial)
hasta tener al menos `max(8, 4*trabajadores)` ramas y las reparte bajo demanda.
Cada trabajador explora su rama con backtracking y, cada 2000 nodos, mira si el
coordinador pidió parar. Cuando una rama devuelve la solución, el coordinador envía una
orden de parada (con el número de tablero, para ignorar órdenes atrasadas) y espera a que
todos contesten antes de pasar al siguiente tablero. Se muestra el tiempo parcial de
cada ID y el total real. Se conserva `--id`.

Código común (ramas, cancelación): `../ramas_comun.py`.

```bash
# macOS - todos los IDs
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_por_ramas/mpi_ramas.py --all
# macOS - un ID
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_por_ramas/mpi_ramas.py --id 7
```
```powershell
# Windows - todos los IDs
docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_por_ramas/mpi_ramas.py --all
# Windows - un ID
docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_por_ramas/mpi_ramas.py --id 7
```

Nota: de los N procesos, uno es coordinador (casi inactivo), así que exploran N-1.
El tiempo total de `--all` se compara con el serial en `../INFORME.md`.
