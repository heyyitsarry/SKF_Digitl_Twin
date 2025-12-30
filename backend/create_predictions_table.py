import mysql.connector

DB_CONFIG = {
    "database": "spindless_db",
    "user": "spindless_user",
    "password": "Admin@123",
    "host": "localhost",
    "port": 3306
}

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

# Create spindle_predictions table
create_table_query = """
CREATE TABLE IF NOT EXISTS spindle_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id VARCHAR(50) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    health_score FLOAT,
    failure_risk FLOAT,
    anomaly_score FLOAT,
    status VARCHAR(50),
    raw_data JSON,
    INDEX idx_machine_timestamp (machine_id, timestamp)
);
"""

cur.execute(create_table_query)
conn.commit()

print("✅ Table 'spindle_predictions' created successfully!")

cur.close()
conn.close()
