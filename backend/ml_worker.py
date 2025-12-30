import time
import psycopg2
from spindle_inference import run_inference

DB_CONFIG = {
    "dbname": "your_db",
    "user": "your_user",
    "password": "your_password",
    "host": "localhost",
    "port": 5432
}

POLL_INTERVAL = 5

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    last_id = 0
    print("🟢 ML worker running")

    while True:
        cur.execute("SELECT * FROM spindlereadings WHERE id > %s ORDER BY id", (last_id,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

        for row in rows:
            rec = dict(zip(cols, row))
            last_id = rec["id"]
            result = run_inference(rec)
            print(f"📈 {last_id} → {result}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()


