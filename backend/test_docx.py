from minio import Minio
from common.core.config import settings

# Create client
client = Minio(settings.MINIO_ENDPOINT, settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY, secure=settings.MINIO_SECURE)

bucket_name = 'edu-homework'
object_name = '68ddba34-d819-40b3-b40d-8688a5d0d297/1774524905229/对象与类作业-批改 - 副本.docx'

# Download file
response = client.get_object(bucket_name, object_name)
content = response.read()
response.close()
response.release_conn()

print(f'Content length: {len(content)}')
print(f'First 20 bytes (hex): {content[:20].hex()}')
print(f'Is PK (ZIP): {content[:2] == b"PK"}')

# Try to extract text
import io
import zipfile

try:
    with zipfile.ZipFile(io.BytesIO(content), 'r') as z:
        print(f'Files in zip: {z.namelist()[:5]}')
        if 'word/document.xml' in z.namelist():
            print('word/document.xml found!')
except Exception as e:
    print(f'ZIP error: {e}')
