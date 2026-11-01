"""Tarea 2: tableros en orden; las ramas de cada tablero en paralelo."""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mpi4py import MPI

from baseline_secuencial import leer_seeds
from ramas_comun import TAG_FIN, coordinar_ramas, trabajar_ramas
from sudoku import resolver_con_tiempo


def main():
    comm = MPI.COMM_WORLD
    parser = argparse.ArgumentParser()
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
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

    if comm.Get_size() == 1:
        for nombre in seleccionados:
            r, s = resolver_con_tiempo([f[:] for f in seeds[nombre]])
            print(f"\nID: {nombre}\n{'Resuelto' if r else 'Sin solución'}\nTiempo: {s:.6f} segundos")
        return

    comm.Barrier()
    if comm.Get_rank() != 0:
        trabajar_ramas(comm, MPI)
        return

    inicio = MPI.Wtime()
    resueltos = 0
    for epoca, nombre in enumerate(seleccionados):
        t0 = MPI.Wtime()
        ok, _solucion = coordinar_ramas(comm, MPI, seeds[nombre], epoca)
        dt = MPI.Wtime() - t0
        resueltos += ok
        etiqueta = "Tiempo" if args.id else "Tiempo parcial"
        print(f"\nID: {nombre}\n{'Resuelto' if ok else 'Sin solución'}\n{etiqueta}: {dt:.6f} segundos",
              flush=True)
    total = MPI.Wtime() - inicio
    for w in range(1, comm.Get_size()):
        comm.send(None, dest=w, tag=TAG_FIN)
    if not args.id:
        print(f"\nTiempo total (reloj real): {total:.6f} segundos")
        print(f"IDs procesados: {len(seleccionados)}; resueltos: {resueltos}", flush=True)


if __name__ == "__main__":
    main()
