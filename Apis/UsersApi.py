from fastapi import  Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError



from Common.routers_factory import generar_router
from Config.settings import get_db
from Security.password_utils import hash_password
from Models.Usuarios import Usuarios
import re




_PREFIX = '/user'
router_user_public = generar_router(_PREFIX, ["Registro Usuarios"], protegido=False)




@router_user_public.post("/registro-usuario")
async def RegistroUsuario(
    nombre: str = Form(...),
    apellido: str = Form(...),
    username: str = Form(...),
    correo: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        username = re.sub(r'\s+', '', username.lower())
        existing_user = await db.execute(
            select(Usuarios).where(Usuarios.UserName == username)
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

        nuevo_usuario = Usuarios(
            NombreUsuario=nombre,
            ApellidoUsuario=apellido,
            UserName=username,
            Correo=correo,
            Password=hash_password(password),
        )

        db.add(nuevo_usuario)
        await db.commit()
        await db.refresh(nuevo_usuario)

        return {
            "status": "success",
            "id": nuevo_usuario.Id,
            "UserName": nuevo_usuario.UserName,
            "Correo": nuevo_usuario.Correo,
            "FechaRegistro": nuevo_usuario.FechaRegistro,
        }

    except HTTPException:
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="El usuario o correo ya existe en la base de datos"
        )

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error interno al guardar el usuario. Intente más tarde."
        )

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error inesperado del servidor. Intente más tarde."
        )