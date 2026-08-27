
from Common.routers_factory import generar_router
from Common.rate_limit_middleware import rate_limit
router_tests = generar_router('/test-data',data_tags=[], protegido=False)
@router_tests.get("/tests")
@rate_limit(max_requests=2, window_seconds=1)
async def tests():
    return {
       'OK'
    }