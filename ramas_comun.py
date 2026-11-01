"""Utilidades compartidas por mpi_por_ramas y mpi_hibrido.

- generar_ramas: divide un tablero en subproblemas (ramas) independientes.
- resolver_cancelable: backtracking que consulta cada cierto tiempo si debe parar.
- coordinar_ramas / trabajar_ramas: protocolo coordinador-trabajadores sobre un
  comunicador cualquiera (rank 0 coordina, el resto explora ramas).
"""

import time

from sudoku import puede_colocar

TAG_TAREA = 1      # coordinador -> trabajador: (epoca, id_rama, tablero)
TAG_RESULTADO = 2  # trabajador -> coordinador: (epoca, id_rama, estado, tablero)
TAG_PARAR = 3      # coordinador -> trabajador: epoca a cancelar
TAG_FIN = 4        # coordinador -> trabajador: no hay mas trabajo

RESUELTO, SIN_SOLUCION, CANCELADO = "resuelto", "sin_solucion", "cancelado"


class Cancelado(Exception):
    pass


def siguiente_vacia(tablero):
    for f in range(9):
        for c in range(9):
            if tablero[f][c] == 0:
                return f, c
    return None


def generar_ramas(tablero, minimo):
    """Expande la primera casilla vacia de cada rama parcial hasta tener
    al menos `minimo` ramas. Conserva el orden DFS del algoritmo serial
    (valores 1..9), de modo que las primeras ramas son las que el serial
    exploraria primero. Si el tablero se resuelve solo con ramas (sin
    vacias), esas ramas ya son soluciones completas."""
    ramas = [[fila[:] for fila in tablero]]
    while len(ramas) < minimo:
        nuevas = []
        expandio = False
        for rama in ramas:
            pos = siguiente_vacia(rama)
            if pos is None:
                nuevas.append(rama)
                continue
            expandio = True
            f, c = pos
            for valor in range(1, 10):
                if puede_colocar(rama, f, c, valor):
                    hija = [fila[:] for fila in rama]
                    hija[f][c] = valor
                    nuevas.append(hija)
        ramas = nuevas
        if not expandio or not ramas:
            break
    return ramas


def resolver_cancelable(tablero, debe_parar, cada=2000):
    """Backtracking igual al de sudoku.resolver, pero cada `cada` nodos llama
    a debe_parar(); si devuelve True lanza Cancelado."""
    contador = [0]

    def buscar():
        pos = siguiente_vacia(tablero)
        if pos is None:
            return True
        f, c = pos
        for valor in range(1, 10):
            if puede_colocar(tablero, f, c, valor):
                tablero[f][c] = valor
                contador[0] += 1
                if contador[0] % cada == 0 and debe_parar():
                    raise Cancelado()
                if buscar():
                    return True
                tablero[f][c] = 0
        return False

    return buscar()


def esperar_mensaje(comm, source, tag, MPI, pausa=0.0005):
    """Recepcion que duerme entre sondeos para no ocupar un nucleo mientras el
    coordinador espera (OpenMPI hace espera activa en recv bloqueante)."""
    status = MPI.Status()
    while not comm.Iprobe(source=source, tag=tag, status=status):
        time.sleep(pausa)
    return comm.recv(source=status.Get_source(), tag=status.Get_tag()), status.Get_source()


def trabajar_ramas(comm, MPI):
    """Bucle de un trabajador (rank != 0 de `comm`). Termina al recibir TAG_FIN."""
    epoca_actual = [-1]
    status = MPI.Status()

    def debe_parar():
        while comm.Iprobe(source=0, tag=TAG_PARAR):
            if comm.recv(source=0, tag=TAG_PARAR) == epoca_actual[0]:
                return True
        return False

    while True:
        comm.Probe(source=0, tag=MPI.ANY_TAG, status=status)
        tag = status.Get_tag()
        if tag == TAG_FIN:
            comm.recv(source=0, tag=TAG_FIN)
            return
        if tag == TAG_PARAR:  # parada atrasada de una epoca ya cerrada
            comm.recv(source=0, tag=TAG_PARAR)
            continue
        epoca, id_rama, rama = comm.recv(source=0, tag=TAG_TAREA)
        epoca_actual[0] = epoca
        try:
            ok = resolver_cancelable(rama, debe_parar)
            estado = RESUELTO if ok else SIN_SOLUCION
        except Cancelado:
            estado = CANCELADO
        comm.send((epoca, id_rama, estado, rama if estado == RESUELTO else None),
                  dest=0, tag=TAG_RESULTADO)


def coordinar_ramas(comm, MPI, tablero, epoca, factor=4):
    """Coordinador (rank 0 de `comm`). Resuelve `tablero` repartiendo sus ramas
    entre los trabajadores (ranks 1..size-1). Devuelve (resuelto, solucion).
    No retorna hasta que todos los trabajadores contestaron por esta epoca."""
    trabajadores = comm.Get_size() - 1
    ramas = generar_ramas(tablero, max(8, factor * trabajadores))
    pendientes = list(range(len(ramas)))  # se reparten en orden DFS
    libres = list(range(1, trabajadores + 1))
    ocupados = set()
    solucion = None
    cancelando = False

    while pendientes or ocupados:
        # Asignar mientras haya trabajo y trabajadores libres.
        while libres and pendientes and not cancelando:
            w = libres.pop(0)
            i = pendientes.pop(0)
            comm.send((epoca, i, ramas[i]), dest=w, tag=TAG_TAREA)
            ocupados.add(w)
        if not ocupados:
            break
        (ep, _id, estado, sol), w = esperar_mensaje(comm, MPI.ANY_SOURCE, TAG_RESULTADO, MPI)
        ocupados.discard(w)
        libres.append(w)
        if estado == RESUELTO and solucion is None:
            solucion = sol
            cancelando = True
            for otro in ocupados:
                comm.send(epoca, dest=otro, tag=TAG_PARAR)
    return solucion is not None, solucion
