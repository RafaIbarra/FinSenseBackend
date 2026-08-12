import pytest


@pytest.mark.asyncio
async def test_registrar_categoria_requiere_nombre():
    from Services.categorias_gastos_service import registrar_categoria

    class DummyDB:
        async def execute(self, *args, **kwargs):
            return type("Result", (), {"scalars": lambda self: type("Scalars", (), {"first": lambda self: None})()})()

        async def commit(self):
            return None

        async def refresh(self, *args, **kwargs):
            return None

    db = DummyDB()
    resultado = await registrar_categoria(db, {"user_id": 1, "nombre": "   "})

    assert isinstance(resultado, dict)
    assert "error" in resultado
    assert "obligatorio" in resultado["error"].lower()
