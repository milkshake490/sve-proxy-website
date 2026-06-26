import boto3
import psycopg2
import os
import re
from dotenv import load_dotenv

load_dotenv()

#S3 setup
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

#DB setup
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

bucket = os.getenv("AWS_BUCKET_NAME")
paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=bucket, Prefix = "watermarked_cards/")

count = 0
batch_size = 100

for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        filename = key.split("/")[-1].replace(".png", "")
        
        match = re.match(r"([a-z0-9]+)-([a-z]*\d+[a-z]*)_(.*)", filename, re.IGNORECASE)
        if not match:
            print(f"NO MATCH: {filename}")
            continue
        
        set_code = match.group(1).lower()
        card_number = match.group(2).lower()
        card_name = match.group(3).replace("_", " ").lower()
        image_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{key}"
        
        try:
            cur.execute("""
                INSERT INTO cards (set_code, card_number, card_name, image_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (set_code, card_number, card_name, image_url))

            if cur.rowcount == 0:
                print(f"SKIPPED (duplicate): {filename}")

            count += 1

            # Commit every 100 records
            if count % batch_size == 0:
                conn.commit()
                print(f"Processed {count} cards...")

        except Exception as e:
            print(f"ERROR on {filename}: {e}")
            # Reconnect
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur = conn.cursor()

# Final commit
conn.commit()
cur.close()
conn.close()
print(f"Done! Loaded {count} cards into the database.")