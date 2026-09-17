def formatear_fecha_larga(fecha):
    return fecha.strftime("%d/%m/%Y %H:%M:%S") if fecha else None

def formatear_fecha_corta(fecha):
    return fecha.strftime("%d/%m/%Y") if fecha else None