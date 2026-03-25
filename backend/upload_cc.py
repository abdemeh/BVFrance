import os
import pandas as pd
import boto3
from botocore.config import Config
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CSV_FOLDER     = Path("csv")
PARQUET_FOLDER = Path("parquet")
PARQUET_FOLDER.mkdir(exist_ok=True)

# Nettoyage initial
for f in PARQUET_FOLDER.glob("*.parquet"):
    f.unlink()
    print(f"Fichier local supprime: {f.name}")

# CSV -> Parquet
csv_files = list(CSV_FOLDER.glob("*.csv"))
print(f"Extraction de {len(csv_files)} fichiers...")

for csv_file in csv_files:
    print(f"Traitement: {csv_file.name}")
    df = pd.read_csv(csv_file, sep=";", encoding="utf-8", dtype=str)

    # Nettoyage colonnes et valeurs
    df.columns = df.columns.str.strip().str.strip('"')
    for col in df.columns:
        df[col] = df[col].str.strip().str.strip('"')

    # Types numeriques
    for col in df.columns:
        if "%" in col:
            df[col] = df[col].str.replace("%", "", regex=False).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    int_cols = ["Inscrits", "Votants", "Abstentions", "Exprimés", "Blancs", "Nuls"]
    for i in range(1, 6):
        int_cols += [f"Voix {i}", f"Sièges au CM {i}", f"Sièges au CC {i}"]
    
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    out = PARQUET_FOLDER / csv_file.with_suffix(".parquet").name
    df.to_parquet(out, index=False)
    print(f"Parquet cree: {out.name}")

# Upload S3
print("\nUpload vers Clever Cloud...")
s3 = boto3.client(
    's3',
    region_name='default',
    aws_access_key_id=os.environ['CELLAR_ADDON_KEY_ID'],
    aws_secret_access_key=os.environ['CELLAR_ADDON_KEY_SECRET'],
    endpoint_url=f"https://{os.environ['CELLAR_ADDON_HOST']}",
    config=Config(
        signature_version='s3v4',
        request_checksum_calculation='WHEN_REQUIRED',
        response_checksum_validation='WHEN_REQUIRED'
    )
)

bucket = os.getenv("CELLAR_BUCKET")

# Verification/Creation du bucket
try:
    s3.head_bucket(Bucket=bucket)
except:
    s3.create_bucket(Bucket=bucket)
    print(f"Bucket {bucket} cree")

for f in PARQUET_FOLDER.glob("*.parquet"):
    key = f"parquet/{f.name}"
    print(f"Envoi: {f.name}")
    data = f.read_bytes()
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentLength=len(data))

print("Termine avec succes")
