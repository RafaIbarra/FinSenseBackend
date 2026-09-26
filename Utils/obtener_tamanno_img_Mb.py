def calcular_mb(tammano:int =0):
    if tammano==0:
        result=0.0
    else:
        result = round(tammano / 1048576, 2)
    return result
    