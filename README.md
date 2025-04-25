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

```

### Verificar internamente los datos en el sqlite
```sh
$ sqlite3 db/expend_local.db
$ .tables # ver listado de tablas generadas
$ .schema table_name # ver estructura de una tabla
```