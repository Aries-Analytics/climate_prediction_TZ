import psycopg2
import sys

host = "localhost"
port = 5432
dbname = "climate_dev"
user = "user"
passwords = ["pass", "password", "change_this_password", "admin", "postgres", "root"]

print(f"Testing connection to {dbname} as {user}...")

for p in passwords:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=p
        )
        print(f"\n[SUCCESS] Password found: '{p}'")
        conn.close()
        sys.exit(0)
    except psycopg2.OperationalError:
        print(f"X Failed: '{p}'")

print("\n[FAILED] No password worked.")
sys.exit(1)
