"""Análisis completo de SQPC sin abrir la app (lo mismo que el botón "Todo"), para la tarea programada.

Usa la configuración guardada de la app (config.json: ligas, Libertadores, BetPlay, NBA, e-sports...), descarga datos,
predice los próximos partidos y registra los picks. Al final publica en easygoldglitch.com.
Salida en analisis_goldglitch.log.
"""
from __future__ import annotations

import logging
import multiprocessing
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    os.chdir(HERE)
    sys.path.insert(0, HERE)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s", stream=sys.stdout)
    from sqpc.gui.app import Api

    api = Api()
    api._publish_web = lambda: None          # se publica una sola vez al final, esperando a que termine
    t0 = time.time()
    api._run("all")
    err = api._job.get("error")
    print(f"análisis {'con error: ' + err if err else 'completado'} en {(time.time() - t0) / 60:.0f} min", flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, "goldglitch_sync.py")], cwd=HERE)
    print(f"publicación: código {r.returncode}", flush=True)
    return 1 if err else r.returncode


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
