# Informe de resultados

## Entorno

- Equipo: Arch Linux, Intel Core i5-12450H (12.ª generación, 8 núcleos y 12 hilos; combina 4 núcleos de alto rendimiento y 4 de eficiencia), 7,5 GiB de RAM.
- Versión del contenedor: `augustosalazar/slim-mpi:2`
- Cantidad de repeticiones por medición: 3
- Valor común de `N` elegido: 11 (recomendado por `detectar_procesos_mpi.py`: mediana de 1,653 s)

## Comparación final con el mismo `N`

Todas las filas MPI usan `N = 11`, el mismo `seeds.txt` y `mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe`.

| Implementación | Caso | Procesos | Mediana del tiempo total (s) | Aceleración frente a secuencial |
| --- | --- | ---: | ---: | ---: |
| Secuencial | Todos los IDs | 1 | 126,772 | 1,00 |
| MPI por tableros | Todos los IDs | 11 | 22,743 | 5,57 |
| MPI por ramas | Todos los IDs, uno después de otro | 11 | 26,096 | 4,86 |
| MPI híbrido (grupo de 5) | Todos los IDs | 11 | 21,295 | 5,95 |

Repeticiones (s): secuencial 125,943 / 126,998 / 126,772; tableros 21,850 / 22,743 / 22,900; ramas 26,195 / 26,096 / 25,943; híbrido (G=5) 21,295 / 21,227 / 21,383.

### Elección del tamaño de grupo del híbrido

Con N = 11 hay 10 procesos disponibles aparte del coordinador global. Se probaron cinco tamaños de grupo:

| Tamaño de grupo | Mediana (s) | Aceleración |
| ---: | ---: | ---: |
| 1 | 21,453 | 5,91 |
| 2 | 29,987 | 4,23 |
| 3 | 22,604 | 5,61 |
| 5 | 21,295 | 5,95 |
| 10 | 24,254 | 5,23 |

Se eligió 5 por tener la menor mediana. Su diferencia con el grupo de 1 (0,16 s) es menor que la variación entre repeticiones de una misma configuración, así que ambos quedan prácticamente empatados.

### Detalle de la versión por tableros (corrida con `--mostrar-rank`)

- Tiempo total: 21,888 s. Suma de tiempos parciales: 188,368 s (el secuencial suma 126,772 s).
- Tablero más lento: ID 3, con 16,701 s. Le siguen ID 8 (12,670 s), ID 18 (11,445 s) y ID 10 (11,393 s). El más rápido fue ID 28 (2,957 s).
- Tiempo ideal con 10 trabajadores y reparto perfecto: 126,772 / 10 = 12,677 s.
- Ocupación de los trabajadores: 188,368 / (10 × 21,888) = 86 %.

## Conclusiones

- **Menor tiempo.** El híbrido con grupos de 5 obtuvo el menor tiempo, 21,295 s, frente a 126,772 s del secuencial: 5,95 veces más rápido (se redujo el tiempo en 83 %, unos 105 s). Sin embargo, la ventaja sobre la versión por tableros (22,743 s) es de 6 %, y el híbrido con grupo de 1, que hace lo mismo que la versión por tableros, midió 21,453 s, es decir, el mismo tipo de diferencia aparece entre configuraciones equivalentes. Por eso no hay evidencia clara de que el híbrido supere a repartir tableros: ambas estrategias quedan en torno a 5,6–5,9 veces. Ninguna se acerca a 10 o 11 veces (eficiencia de 51–54 % con N = 11).

- **Comunicación y diferencias de duración.** La comunicación pesa poco: se envían mensajes pequeños (un ID y un resultado) y, en la versión por tableros, los trabajadores estuvieron ocupados el 86 % del tiempo. Lo que limita es la diferencia de duración entre tableros: van de 3 s a 16,7 s. Esto afecta de dos maneras. Primero, el tablero 3 (16,7 s) es más largo que el tiempo ideal de 12,7 s, de modo que repartir tableros completos no puede bajar de ahí. Segundo, al final de la ejecución algunos procesos se quedan sin tableros mientras otros terminan los últimos. Además, la suma de tiempos parciales (188,4 s) supera al tiempo secuencial (126,8 s): cada tablero tarda en promedio 1,49 veces más cuando hay 10 procesos corriendo a la vez. Esto es compatible con que los 12 hilos del equipo compartan recursos (núcleos, caché, memoria) y con que el procesador combine núcleos de alto rendimiento y de eficiencia, de modo que con muchos procesos algunos corren en núcleos más lentos; también concuerda con la calibración, donde una tarea perfectamente paralela solo aceleró 3,9 veces con N = 11. Es una explicación plausible que no comprobé con otra medición. El reparto dinámico (el siguiente tablero se asigna cuando un proceso queda libre) ayudó a que no hubiera esperas largas, pero no puede corregir el límite del tablero más largo.

- **Tableros frente a ramas.** Repartir tableros (22,743 s) fue más rápido que resolverlos en orden y repartir las ramas de cada uno (26,096 s), 15 % menos de tiempo. En la versión por ramas hay 30 puntos de sincronización, uno por tablero: el coordinador debe esperar a que todos los procesos confirmen la cancelación antes de pasar al siguiente, y cada tablero requiere generar ramas y enviar mensajes. Además, la búsqueda ya no sigue el mismo orden que el serial, por lo que puede explorar ramas que el serial no habría visitado. Estas son las causas probables; no medí cuánto aporta cada una. A favor de las ramas, no dependen de que un tablero individual sea corto: el tablero 3, que limita a la versión por tableros, se reparte entre varios procesos. El híbrido combina ambas ideas y, con grupos de 5, quedó como la mejor medición, aunque la diferencia con tableros esté dentro del ruido. Los grupos de 2 fueron los peores (29,987 s): con un coordinador por grupo y solo un proceso explorando, la mitad de los procesos no aporta búsqueda útil.