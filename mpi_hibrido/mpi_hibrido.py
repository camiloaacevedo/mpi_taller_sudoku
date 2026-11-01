"""Tarea 3: hibrido.

- Rank 0 (mundo): coordinador global, reparte IDs entre grupos bajo demanda.
- Los ranks 1..N-1 se dividen en grupos de tamano --grupo (el ultimo grupo
  absorbe el sobrante). En cada grupo, el rank 0 del grupo (lider) recibe un ID
  y reparte las ramas de ese tablero entre los demas miembros del grupo.
- Con --grupo 1 cada proceso resuelve tableros completos (equivale a la Tarea 1).
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mpi4py import MPI

from baseline_secuencial import leer_seeds
from ramas_comun import TAG_FIN, coordinar_ramas, esperar_mensaje, trabajar_ramas
from sudoku import resolver_con_tiempo

TAG_PIDE, TAG_ASIGNA = 10, 11


def coordinador_global(mundo, seleccionados, n_lideres):
    pendientes = list(seleccionados)
    activos = n_lideres
    resultados = {}
    suma_parciales = 0.0
    inicio = MPI.Wtime()
    while activos:
        (previo, ), lider = esperar_mensaje(mundo, MPI.ANY_SOURCE, TAG_PIDE, MPI)
        if previo is not None:
            nombre, ok, seg, grupo = previo
            resultados[nombre] = ok
            suma_parciales += seg
            print(f"\nID: {nombre} (grupo {grupo})\n{'Resuelto' if ok else 'Sin solución'}\n"
                  f"Tiempo parcial: {seg:.6f} segundos", flush=True)
        if pendientes:
            mundo.send(pendientes.pop(0), dest=lider, tag=TAG_ASIGNA)
        else:
            mundo.send(None, dest=lider, tag=TAG_ASIGNA)
            activos -= 1
    total = MPI.Wtime() - inicio
    print(f"\nTiempo total (reloj real): {total:.6f} segundos")
    print(f"Suma de tiempos parciales (informativa, no es el total): {suma_parciales:.6f} s")
    print(f"IDs procesados: {len(resultados)} de {len(seleccionados)}; "
          f"resueltos: {sum(resultados.values())}", flush=True)


def lider(mundo, grupo, seeds, id_grupo):
    previo = None
    epoca = 0
    while True:
        mundo.send((previo,), dest=0, tag=TAG_PIDE)
        nombre = mundo.recv(source=0, tag=TAG_ASIGNA)
        if nombre is None:
            for w in range(1, grupo.Get_size()):
                grupo.send(None, dest=w, tag=TAG_FIN)
            return
        t0 = MPI.Wtime()
        if grupo.Get_size() == 1:
            ok, _ = resolver_con_tiempo([f[:] for f in seeds[nombre]])
        else:
            ok, _ = coordinar_ramas(grupo, MPI, seeds[nombre], epoca)
        epoca += 1
        previo = (nombre, ok, MPI.Wtime() - t0, id_grupo)


def main():
    mundo = MPI.COMM_WORLD
    parser = argparse.ArgumentParser()
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
    parser.add_argument("--grupo", type=int, default=3,
                        help="procesos por grupo (1 lider + el resto explora ramas)")
    sel = parser.add_mutually_exclusive_group()
    sel.add_argument("--id", dest="id")
    sel.add_argument("--all", action="store_true")
    args = parser.parse_args()

    seeds = leer_seeds(args.archivo)
    if args.id:
        if args.id not in seeds:
            sys.exit(f"ID '{args.id}' no existe.")
        seleccionados = [args.id]
    else:
        seleccionados = list(seeds)

    n = mundo.Get_size()
    if n < 2:
        sys.exit("El híbrido necesita al menos 2 procesos (1 coordinador + 1 trabajador).")
    g = max(1, min(args.grupo, n - 1))
    n_grupos = (n - 1) // g
    rank = mundo.Get_rank()

    if rank == 0:
        color = MPI.UNDEFINED
    else:
        color = min((rank - 1) // g, n_grupos - 1)
    grupo = mundo.Split(color, rank)

    mundo.Barrier()
    if rank == 0:
        print(f"Procesos: {n} = 1 coordinador + {n_grupos} grupo(s) de tamaño {g}"
              f"{' (último con sobrante)' if (n - 1) % g else ''}", flush=True)
        coordinador_global(mundo, seleccionados, n_grupos)
    elif grupo.Get_rank() == 0:
        lider(mundo, grupo, seeds, color)
    else:
        trabajar_ramas(grupo, MPI)


if __name__ == "__main__":
    main()
