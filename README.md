# expend-machine-procesor

### Inicializar el proyecto localmente
```sh
$ python3 -m venv .venv
$ . .venv/bin/activate

## Para todo lo fundamenta
$ pip3 install -r ./requirements.txt

## Para ejecutarlo desde rasperry 
$ pip3 install -r ./requirements-pi.txt

## Inicializar la base de datos
$ python3 db/init_db.py # se debe ejecuta asi, para que te genere en la carpeta raiz, desde donde se ejecuta python, no aplicar 'cd' para ingresar a la carpeta
```


### Ejecutar el proyecto
```sh
$ flask run --host=0.0.0.0 --port 5001 --debug 

# tb podemos ejecutar el run.sh que se encuentra en la consola, es lo mismo
$ bash run.sh

```

### Verificar internamente los datos en el sqlite
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

Table slot_config {
  id INTEGER [pk, increment]
  slot_num INTEGER [unique]
  fila INTEGER
  columna INTEGER
}

Table slots {
  id INTEGER [pk, increment]
  maquina_id TEXT
  slot_num INTEGER
  producto_id INTEGER [ref: > productos.id]
  stock INTEGER
  stock_minimo INTEGER
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
  estado TEXT [default: 'pendiente']
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

```


### Seeders
```sh
python3 db/seeders/slot_config_seed.py
```