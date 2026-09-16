from Common.routers_factory import generar_router
def generar_router_app_publica(recurso):
    router = generar_router(base='api',data_prefix=recurso, protegido=False)
    return router
def generar_router_app_privada(recurso):
    router = generar_router(base='api',data_prefix=recurso)
    return router