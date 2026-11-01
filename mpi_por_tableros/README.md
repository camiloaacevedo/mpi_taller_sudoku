# Tarea 1: repartir tableros

`mpi_tableros.py`: el proceso 0 es coordinador y reparte los IDs **bajo demanda**
(cuando un trabajador termina, recibe el siguiente). Se eligió reparto dinámico y no
fijo porque los tableros tardan entre 2 y 10 s: con un reparto fijo, un proceso con
tableros difíciles dejaría a los demás esperando. Reutiliza `resolver_con_tiempo` de
`../sudoku.py`. El coordinador reúne los estados, confirma cuántos IDs se procesaron y
mide el tiempo real (`MPI.Wtime`) desde el primer reparto hasta recibir el último resultado.
Los N procesos incluyen al coordinador, que casi no consume CPU (duerme entre sondeos).

Ejecutar desde la carpeta raíz del proyecto (reemplaza `N` por el valor del informe):

```bash
# macOS
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_por_tableros/mpi_tableros.py --all
```
```powershell
# Windows PowerShell
docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_por_tableros/mpi_tableros.py --all
```

Un solo tablero: cambia `--all` por `--id 7`.

## Resultados
- Tiempo total (mediana de 3, con N = 11): 22,743 s (aceleración 5,57 frente a 126,772 s del secuencial)
- IDs procesados: 30 de 30