"""Tarea 1: cada ID es una tarea. El rank 0 reparte IDs bajo demanda."""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mpi4py import MPI

from baseline_secuencial import leer_seeds
from ramas_comun import esperar_mensaje
from sudoku import resolver_con_tiempo

TAG_TAREA, TAG_RESULTADO = 1, 2


def trabajador(comm, seeds):
    while True:
        nombre = comm.recv(source=0, tag=TAG_TAREA)
        if nombre is None:
            return
        tablero = [fila[:] for fila in seeds[nombre]]
        resuelto, segundos = resolver_con_tiempo(tablero)
        comm.send((nombre, resuelto, segundos, comm.Get_rank()), dest=0, tag=TAG_RESULTADO)


def coordinador(comm, seleccionados, mostrar_rank):
    n_trab = comm.Get_size() - 1
    pendientes = list(seleccionados)
    resultados = {}
    activos = 0
    suma_parciales = 0.0

    inicio = MPI.Wtime()
    for w in range(1, n_trab + 1):  # un tablero inicial por trabajador
        if pendientes:
            comm.send(pendientes.pop(0), dest=w, tag=TAG_TAREA)
            activos += 1
        else:
            comm.send(None, dest=w, tag=TAG_TAREA)

    while activos:
        (nombre, resuelto, segundos, rank), w = esperar_mensaje(comm, MPI.ANY_SOURCE, TAG_RESULTADO, MPI)
        resultados[nombre] = resuelto
        suma_parciales += segundos
        extra = f" (proceso {rank})" if mostrar_rank else ""
        print(f"\nID: {nombre}{extra}\n{'Resuelto' if resuelto else 'Sin solución'}\n"
              f"Tiempo parcial: {segundos:.6f} segundos", flush=True)
        if pendientes:
            comm.send(pendientes.pop(0), dest=w, tag=TAG_TAREA)
        else:
            comm.send(None, dest=w, tag=TAG_TAREA)
            activos -= 1
    total = MPI.Wtime() - inicio

    print(f"\nTiempo total (reloj real): {total:.6f} segundos")
    print(f"Suma de tiempos parciales (informativa, no es el total): {suma_parciales:.6f} s")
    print(f"IDs procesados: {len(resultados)} de {len(seleccionados)}; "
          f"resueltos: {sum(resultados.values())}", flush=True)
    return len(resultados) == len(seleccionados)


def main():
    comm = MPI.COMM_WORLD
    parser = argparse.ArgumentParser()
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
    sel = parser.add_mutually_exclusive_group()
    sel.add_argument("--id", dest="id")
    sel.add_argument("--all", action="store_true")
    parser.add_argument("--mostrar-rank", action="store_true")
    args = parser.parse_args()

    seeds = leer_seeds(args.archivo)
    if args.id:
        if args.id not in seeds:
            sys.exit(f"ID '{args.id}' no existe.")
        seleccionados = [args.id]
    else:
        seleccionados = list(seeds)

    if comm.Get_size() == 1:  # sin trabajadores: se resuelve en el mismo proceso
        inicio = MPI.Wtime()
        for nombre in seleccionados:
            r, s = resolver_con_tiempo([f[:] for f in seeds[nombre]])
            print(f"\nID: {nombre}\n{'Resuelto' if r else 'Sin solución'}\nTiempo parcial: {s:.6f} segundos")
        print(f"\nTiempo total (reloj real): {MPI.Wtime() - inicio:.6f} segundos")
        return

    comm.Barrier()
    if comm.Get_rank() == 0:
        coordinador(comm, seleccionados, args.mostrar_rank)
    else:
        trabajador(comm, seeds)


if __name__ == "__main__":
    main()
