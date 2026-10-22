"""Prueba local de punta a punta del stock local + sync + migraciones.

Levanta: MySQL (docker), expend-api-node (node), un POS falso y el processor.
Corre los escenarios con verificaciones y al final baja todo (o lo deja levantado con --keep).

    .venv/bin/python scripts/local_test/e2e_stock.py            # corre los escenarios
    .venv/bin/python scripts/local_test/e2e_stock.py --keep     # y deja todo levantado para probar a mano

Requisitos: docker, node y `npm install` en ../expend-api-node/app
"""
import argparse
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA_DIR = os.path.join(HERE, ".data")

MYSQL_CONTAINER = "expend-local-test-mysql"
MYSQL_PORT = 33306
MYSQL_PASSWORD = "test"
API_PORT = 5099
POS_PORT = 5098
PROCESSOR_PORT = 5097
MACHINE_ID = "maquina-test"
SYNC_INTERVAL = 2

API = f"http://localhost:{API_PORT}"
PROC = f"http://localhost:{PROCESSOR_PORT}"
PROCESSOR_DB = os.path.join(DATA_DIR, "processor.db")
API_DIR = None

processes = []
pos_calls = []
pos_delay = {"seconds": 0}  # simula un cliente que tarda en pagar
results = []


# ---------------------------------------------------------------- utilidades

def log(msg):
    print(f"\033[36m==>\033[0m {msg}", flush=True)


def check(name, condition, detail=""):
    results.append((name, bool(condition)))
    mark = "\033[32mPASS\033[0m" if condition else "\033[31mFAIL\033[0m"
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail and not condition else ""), flush=True)


def mysql(sql):
    out = subprocess.run(
        ["docker", "exec", MYSQL_CONTAINER, "mysql", "-uroot", f"-p{MYSQL_PASSWORD}",
         "-N", "-B", "expend_db", "-e", sql],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    return [line.split("\t") for line in out.stdout.strip().splitlines() if line]


def local_db(sql, params=()):
    with sqlite3.connect(PROCESSOR_DB) as conn:
        return conn.execute(sql, params).fetchall()


def wait_http(url, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        try:
            requests.get(url, timeout=2)
            return
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    raise RuntimeError(f"{url} no respondio en {timeout}s")


def local_stock(slot_num):
    return requests.get(f"{PROC}/stock/{slot_num}", timeout=5).json()["stock"]


def remote_stock(slot_num):
    return int(mysql(f"SELECT stock FROM slots WHERE maquina_id='{MACHINE_ID}' AND slot_num={slot_num}")[0][0])


def sync():
    return requests.post(f"{PROC}/stock/sync", timeout=20)


def crear_venta(slot_num):
    """La venta se registra en la maquina (como lo hace el kiosko)."""
    res = requests.post(f"{PROC}/vending/", json={"slot_num": slot_num}, timeout=10)
    return res.json()


def pagar(venta_id, metodo="qr"):
    return requests.patch(f"{PROC}/vending/{venta_id}/{metodo}", timeout=30).json()


def ventas_api(where="1=1"):
    return mysql(f"SELECT uuid, estado, metodo_pago, precio_venta FROM ventas WHERE maquina_id='{MACHINE_ID}' AND {where} ORDER BY id")


# ---------------------------------------------------------------- servicios

class FakePos(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        pos_calls.append((self.path, json.loads(body or b"{}")))
        time.sleep(pos_delay["seconds"])
        payload = {"nsu": "123", "bin": "456"} if self.path.endswith("venta-ux") else {"ok": True}
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *args):
        pass


def start_mysql():
    log("Levantando MySQL en docker")
    subprocess.run(["docker", "rm", "-f", MYSQL_CONTAINER], capture_output=True)
    subprocess.run(
        ["docker", "run", "-d", "--rm", "--name", MYSQL_CONTAINER,
         "-e", f"MYSQL_ROOT_PASSWORD={MYSQL_PASSWORD}", "-e", "MYSQL_DATABASE=expend_db",
         "-p", f"{MYSQL_PORT}:3306", "mysql:8"],
        check=True, capture_output=True,
    )
    for _ in range(60):
        ok = subprocess.run(
            ["docker", "exec", MYSQL_CONTAINER, "mysql", "-uroot", f"-p{MYSQL_PASSWORD}",
             "-e", "SELECT 1", "expend_db"],
            capture_output=True,
        )
        if ok.returncode == 0:
            return
        time.sleep(2)
    raise RuntimeError("MySQL no levanto")


def start_api(api_dir):
    log("Levantando expend-api-node (aplica migraciones al iniciar)")
    env = {
        **os.environ,
        "DB_ENGINE": "mysql", "DB_HOST": "127.0.0.1", "DB_PORT": str(MYSQL_PORT),
        "DB_USERNAME": "root", "DB_PASSWORD": MYSQL_PASSWORD, "DB_NAME": "expend_db",
        "PORT": str(API_PORT), "JWT_SECRET": "test",
    }
    logf = open(os.path.join(DATA_DIR, "api.log"), "a")
    processes.append(subprocess.Popen(["node", "src/main.js"], cwd=api_dir, env=env, stdout=logf, stderr=logf))
    wait_http(API)


def start_processor():
    log("Levantando el processor (aplica migraciones sqlite y arranca el sync)")
    env = {
        **os.environ,
        "TEST_API_URL": API, "TEST_MACHINE_ID": MACHINE_ID,
        "TEST_POS_URL": f"http://localhost:{POS_PORT}",
        "TEST_DATABASE_PATH": PROCESSOR_DB, "TEST_STOCK_SYNC_INTERVAL": str(SYNC_INTERVAL),
    }
    logf = open(os.path.join(DATA_DIR, "processor.log"), "a")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "run_processor.py"), str(PROCESSOR_PORT)],
        env=env, stdout=logf, stderr=logf,
    )
    processes.append(proc)
    wait_http(PROC)
    return proc


