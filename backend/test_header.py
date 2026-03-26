from minio import Minio
from common.core.config import settings

# Download file from MinIO
client = Minio(settings.MINIO_ENDPOINT, settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY, secure=settings.MINIO_SECURE)
bucket_name = 'edu-homework'
object_name = '68ddba34-d819-40b3-b40d-8688a5d0d297/1774524905229/对象与类作业-批改 - 副本.docx'

response = client.get_object(bucket_name, object_name)
content = response.read()
response.close()
response.release_conn()

print(f"Content length: {len(content)}")
print(f"First 4 bytes: {content[:4]}")
print(f"First 4 bytes hex: {content[:4].hex()}")
print(f"Match b'\\xd0\\xcf\\x11\\xe0': {content[:4] == b'\xd0\xcf\x11\xe0'}")
