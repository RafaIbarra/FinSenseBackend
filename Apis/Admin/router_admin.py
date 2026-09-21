from Common.routers_factory import generar_router
def generar_router_admin(recurso):
    router = generar_router(base='api',data_prefix=recurso,protegido_admin=True)
    return router