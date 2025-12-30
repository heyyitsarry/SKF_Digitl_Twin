
import time
import mysql.connector
from spindle_inference_PCA import run_inference

# ------------------------
# DB config (adjust if needed)
# ------------------------
DB_CONFIG = {
    "database": "spindless_db",
    "user": "spindless_user",
    "password": "Admin@123",
    "host": "localhost",
    "port": 3306
}

POLL_INTERVAL = 5  # seconds

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    last_id = 0

    print("🟢 ML worker started (ONNX runtime)")

    while True:
        cur.execute(
            """
            SELECT * FROM spindlereadings
            WHERE id > %s
            ORDER BY id ASC
            """,
            (last_id,)
        )

        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

        for row in rows:
            record = dict(zip(colnames, row))
            last_id = record["id"]

            result = run_inference(record)

            # Store prediction (or cache / emit later)
            print(f"📈 Prediction for ID {last_id}: {result}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
