from Config.settings import settings

def cookie_name(base: str) -> str:
    return f"__Host-{base}" if settings.MODO_PRODUCCION else base

ACCESS_COOKIE = cookie_name("access_token")
REFRESH_COOKIE = cookie_name("refresh_token")