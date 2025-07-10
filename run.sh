. .venv/bin/activate

export FLASK_RUN_CERT=cert.pem
export FLASK_RUN_KEY=key.pem
flask run --host 0.0.0.0 --port 8443 --debug
