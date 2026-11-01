# Tarea 3: combinar tableros y ramas

`mpi_hibrido.py`: el proceso 0 reparte IDs bajo demanda entre **grupos**. Los demás
procesos se dividen con `Comm.Split` en grupos de tamaño `--grupo G` (el último grupo
absorbe el sobrante). En cada grupo, el líder recibe un ID, reparte las ramas de ese
tablero entre los demás miembros (mismo protocolo de `../ramas_comun.py`, con
cancelación al hallar la solución) y avisa el resultado al proceso 0.
Con `--grupo 1` equivale a la Tarea 1; con `--grupo N-1` equivale a la Tarea 2.

## Cómo elegir el tamaño de grupo
Se probaron los valores 1, 2, 3, 5 y 10 de `--grupo` con el mismo `N` y se eligió el de
menor mediana de tiempo (script abajo). Criterio: grupos pequeños reparten mejor los
tableros (menos esperas por tableros difíciles) pero un líder por grupo es un proceso que
no explora; grupos grandes aprovechan más ramas por tablero pero serializan los tableros.
Grupo elegido = **5** (con N = 11): mediana de 21,295 s. Su diferencia con el grupo de 1
(21,453 s) es menor que la variación entre repeticiones, así que ambos quedan prácticamente
empatados. El grupo de 2 fue el peor (29,987 s): con 1 líder y 1 solo explorador por grupo,
la mitad de los procesos no busca. Tabla de pruebas abajo.

```bash
# macOS (G = tamaño de grupo)
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_hibrido/mpi_hibrido.py --grupo G --all
```
```powershell
# Windows
docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_hibrido/mpi_hibrido.py --grupo G --all
```

Medir 3 repeticiones y mediana para un G (dentro del contenedor):

```bash
docker run --rm -v "$(pwd):/app" augustosalazar/slim-mpi:2 python /app/medir.py -- mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n N python /app/mpi_hibrido/mpi_hibrido.py --grupo G --all
```

| Grupo G | Mediana (s) | Aceleración frente al secuencial (126,772 s) |
| ---: | ---: | ---: |
| 1 | 21,453 | 5,91 |
| 2 | 29,987 | 4,23 |
| 3 | 22,604 | 5,61 |
| 5 | 21,295 | 5,95 |
| 10 | 24,254 | 5,23 |