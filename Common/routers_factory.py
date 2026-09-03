from fastapi import APIRouter, Depends
from Security.guards import auth_guard

def generar_router(data_prefix, data_tags=[], protegido=True, protegido_admin=False):
    prefijo_final = f'/api{data_prefix}'
    
    kwargs = {
        "prefix": prefijo_final,
        "tags": data_tags,
    }
    
    if protegido or protegido_admin:
        kwargs["dependencies"] = [Depends(auth_guard(requiere_admin=protegido_admin))]
    
    return APIRouter(**kwargs)