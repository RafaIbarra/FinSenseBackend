# gunicorn_conf.py
from uvicorn_worker import UvicornWorker


class ProxiedUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "proxy_headers": True,
        "forwarded_allow_ips": "127.0.0.1",
    }
# PARA LLEVANTAR EN PRODUCCION    
#gunicorn main:app -k gunicorn_conf.ProxiedUvicornWorker --bind 127.0.0.1:8010 --workers 1