def seed():
    log("Cargando maquina, producto y slots de prueba")
    mysql(f"""
        INSERT INTO productos (id, nombre, precio) VALUES (1, 'Coca Cola', 5000);
        INSERT INTO maquinas (uuid, etiqueta, cantidad_slot) VALUES ('{MACHINE_ID}', 'Test', 2);
        INSERT INTO slots (maquina_id, slot_num, producto_id, stock, stock_minimo, precio, precio_oferta)
        VALUES ('{MACHINE_ID}', 1, 1, 3, 1, 5000, 0), ('{MACHINE_ID}', 2, 1, 0, 1, 7000, 0);
        INSERT INTO slot_config (slot_num, fila, columna, maquina_id)
        VALUES (1, 17, 12, '{MACHINE_ID}'), (2, 17, 16, '{MACHINE_ID}');
    """)


def teardown():
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
    subprocess.run(["docker", "rm", "-f", MYSQL_CONTAINER], capture_output=True)


# ---------------------------------------------------------------- escenarios

def seed_demo():
    """Datos mas completos para probar a mano (modo --serve)."""
    log("Cargando datos de demo")
    mysql(f"""
        INSERT INTO productos (id, nombre, precio) VALUES
            (2, 'Agua Mineral 500ml', 4000), (3, 'Papas Fritas', 6000), (4, 'Chocolate', 3500);
        UPDATE slots SET stock_inicial = 10, stock_minimo = 3 WHERE maquina_id = '{MACHINE_ID}';
        INSERT INTO slots (maquina_id, slot_num, producto_id, stock, stock_minimo, stock_inicial, precio, precio_oferta)
        VALUES ('{MACHINE_ID}', 3, 2, 8, 2, 8, 4000, 0),
               ('{MACHINE_ID}', 4, 3, 1, 2, 6, 6000, 0),
               ('{MACHINE_ID}', 5, 4, 12, 3, 12, 3500, 3000),
               ('{MACHINE_ID}', 6, NULL, 0, 0, 0, 0, 0);
        INSERT INTO slot_config (slot_num, fila, columna, maquina_id)
        VALUES (3, 17, 4, '{MACHINE_ID}'), (4, 17, 5, '{MACHINE_ID}'),
               (5, 17, 6, '{MACHINE_ID}'), (6, 17, 13, '{MACHINE_ID}');
        UPDATE maquinas SET etiqueta = 'Maquina de prueba', cantidad_slot = 6 WHERE uuid = '{MACHINE_ID}';
    """)


