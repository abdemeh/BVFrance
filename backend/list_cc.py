import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.getenv('CELLAR_ADDON_HOST')}",
    aws_access_key_id=os.getenv("CELLAR_ADDON_KEY_ID"),
    aws_secret_access_key=os.getenv("CELLAR_ADDON_KEY_SECRET"),
    config=Config(request_checksum_calculation="when_required"),
)

bucket = os.getenv("CELLAR_BUCKET")
print(f"--- Fichiers dans {bucket} ---")

try:
    resp = s3.list_objects_v2(Bucket=bucket)
    if "Contents" in resp:
        for obj in resp["Contents"]:
            print(f"{obj['Key']} ({obj['Size'] / 1_048_576:.2f} MB)")
    else:
        print("Aucun fichier trouve.")
except Exception as e:
    print(f"Erreur: {e}")
