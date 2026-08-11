from fastapi import APIRouter, Depends
from Security.guards import auth_guard

def generar_router(data_prefix, data_tags=[], protegido=True):
    prefijo_final = f'/api{data_prefix}'
    
    kwargs = {
        "prefix": prefijo_final,
        "tags": data_tags,
    }
    
    if protegido:
        kwargs["dependencies"] = [Depends(auth_guard)]
    
    return APIRouter(**kwargs)