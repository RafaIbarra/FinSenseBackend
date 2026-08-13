# FinTrackApp/Utils/r2_storage.py
import os
import re
import uuid
import urllib.parse
from datetime import datetime
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from Config.settings import settings


class R2Storage:
    """
    Cliente de almacenamiento para Cloudflare R2 (API S3-compatible).
    Reemplazo directo de SupabaseStorage.
    Los buckets deben existir previamente y tener dominio personalizado conectado.
    """

    def __init__(self):
        # Credenciales S3 API
        self.account_id = getattr(settings, 'R2_ACCOUNT_ID', '')
        self.access_key = getattr(settings, 'R2_ACCESS_KEY_ID', '')
        self.secret_key = getattr(settings, 'R2_SECRET_ACCESS_KEY', '')
        self.endpoint_url = getattr(settings, 'R2_ENDPOINT_URL', '')

        # Nombres de buckets (desde settings, deben existir en R2)
        self.bucket_gastos = getattr(settings, 'R2_BUCKET_GASTOS', '')
        

        # URLs públicas por bucket (dominios personalizados conectados en R2)
        self.public_urls = {
            self.bucket_gastos: getattr(settings, 'R2_PUBLIC_URL_GASTOS', ''),
            
        }

        if not all([self.account_id, self.access_key, self.secret_key, self.endpoint_url]):
            raise ValueError(
                "Faltan credenciales de R2 en settings. "
                "Requeridas: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL"
            )

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='auto'
        )

    # ───────────────────────────────────────────────
    # GASTOS
    # ───────────────────────────────────────────────

    def upload_gasto_image(self, file_bytes: bytes, file_name: str):
        return self._upload_image(self.bucket_gastos, file_bytes, file_name)

    def delete_gasto_image(self, image_url: str):
        return self._delete_image(self.bucket_gastos, image_url)

    # ───────────────────────────────────────────────
    # INGRESOS
    # ───────────────────────────────────────────────

    def upload_ingreso_image(self, file_bytes: bytes, file_name: str):
        return self._upload_image(self.bucket_ingresos, file_bytes, file_name)

    def delete_ingreso_image(self, image_url: str):
        return self._delete_image(self.bucket_ingresos, image_url)

    # ───────────────────────────────────────────────
    # LOGO EMPRESAS
    # ───────────────────────────────────────────────

    def upload_logo_empresa(self, file_bytes: bytes, file_name: str):
        return self._upload_image(self.bucket_empresas, file_bytes, file_name)

    def delete_logo_empresa(self, image_url: str):
        return self._delete_image(self.bucket_empresas, image_url)

    # ───────────────────────────────────────────────
    # MÉTODOS INTERNOS
    # ───────────────────────────────────────────────

    def _generar_path(self, file_name: str) -> str:
        """Genera path único: imagenes/20260519_154700_a1b2c3d4.jpg"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        ext = os.path.splitext(file_name)[1] or '.jpg'

        if settings.DEBUG:
            timestamp = f'FIND_{timestamp}'

        return f"{timestamp}_{unique_id}{ext}"

    def _upload_image(self, bucket: str, file_bytes: bytes, file_name: str):
        """Sube archivo al bucket y retorna URL pública."""
        try:
            path = self._generar_path(file_name)

            ext = os.path.splitext(file_name)[1].lower()
            content_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml',
            }.get(ext, 'image/jpeg')

            self.client.put_object(
                Bucket=bucket,
                Key=path,
                Body=BytesIO(file_bytes),
                ContentType=content_type
            )

            url = self._construir_url_publica(bucket, path)

            return {
                'success': True,
                'url': url,
                'path': path,
                'message': 'OK'
            }

        except Exception as e:
            return {
                'success': False,
                'url': '',
                'path': '',
                'message': str(e)
            }

    def _delete_image(self, bucket: str, image_url: str):
        """Elimina archivo del bucket usando su URL pública."""
        try:
            if not image_url:
                return {'success': True, 'message': 'No hay imagen para eliminar'}

            path = self._extraer_path_de_url(image_url, bucket)

            if not path:
                return {
                    'success': False,
                    'error': 'URL no corresponde al bucket',
                    'details': f'No se pudo extraer path de: {image_url}'
                }

            self.client.delete_object(Bucket=bucket, Key=path)

            return {'success': True, 'path': path}

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ('NoSuchKey', '404'):
                return {'success': True, 'message': 'Imagen ya no existe en el bucket'}
            return {
                'success': False,
                'error': 'Error eliminando imagen',
                'details': str(e),
                'image_url': image_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Error eliminando imagen',
                'details': str(e),
                'image_url': image_url
            }

    def _construir_url_publica(self, bucket: str, path: str) -> str:
        """
        Construye URL pública usando el dominio personalizado del bucket.
        No incluye el nombre del bucket en la ruta.
        """
        public_url = self.public_urls.get(bucket, '')

        if public_url:
            return f"{public_url.rstrip('/')}/{path}"

        # Fallback: endpoint S3 nativo (no es público, requiere firma)
        return f"{self.endpoint_url}/{bucket}/{path}"

    def _extraer_path_de_url(self, image_url: str, bucket: str) -> str | None:
        """Extrae el path (Key) de una URL pública o del endpoint S3."""
        if not image_url.startswith('https://'):
            return None

        # Patrón 1: URL nativa R2 (endpoint S3)
        pattern_nativa = rf'https://[^/]+\.r2\.cloudflarestorage\.com/{re.escape(bucket)}/(.+)'
        match = re.search(pattern_nativa, image_url)
        if match:
            return urllib.parse.unquote(match.group(1))

        # Patrón 2: URL pública del bucket (dominio personalizado)
        public_url = self.public_urls.get(bucket, '')
        if public_url:
            pattern_public = rf'{re.escape(public_url.rstrip("/"))}/(.+)'
            match = re.search(pattern_public, image_url)
            if match:
                return urllib.parse.unquote(match.group(1))

        # Patrón 3: Fallback genérico - buscar después del nombre del bucket
        pattern_generico = rf'/{re.escape(bucket)}/(.+)'
        match = re.search(pattern_generico, image_url)
        if match:
            return urllib.parse.unquote(match.group(1))

        return None


# Instancia global
r2_storage = R2Storage()