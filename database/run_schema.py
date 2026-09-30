import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from your .env file.")

SCHEMA_PATH = Path(__file__).resolve().parent / "Schema.sql"

with open(SCHEMA_PATH, "r") as f:
    schema_sql = f.read()

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute(schema_sql)

print("Schema applied successfully. Tables created:")

with conn.cursor() as cur:
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    for row in cur.fetchall():
        print(f"  - {row[0]}")

conn.close()