def escenarios():
    log("1. Migraciones")
    applied = mysql("SELECT name FROM schema_migrations ORDER BY name")
    check("api: migraciones aplicadas sobre base vacia", len(applied) >= 2, applied)
    check("api: tabla reposiciones creada", mysql("SHOW TABLES LIKE 'reposiciones'"))
    local_applied = local_db("SELECT name FROM schema_migrations")
    check("processor: migraciones sqlite aplicadas", len(local_applied) >= 2, local_applied)

    log("2. Carga inicial: el processor toma el stock remoto la primera vez")
    sync()
    check("slot 1 local = 3", local_stock(1) == 3, local_stock(1))
    check("slot 2 local = 0", local_stock(2) == 0, local_stock(2))

    log("3. Reposicion desde la api (pull)")
    rep = requests.post(f"{API}/slots/2/reposiciones", json={"cantidad": 5}, timeout=5).json()
    check("reposicion creada pendiente", rep.get("estado") == "P", rep)
    sync()
    check("slot 2 local = 5", local_stock(2) == 5, local_stock(2))
    estado = mysql(f"SELECT estado, stock_resultante FROM reposiciones WHERE id={rep['id']}")[0]
    check("reposicion confirmada en la api", estado == ["A", "5"], estado)
    check("stock remoto actualizado por el push", remote_stock(2) == 5, remote_stock(2))

    log("4. Idempotencia: sincronizar de nuevo no reaplica la reposicion")
    sync()
    sync()
    check("slot 2 local sigue en 5", local_stock(2) == 5, local_stock(2))

    log("5. Venta en la maquina (QR): no usa la api y se sincroniza despues")
    venta = crear_venta(1)
    check("venta creada en la maquina", venta.get("estado") == "P" and venta.get("uuid"), venta)
    check("precio_oferta 0 no se usa como precio", float(venta.get("precio_venta", 0)) == 5000, venta)
    calls_before = len(pos_calls)
    res = pagar(venta["id"], "qr")
    check("venta aceptada", res.get("estado") == "A", res)
    check("POS llamado", len(pos_calls) == calls_before + 1)
    check("slot 1 local = 2", local_stock(1) == 2, local_stock(1))
    sync()
    check("venta subida a la api", ventas_api(f"uuid='{venta['uuid']}'") == [[venta["uuid"], "A", "qr", "5000"]],
          ventas_api())
    check("stock remoto slot 1 = 2 tras el push", remote_stock(1) == 2, remote_stock(1))
    sync()
    check("reenviar no duplica la venta", len(ventas_api(f"uuid='{venta['uuid']}'")) == 1)

    log("6. Venta con tarjeta (UX)")
    venta = crear_venta(2)
    res = pagar(venta["id"], "ux")
    check("venta con tarjeta aceptada", res.get("estado") == "A", res)
    check("slot 2 local = 4", local_stock(2) == 4, local_stock(2))
    res = pagar(venta["id"], "ux")
    check("pagar dos veces la misma venta se rechaza", res.get("bancard_status") == 409, res)

    log("7. Ajuste desde el admin (PATCH /slots/:id con stock)")
    slot_id = mysql(f"SELECT id FROM slots WHERE maquina_id='{MACHINE_ID}' AND slot_num=1")[0][0]
    requests.patch(f"{API}/slots/{slot_id}", json={"precio": 6000, "stock": 10}, timeout=5)
    check("ajuste tipo A pendiente creado",
          mysql("SELECT COUNT(*) FROM reposiciones WHERE tipo='A' AND estado='P'")[0][0] == "1")
    sync()
    check("slot 1 local = 10", local_stock(1) == 10, local_stock(1))
    precio = requests.get(f"{PROC}/stock/1", timeout=5).json()["precio"]
    check("precio actualizado en local", precio == 6000, precio)

    log("7b. Cambio de producto en un slot: el stock pasa a 0 hasta que se llene")
    mysql("INSERT INTO productos (id, nombre, precio) VALUES (9, 'Agua', 4000)")
    requests.patch(f"{API}/slots/{slot_id}", json={"producto_id": 9, "precio": 4000}, timeout=5)
    nota = mysql("SELECT notas FROM reposiciones WHERE tipo='A' AND estado='P' ORDER BY id DESC LIMIT 1")
    check("ajuste a 0 por cambio de producto", nota and "Agua" in nota[0][0], nota)
    sync()
    slot = requests.get(f"{PROC}/stock/1", timeout=5).json()
    check("slot 1 local: producto nuevo y stock 0", slot["producto_id"] == 9 and slot["stock"] == 0, slot)
    requests.post(f"{API}/slots/{slot_id}/reposiciones", json={"cantidad": 10}, timeout=5)
    requests.patch(f"{API}/slots/{slot_id}", json={"producto_id": 1, "precio": 6000}, timeout=5)
    sync()
    check("volver al producto original tambien reinicia el stock", local_stock(1) == 0, local_stock(1))
    requests.post(f"{API}/slots/{slot_id}/reposiciones", json={"cantidad": 10}, timeout=5)
    sync()
    check("llenado despues del cambio", local_stock(1) == 10, local_stock(1))

    log("7c. GPIO configurado en el admin: la maquina lo descarga (pull)")
    slot2_id = mysql(f"SELECT id FROM slots WHERE maquina_id='{MACHINE_ID}' AND slot_num=2")[0][0]
    res = requests.patch(f"{API}/slots/{slot2_id}/config", json={"fila": 1, "columna": 99}, timeout=5)
    check("pin invalido se rechaza", res.status_code == 400, res.text)
    res = requests.patch(f"{API}/slots/{slot2_id}/config", json={"fila": 22, "columna": 22}, timeout=5)
    check("fila y columna iguales se rechaza", res.status_code == 400, res.text)
    res = requests.patch(f"{API}/slots/{slot2_id}/config", json={"fila": 22, "columna": 23}, timeout=5)
    check("GPIO guardado en la api", res.status_code == 200, res.text)
    sync()
    res = requests.get(f"{PROC}/slots/2", timeout=10).json()
    check("la maquina descarga el GPIO y la prueba lo usa", (res.get("fila"), res.get("columna")) == (22, 23), res)
    sync()
    cfg = mysql(f"SELECT fila, columna FROM slot_config WHERE maquina_id='{MACHINE_ID}' AND slot_num=2")
    check("el sync no modifica el GPIO de la api", cfg == [["22", "23"]], cfg)

    log("8. Sin stock local: no se registra ni se cobra")
    local_db("UPDATE stock_slots SET stock = 0 WHERE slot_num = 2")
    calls_before = len(pos_calls)
    res = requests.post(f"{PROC}/vending/", json={"slot_num": 2}, timeout=10)
    check("POST /vending/ rechaza con 409", res.status_code == 409, res.text)
    check("POS NO llamado", len(pos_calls) == calls_before)

    log("9. Ultima unidad: dos ventas simultaneas no venden la misma unidad")
    local_db("UPDATE stock_slots SET stock = 1 WHERE slot_num = 2")
    v1, v2 = crear_venta(2), crear_venta(2)
    pos_delay["seconds"] = 3
    hilo = threading.Thread(target=lambda: results_v1.append(pagar(v1["id"])))
    results_v1 = []
    hilo.start()
    time.sleep(0.5)
    res = pagar(v2["id"])
    check("segunda venta rechazada por stock reservado", res.get("bancard_status") == 409, res)

    log("10. El sync no bloquea otros requests mientras hay un cobro en curso")
    t0 = time.time()
    ok_stock = requests.get(f"{PROC}/stock/", timeout=5).status_code == 200
    ok_sync = sync().status_code == 200
    elapsed = time.time() - t0
    check("GET /stock y POST /stock/sync responden durante el cobro", ok_stock and ok_sync and elapsed < 2,
          f"{elapsed:.2f}s")
    hilo.join()
    pos_delay["seconds"] = 0
    check("la primera venta se completo", results_v1 and results_v1[0].get("estado") == "A", results_v1)
    check("slot 2 local = 0", local_stock(2) == 0, local_stock(2))

    log("11. Sin conexion con la api: se sigue vendiendo y luego se sincroniza")
    api_proc = processes.pop(0)
    api_proc.terminate()
    api_proc.wait()
    check("GET /stock sigue funcionando", requests.get(f"{PROC}/stock/", timeout=5).status_code == 200)
    res = requests.get(f"{PROC}/slots/1", timeout=10)
    check("GET /slots/1 usa fila/columna local", res.status_code == 200 and res.json().get("fila") == 17, res.text)
    venta = crear_venta(1)
    res = pagar(venta["id"], "qr")
    check("venta aceptada sin api", res.get("estado") == "A", res)
    res = sync()
    check("POST /stock/sync sin api: 502, o en curso sin esperar",
          res.status_code == 502 or res.json().get("en_curso"), res.text)
    start_api(API_DIR)
    sync()
    check("venta offline subida al volver la api", len(ventas_api(f"uuid='{venta['uuid']}'")) == 1, ventas_api())
    check("stock remoto slot 1 = 9", remote_stock(1) == 9, remote_stock(1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="deja todo levantado al terminar")
    parser.add_argument("--serve", action="store_true",
                        help="solo levanta el entorno con datos de demo, sin correr las verificaciones")
    parser.add_argument("--api-dir", default=os.path.join(ROOT, "..", "expend-api-node", "app"))
    args = parser.parse_args()

    global API_DIR
    api_dir = API_DIR = os.path.abspath(args.api_dir)
    if not os.path.isdir(os.path.join(api_dir, "node_modules")):
        sys.exit(f"Falta node_modules en {api_dir}: ejecutar `npm install` ahi primero")

    shutil.rmtree(DATA_DIR, ignore_errors=True)
    os.makedirs(DATA_DIR)

    # `kill <pid>` tambien baja todo (ademas de Ctrl+C)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))

    pos = ThreadingHTTPServer(("127.0.0.1", POS_PORT), FakePos)
    threading.Thread(target=pos.serve_forever, daemon=True).start()

    try:
        start_mysql()
        start_api(api_dir)
        seed()
        if args.serve:
            seed_demo()
        start_processor()
        if not args.serve:
            escenarios()

        if args.keep or args.serve:
            print(f"""
Todo levantado (Ctrl+C para bajar):
  API        {API}
  Processor  {PROC}   (GET /stock/, POST /stock/sync)
  POS falso  http://localhost:{POS_PORT}
  MySQL      docker exec -it {MYSQL_CONTAINER} mysql -uroot -p{MYSQL_PASSWORD} expend_db
  SQLite     sqlite3 {PROCESSOR_DB}
  Logs       {DATA_DIR}/api.log, processor.log

Frontends (en otra terminal):
  vending-admin-front:  npm run start:local  -> http://localhost:8100
                        cookie de sesion: document.cookie = "token=test; path=/"
  expend-local-app:     npm run start:local  -> http://localhost:8101/maquina-local
                        MAQUINA_ID = {MACHINE_ID}
                        MACHINE_HOST = {PROC}
                        luego ir a http://localhost:8101/keyboard

Ejemplos:
  curl -X POST {API}/slots/1/reposiciones -H 'content-type: application/json' -d '{{"cantidad": 3}}'
  curl -X POST {PROC}/stock/sync
  curl {PROC}/stock/
""", flush=True)
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        teardown()
        pos.shutdown()

    failed = [name for name, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} verificaciones OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
