# expend-machine-procesor

### IMPORTANTE! al inicializar el proyecto en el raspberry
```sh
$ ## Generar la carpeta en el raspberry y luego clonar el repo
mkdir /home/rasp/automatica-vending
```


### Inicializar el proyecto localmente
```sh
$ python3 -m venv .venv
$ . .venv/bin/activate

## Para todo lo fundamenta
$ pip3 install -r ./requirements.txt

## Para ejecutarlo desde rasperry 
$ pip3 install -r ./requirements-pi.txt

## Aplicar migraciones manualmente (tambien se aplican solas al iniciar la app)
$ flask init-db
```

### Base de datos local y migraciones
- La base sqlite queda en `DATABASE_PATH` (por defecto `db/expend_local.db`, ignorada por git).
- Al iniciar la app se aplican solo las migraciones pendientes de `database/migrations/*.sql`
  (quedan registradas en la tabla `schema_migrations`, las ya aplicadas no se tocan).
- Para cambiar el esquema agregar un archivo nuevo, ej. `0003_descripcion.sql`. No editar los ya aplicados.

### Stock local
El stock vive en la maquina (tabla `stock_slots`). Cada `STOCK_SYNC_INTERVAL` segundos:
1. **pull** `GET {API_URL}/maquinas/{MACHINE_ID}/stock-sync`: actualiza producto, precio y fila/columna
   de cada slot y aplica las reposiciones pendientes (tipo `R` suma, tipo `A` ajusta el stock al valor).
   El stock remoto solo se toma la primera vez que aparece un slot.
2. **push** `PUT {API_URL}/maquinas/{MACHINE_ID}/stock-sync`: envia el stock local y confirma las reposiciones aplicadas.

Sin conexion se sigue vendiendo con el stock local y se reintenta en el proximo ciclo.

### Configuracion GPIO (fila/columna)
La fila/columna de cada slot (pines BCM de los reles) se configura en el admin
(Maquina -> Configuracion) y la maquina la descarga en cada sync, igual que producto y precio.
- `GET /slots/config` configuracion descargada de todos los slots
- `GET /slots/<slot_num>` prueba el slot con esa configuracion (sin ir a la api)
- `GET /slots/<fila>/<columna>` prueba directa de un par de pines

En el kiosko: menu "Configuración GPIO" (ver, sincronizar ahora y probar).

### Ventas locales
La venta se registra y ejecuta completa en la maquina (tabla `ventas_locales`), sin llamar a la api:
1. `POST /vending/ {slot_num}` valida stock/producto/precio locales y crea la venta `P`.
2. `PATCH /vending/<id>/<qr|ux>` reserva el stock (estado `E`), cobra con el POS, despacha,
   descuenta el stock local y deja la venta `A` (o `R` si el pago falla).
3. El sync sube las ventas terminadas a `POST {API_URL}/maquinas/{MACHINE_ID}/ventas-sync`
   (idempotente por `uuid`). Ventas `P`/`E` sin terminar en 15 min pasan a `C`.

El sync no bloquea: corre en su propio hilo, las llamadas http van fuera de transacciones y
`POST /stock/sync` responde `{"en_curso": true}` si ya hay uno corriendo. Tras cada venta se
pide un sync inmediato en segundo plano. `GET /vending/` lista las ultimas ventas locales.

Variables nuevas en `env.py` (opcionales):
```py
DATABASE_PATH = "db/expend_local.db"
STOCK_SYNC_INTERVAL = 60  # segundos, 0 deshabilita el sync
```

Endpoints:
- `GET /stock/` stock local de todos los slots
- `GET /stock/<slot_num>` stock local de un slot
- `POST /stock/sync` fuerza un ciclo de sincronizacion (ventas + stock)

### Probar localmente (stock + sync + migraciones)
Levanta MySQL (docker), `expend-api-node` (node), un POS falso y el processor con una configuracion
de prueba (`scripts/local_test/test_env.py`, no toca `env.py`), corre los escenarios y baja todo.
Requiere docker, node y `npm install` en `../expend-api-node/app`.
```sh
$ .venv/bin/python scripts/local_test/e2e_stock.py          # corre las verificaciones
$ .venv/bin/python scripts/local_test/e2e_stock.py --keep   # y deja todo levantado para probar a mano
$ .venv/bin/python scripts/local_test/e2e_stock.py --serve  # solo levanta el entorno con datos de demo (sin verificaciones)

# solo el processor contra otra api (variables TEST_API_URL, TEST_MACHINE_ID, TEST_POS_URL...)
$ TEST_API_URL=http://localhost:8000 .venv/bin/python scripts/local_test/run_processor.py 5001
```

### Ejecutar el proyecto
```sh
$ flask run --host=0.0.0.0 --port 5001 --debug 

# tb podemos ejecutar el run.sh que se encuentra en la consola, es lo mismo
$ bash run.sh

```

### Verificar internamente los datos en el sqlitea
```sh
$ sqlite3 db/expend_local.db
$ .tables # ver listado de tablas generadas
$ .schema table_name # ver estructura de una tabla
```


### Docs
[db diagram](https://dbdiagram.io/d/evending-local-db-68559a7cf039ec6d362f6303)

```js
Table productos {
  id INTEGER [pk, increment]
  nombre TEXT
}

Table maquinas {
  id INTEGER [pk, increment] 
  uuid TEXT [uk]
  local_id INTEGER
}

Table slot_config {
  id INTEGER [pk, increment]
  slot_num INTEGER 
  fila INTEGER
  columna INTEGER
  activo BOOLEAN [default: true]
}

Table slots { // podemos moverlo y tomarlo como opciones
  id INTEGER [pk, increment]
  maquina_id TEXT
  slot_num INTEGER
  producto_id INTEGER [ref: > productos.id]
  stock INTEGER
  stock_minimo INTEGER
  stock_inicial INTEGER
  precio REAL
  precio_oferta REAL
  fecha_actualizacion TIMESTAMP
}

Table ventas {
  id INTEGER [pk, increment]
  slot_id INTEGER [ref: > slots.id]
  producto_id INTEGER [ref: > productos.id]
  maquina_id TEXT
  precio_venta REAL
  fecha TIMESTAMP
  estado TEXT [default: 'P']
  metodo_pago TEXT
  notas TEXT
}

// no implementado
Table usuarios {
  id INTEGER [pk, increment]
  username TEXT [unique]
  password_hash TEXT
  rol TEXT [default: 'user']
}


## Info
```sh
Ver paquetes instalados de python en .venv
pip show requests

Ver todos los pquetes instalados en env
pip list
```
