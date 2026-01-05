import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List




from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse




import mysql.connector
import mysql.connector.errors
from opcua import Client
import os
import json
import sys
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List




from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse




import mysql.connector
import mysql.connector.errors
from opcua import Client
import os
import json
import sys




# -------------------------
# Basic config / logging
# -------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(base_dir, "spindle_log.txt")




logging.basicConfig(
   filename=log_file,
   level=logging.INFO,
   format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("modern.py logging initialized")




# -------------------------
# MySQL config (HARDCODED - AVOID IN PRODUCTION)
# -------------------------
MYSQL_CONFIG = {
   "host": "localhost",
   "user": "spindless_user",
   "password": "Admin@123",
   "database": "spindless_db",
   "raise_on_warnings": True
}




def get_connection():
   return mysql.connector.connect(**MYSQL_CONFIG)




# -------------------------
# Kepware / OPC UA URLs (HARDCODED - AVOID IN PRODUCTION)
# -------------------------
KEPWARE_URL = "opc.tcp://163.157.19.134:49320"
NEW_KEPWARE_URL = "opc.tcp://INPUN4CE403CJ6W.corp.skf.net:49320"




kepware_client = None
kepware_new_client = None




# --- THREAD SAFETY FIX: Global Lock to prevent concurrent access to OPC UA clients ---
OPC_UA_LOCK = threading.Lock()




# --- CORE SANITIZATION FUNCTION ---
def sanitize_key(key: str) -> str:
   """Removes trailing/leading whitespace and replaces non-alphanumeric chars with underscores."""
   safe_name = key.strip()
   safe_name = safe_name.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('.', '_').replace(',', '')
   return safe_name




# -------------------------
# BASE TAGS (The 52 authoritative tags - Sanitized by dictionary creation)
# -------------------------
RAW_BASE_SPINDLE_TAGS = {
   # 9 Core Metrics
   "Grinding_spindle_mist_pressure": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding_spindle_mist_pressure",
   "GRINDING_SPINDLE_TEMP": "ns=2;s=IMX.CH_04_SSB1080.GRINDING_SPINDLE_TEMP",
   "GRINDING_SPINDLE_CURRENT": "ns=2;s=IMX.CH_04_SSB1080.GRINDING_SPINDLE_CURRENT",
   "SPINDLE_ACTUAL_SPEED": "ns=2;s=IMX.CH_04_SSB1080.SPINDLE_ACTUAL_SPEED",
   "02_HE4_NDE": "ns=2;s=IMX.CH_04_SSB1080.02_HE4_NDE",
   "02_HV_NDE": "ns=2;s=IMX.CH_04_SSB1080.02_HV_NDE",
   "02_HA_NDE": "ns=2;s=IMX.CH_04_SSB1080.02_HA_NDE",
   "01_HV_DE": "ns=2;s=IMX.CH_04_SSB1080.01_HV_DE",
   "01_HE4_DE": "ns=2;s=IMX.CH_04_SSB1080.01_HE4_DE",
   "01_HA_DE": "ns=2;s=IMX.CH_04_SSB1080.01_HA_DE",
 
   # 43 Application/Process Data Tags
 
    "Worn-out grinding wheel": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Worn-out grinding wheel",
    "WORKHEAD_RPM": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.WORKHEAD_RPM",
    "WAITING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.WAITING TIME",
    "TOTAL GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.TOTAL GRINDING TIME",
    "Spindle_type": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Spindle_type",
    "SPARK OUT TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.SPARK OUT TIME",
    "Sizematic knock-off 2 position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Sizematic knock-off 2 position",
    "Sizematic knock-off 1 position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Sizematic knock-off 1 position",
    "Rough_2_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_2_pwr",
    "Rough_2_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_2_feed_rate",
    "Rough_1_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_1_pwr",
    "Rough_1_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_1_feed_rate",
    "ROUGH GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.ROUGH GRINDING TIME",
    "Rough- 1 Grinding Distance": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough- 1 Grinding Distance",
    "RING CHANGE TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.RING CHANGE TIME",
    "New wheel diameter when dressed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.New wheel diameter when dressed",
    "Maximum Grinding Spindle Speed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Maximum Grinding Spindle Speed",
    "Incremental retreat 1, initial": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Incremental retreat 1, initial",
    "Grinding_servo_torque": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding_servo_torque",
    "Grinding_axis_position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding_axis_position",
    "Grinding Wheel Speed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding Wheel Speed",
    "Grinding Wheel Peripheral Speed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding Wheel Peripheral Speed",
    "Grinding finish position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding finish position",
    "Grinding compensation interval ctr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding compensation interval ctr",
    "Grinding compensation interval": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding compensation interval",
    "Grinding compensation": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding compensation",
    "Grinding (reference) position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding (reference) position",
    "Fine_grinding_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Fine_grinding_pwr",
    "Fine_grinding_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Fine_grinding_feed_rate",
    "FINE GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.FINE GRINDING TIME",
    "Early limit position finish size": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Early limit position finish size",
    "Dress-off a new wheel": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Dress-off a new wheel",
    "DRESSING_SPARK_OUT_TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_SPARK_OUT_TIME",
    "DRESSING_INTERVAL": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_INTERVAL",
    "DRESSING_INFEED_SPEED": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_INFEED_SPEED",
    "DRESSING_COMPENSATION": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_COMPENSATION",
    "DRESSING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING TIME",
    "Dressing starting position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Dressing starting position",
    "Dressing slide jump in position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Dressing slide jump in position",
    "Constant Grinding Wheel Speed If SA48 = 1": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Constant Grinding Wheel Speed If SA48 = 1",
    "Compensation memory": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Compensation memory",
    "Bearing_Type": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Bearing_Type",
    "Axis_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Axis_feed_rate",
    "Air_grinding_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Air_grinding_pwr",
    "Air_grinding_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Air_grinding_feed_rate",
    "AIR GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.AIR GRINDING TIME",
    "Actual wheel diameter": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Actual wheel diameter",
    "Marposs Gauge Enter position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Marposs Gauge Enter position",
    "Incremental retreat 2, initial": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Incremental retreat 2, initial",
    "Grinding slide jump in position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding slide jump in position",
    "Gap eliminator safety position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Gap eliminator safety position",
    "Air grind feed rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Air grind feed rate",
}












# --- CRITICAL SANITIZATION STEP APPLIED HERE ---
tags_spindle = {sanitize_key(k): v for k, v in RAW_BASE_SPINDLE_TAGS.items()}
BASE_SPINDLE_TAGS = tags_spindle.copy()




# tags_test (unchanged)
tags_test = {
   "spindle_type": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Type",
   "spindle_temp": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Temp",
   "spindle_speed": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Speed",
   "spindle_resistance": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Resistance",
   "spindle_megger": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Megger",
   "spindle_inductance": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Inductance",
   "spindle_current": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Current",
   "mist_lub_pre_rear": "ns=2;s=Spindle_Room.Test_Rig.Mist_Lub_Pre_Rear",
   "mist_lub_pre_front": "ns=2;s=Spindle_Room.Test_Rig.Mist_Lub_Pre_Front",
   "lub_pump_oil_pre": "ns=2;s=Spindle_Room.Test_Rig.Lub_Pump_Oil_Pre",
   "lub_pump_air_pre": "ns=2;s=Spindle_Room.Test_Rig.Lub_Pump_Air_Pre",
   "chiller_water_pressure": "ns=2;s=Spindle_Room.Test_Rig.Chiller_Water_Pressure",
   "chiller_temp": "ns=2;s=Spindle_Room.Test_Rig.Chiller_Temp",
   "rear_bearing_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_Vibration",
   "rear_bearing_gen_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_gE_03",
   "rear_bearing_gen_vib2": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_gE_04",
   "rear_bearing_acc": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_Acceleration",
   "front_bearing_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_Vibration",
   "front_bearing_gen_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_gE_03",
   "front_bearing_gen_vib2": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_gE_04",
   "front_bearing_acc": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_Acceleration",
}
BASE_TEST_TAGS = tags_test.copy()
# -------------------------
# Shared Variables
# -------------------------
last_values_spindle = {k: 0.0 for k in tags_spindle.keys()}
last_values_test = {k: 0.0 for k in tags_test.keys()}




running = {
   "spindle": {"thread": None, "stop_event": None, "session_id": None, "machine": None, "start_time": None},
    "test"  :{"thread" : None, "stop_event": None, "session_id":None,"machine": None, "stsrt_test":None}
}
# -------------------------
# Helper Functions
# -------------------------
def sql_identifier_from_key(key: str) -> str:
   k = key.replace("`", "``")
   return f"`{k}`"




def load_dynamic_spindle_tags(db_tags: Dict[str, str]) -> Dict[str, str]:
   """Loads all custom tags from DB and merges them with the base tags."""
   final_tags = BASE_SPINDLE_TAGS.copy()
   for raw_name, path in db_tags.items():
       # Sanitize the name read from the DB before using it as a key/column name
       safe_name = sanitize_key(raw_name)
       if safe_name:
           final_tags[safe_name] = path
   return final_tags




def ensure_tables():
   cnx = get_connection()
   cur = cnx.cursor()
   db_name = MYSQL_CONFIG["database"]
 
   # --- Helper to safely execute CREATE TABLE and ignore 'already exists' (Error 1050) ---
   def safe_create_table(sql, table_name):
       try:
           cur.execute(sql)
           cnx.commit()
       except mysql.connector.errors.ProgrammingError as e:
           # Error Code 1050: Table '...' already exists
           if e.errno == 1050:
               logging.info(f"Database setup: Table '{table_name}' already exists. Skipping creation.")
           else:
               raise e
       except Exception as e:
           logging.error(f"Error during initial {table_name} CREATE TABLE: {e}")




   # --- 0. Load ALL possible tags to ensure schema is wide enough (for ALTER TABLE below) ---
   db_tags = {}
   safe_create_table("""
   CREATE TABLE IF NOT EXISTS parameters (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       path VARCHAR(255) NOT NULL
   )
   """, "parameters")
 
   try:
       temp_cur = cnx.cursor(dictionary=True)
       temp_cur.execute("SELECT name, path FROM parameters")
       db_tags = {r['name']: r['path'] for r in temp_cur.fetchall()}
       temp_cur.close()
   except Exception:
       pass
     
   all_spindle_tags = load_dynamic_spindle_tags(db_tags)
 
   # --- 1. spindlereadings Table: Create/Alter (FULLY DYNAMIC) ---
   spindle_cols_sql = ["id INT AUTO_INCREMENT PRIMARY KEY", "timestamp DATETIME", "machine_id VARCHAR(100)"]
   for orig_key in all_spindle_tags.keys():
       col_ident = sql_identifier_from_key(orig_key)
       col_type = "VARCHAR(200)" if orig_key in ("Spindle_type", "Bearing_Type") else "DOUBLE"
       spindle_cols_sql.append(f"{col_ident} {col_type}")
         
   cols_sql = ",\n \t".join(spindle_cols_sql)
   create_spindle_sql = f"CREATE TABLE IF NOT EXISTS spindlereadings (\n \t{cols_sql}\n)"
 
   safe_create_table(create_spindle_sql, "spindlereadings")
     
   # Check and Add Missing Spindle Columns
   for col_name in all_spindle_tags.keys():
       col_ident = sql_identifier_from_key(col_name)
       col_type = "VARCHAR(200)" if col_name in ("Spindle_type", "Bearing_Type") else "DOUBLE"
     
       cur.execute("""
           SELECT 1
           FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = %s
             AND TABLE_NAME = 'spindlereadings'
             AND COLUMN_NAME = %s
       """, (db_name, col_name))
     
       if cur.fetchone() is None:
           logging.warning(f"Column '{col_name}' missing from spindlereadings. Adding it...")
           try:
               cur.execute(f"ALTER TABLE spindlereadings ADD COLUMN {col_ident} {col_type} DEFAULT NULL")
               cnx.commit()
               logging.info(f"Successfully added column '{col_name}'.")
           except Exception as e:
               logging.error(f"Failed to ALTER TABLE to add column '{col_name}': {e}")
             
   # --- 2. TestReading Table: Create/Alter (FULLY DYNAMIC) ---
   test_cols_sql = ["id INT AUTO_INCREMENT PRIMARY KEY", "timestamp DATETIME", "machine_id VARCHAR(100)"]
   for orig_key in tags_test.keys():
       col_ident = sql_identifier_from_key(orig_key)
       col_type = "INT" if orig_key == "spindle_type" else "DOUBLE"
       test_cols_sql.append(f"{col_ident} {col_type}")
         
   cols_sql = ",\n \t".join(test_cols_sql)
   create_test_sql = f"CREATE TABLE IF NOT EXISTS TestReading (\n \t{cols_sql}\n)"
 
   safe_create_table(create_test_sql, "TestReading")
     
   # Check and Add Missing Test Columns
   for col_name in tags_test.keys():
       col_ident = sql_identifier_from_key(col_name)
       col_type = "INT" if col_name == "spindle_type" else "DOUBLE"
     
       cur.execute("""
           SELECT 1
           FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = %s
             AND TABLE_NAME = 'TestReading'
             AND COLUMN_NAME = %s
       """, (db_name, col_name))
     
       if cur.fetchone() is None:
           logging.warning(f"Column '{col_name}' missing from TestReading. Adding it...")
           try:
               cur.execute(f"ALTER TABLE TestReading ADD COLUMN {col_ident} {col_type} DEFAULT NULL")
               cnx.commit()
               logging.info(f"Successfully added column '{col_name}'.")
           except Exception as e:
               logging.error(f"Failed to ALTER TABLE to add column '{col_name}': {e}")
             
 
   # --- 4. SessionHistory (FIXED: Checks for 'remarks') ---
   safe_create_table("""
   CREATE TABLE IF NOT EXISTS SessionHistory (
       id INT AUTO_INCREMENT PRIMARY KEY,
       machine_name VARCHAR(100),
       reading_type ENUM('Spindle','Test'),
       start_time DATETIME,
       end_time DATETIME,
       duration_minutes DOUBLE,
       records_logged INT,
       remarks VARCHAR(500)
   )
   """, "SessionHistory")
 
   # Ensure remarks column exists even if old table was missing it
   try:
       cur.execute("""
           SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'SessionHistory' AND COLUMN_NAME = 'remarks'
       """, (db_name, ))
       if cur.fetchone() is None:
            cur.execute("ALTER TABLE SessionHistory ADD COLUMN remarks VARCHAR(500) DEFAULT NULL")
            cnx.commit()
            logging.info("Successfully added missing 'remarks' column to SessionHistory.")
   except Exception as e:
       logging.error(f"Failed to ensure 'remarks' column: {e}")


   # --- 5. spindle_predictions (For ML predictions) ---
   safe_create_table("""
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
   )
   """, "spindle_predictions")


   cnx.commit()
   cur.close()
   cnx.close()




def connect_kepware():
   global kepware_client, kepware_new_client
   try:
       kepware_client = Client(KEPWARE_URL)
       kepware_client.connect()
       logging.info("Connected to Kepware OPC UA server (spindle).")
   except Exception as e:
       logging.error(f"Spindle Kepware connection failed: {e}")
       kepware_client = None




   try:
       kepware_new_client = Client(NEW_KEPWARE_URL)
       kepware_new_client.connect()
       logging.info("Connected to new Kepware (test).")
   except Exception as e:
       logging.error(f"Test Kepware connection failed: {e}")
       kepware_new_client = None
     
def safe_get_node_value(client: Client, nodeid: str, last_values_map: dict, key: str):
   try:
       if client is None:
           return last_values_map.get(key, 0.0)
     
       node = client.get_node(nodeid)
       val = node.get_value()
     
       if key in ("Spindle_type", "Bearing_Type"):
           val = str(val) if val is not None else ""
       elif val is not None:
           try:
               val = float(val)
           except (ValueError, TypeError):
               val = 0.0
       else:
           val = 0.0
         
       last_values_map[key] = val
       return val
   except Exception as e:
       logging.error(f"Failed reading node {nodeid} ({key}): {e}")
       return last_values_map.get(key, 0.0)




def get_kepware_data_for_tags(client: Client, tags: Dict[str, str], last_values_map: dict):
   data = {}
   for param, nodeid in tags.items():
       data[param] = safe_get_node_value(client, nodeid, last_values_map, param)
   return data




def log_session_start(machine_name: str, reading_type: str) -> int:
   cnx = get_connection()
   cur = cnx.cursor()
   start_time = datetime.now()
 
   sql = "INSERT INTO SessionHistory (machine_name, reading_type, start_time, records_logged, remarks) VALUES (%s, %s, %s, %s, %s)"
   cur.execute(sql, (machine_name, reading_type.capitalize(), start_time, 0, None))
 
   session_id = cur.lastrowid
   cnx.commit()
   cur.close()
   cnx.close()
   logging.info(f"Session started: id={session_id}, machine={machine_name}, type={reading_type}")
   return session_id




# FIX: Added try/except for robustness against DB failure during stop
def log_session_stop(session_id: int, start_time: datetime, end_time: datetime, machine_name: str, reading_type: str):
   cnx = None
   cur = None
   records_logged = 0
   duration_min = (end_time - start_time).total_seconds() / 60.0




   try:
       cnx = get_connection()
       cur = cnx.cursor()




       # 1. Get record count
       table_name = "spindlereadings" if reading_type == "Spindle" else "TestReading"
       cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE machine_id=%s AND timestamp BETWEEN %s AND %s",
                      (machine_name, start_time, end_time))
       records_logged = cur.fetchone()[0]
     
       # 2. Update SessionHistory
       cur.execute("""
           UPDATE SessionHistory
           SET end_time=%s, duration_minutes=%s, records_logged=%s
           WHERE id=%s
       """, (end_time, duration_min, records_logged, session_id))
       cnx.commit()
     
   except Exception as e:
       logging.error(f"FATAL DB ERROR: Failed to finalize session {session_id} in log_session_stop: {e}")
     
   finally:
       # Ensure cleanup runs regardless of success or failure
       if cur: cur.close()
       if cnx: cnx.close()
     
       logging.info(f"Session stopped: id={session_id}, records={records_logged}, duration_min={duration_min:.2f}")




# -------------------------
# Worker: Spindle (Handles dynamic tags and robust DB connection management)
# -------------------------
def spindle_worker(session_id: int, machine_id: str, start_time: datetime, stop_event: threading.Event):
   logging.info(f"Spindle worker started for session {session_id}, machine {machine_id}")
 
   cnx = None
   cur = None




   # DYNAMIC TAGS LOADED HERE: This ensures new parameters are picked up
   try:
       cnx_tags = get_connection()
       cur_tags = cnx_tags.cursor(dictionary=True)
       cur_tags.execute("SELECT name, path FROM parameters")
       db_tags = {r['name']: r['path'] for r in cur_tags.fetchall()}
       cnx_tags.close()
     
       # Use the dynamic list inside the worker
       local_tags_spindle = load_dynamic_spindle_tags(db_tags)
       local_last_values = {k: 0.0 for k in local_tags_spindle.keys()}
     
   except Exception as e:
       logging.error(f"Spindle worker FAILED TO LOAD DYNAMIC TAGS: {e}. Using base tags only.")
       local_tags_spindle = BASE_SPINDLE_TAGS.copy()
       local_last_values = {k: 0.0 for k in BASE_SPINDLE_TAGS.keys()}




   try:
       # 1. Open the main DB connection that runs inside the loop
       cnx = get_connection()
       cur = cnx.cursor()




       counter = 0
       while not stop_event.is_set():
           timestamp = datetime.now()
           # USE LOCAL TAGS/LAST VALUES MAPS
           data = get_kepware_data_for_tags(kepware_client, local_tags_spindle, local_last_values)
         
           # Application Logic: Set current to 0.0 if below 5
           current_val = data.get("GRINDING_SPINDLE_CURRENT", 0.0) or 0.0
         
           # ----------------------------------------------------------------------------------
           # NEW REQUIREMENT: Skip insertion if GRINDING_SPINDLE_CURRENT < 5
           # ----------------------------------------------------------------------------------
           if isinstance(current_val, (int, float)) and current_val < 5:
               logging.info(f"Spindle current ({current_val:.2f}) is less than 5. Skipping DB insert for session {session_id}.")
               time.sleep(20)
               continue # Skip the rest of the loop and start the next iteration
           # ----------------------------------------------------------------------------------




           data["GRINDING_SPINDLE_CURRENT"] = current_val




           # Build SQL statement dynamically for the complete tag list
           cols = ["timestamp", "machine_id"] + list(local_tags_spindle.keys())
           col_sql = ",".join([sql_identifier_from_key(c) for c in cols])
           placeholders = ",".join(["%s"] * len(cols))
         
           # Values retrieved here are mapped to the ordered keys
           values = [timestamp, machine_id] + [data.get(k) for k in local_tags_spindle.keys()]
         
           cur.execute(f"INSERT INTO spindlereadings ({col_sql}) VALUES ({placeholders})", tuple(values))
           cnx.commit()
           counter += 1
           if counter % 5 == 0:
               logging.info(f"Spindle insert #{counter} for session {session_id}: machine={machine_id}")
           time.sleep(20)
         
   except Exception as e:
       logging.error(f"Spindle worker exception: {e}")
     
   finally:
       # CRITICAL FIX: Ensure session end is logged and connections are closed
       end_time = datetime.now()
       log_session_stop(session_id, start_time, end_time, machine_id, "Spindle")
     
       # Explicitly close the worker's own connection/cursor
       if cur: cur.close()
       if cnx: cnx.close()
     
       logging.info(f"Spindle worker finished for session {session_id}")








# -------------------------
# Worker: Test (Robust DB connection management)
# -------------------------
def test_worker(session_id: int, machine_id: str, start_time: datetime, stop_event: threading.Event):
   logging.info(f"Test worker started for session {session_id}, machine {machine_id}")
 
   cnx = None
   cur = None
 
   try:
       # Open the main DB connection
       cnx = get_connection()
       cur = cnx.cursor()
     
       counter = 0
       while not stop_event.is_set():
           timestamp = datetime.now()
           data = get_kepware_data_for_tags(kepware_new_client, tags_test, last_values_test)




           cur.execute(f"""
               INSERT INTO TestReading (
                   timestamp, machine_id, spindle_type, spindle_temp, spindle_speed,
                   spindle_resistance, spindle_megger, spindle_inductance, spindle_current,
                   mist_lub_pre_rear, mist_lub_pre_front, lub_pump_oil_pre, lub_pump_air_pre,
                   chiller_water_pressure, chiller_temp, rear_bearing_vib, rear_bearing_gen_vib,
                   rear_bearing_gen_vib2, rear_bearing_acc, front_bearing_vib, front_bearing_gen_vib,
                   front_bearing_gen_vib2, front_bearing_acc
               ) VALUES (
                   %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
               )
           """, (
               timestamp, machine_id, data.get("spindle_type", 0), data.get("spindle_temp", 0.0),
               data.get("spindle_speed", 0.0), data.get("spindle_resistance", 0.0), data.get("spindle_megger", 0.0),
               data.get("spindle_inductance", 0.0), data.get("spindle_current", 0.0), data.get("mist_lub_pre_rear", 0.0),
               data.get("mist_lub_pre_front", 0.0), data.get("lub_pump_oil_pre", 0.0), data.get("lub_pump_air_pre", 0.0),
               data.get("chiller_water_pressure", 0.0), data.get("chiller_temp", 0.0), data.get("rear_bearing_vib", 0.0),
               data.get("rear_bearing_gen_vib", 0.0), data.get("rear_bearing_gen_vib2", 0.0), data.get("rear_bearing_acc", 0.0),
               data.get("front_bearing_vib", 0.0), data.get("front_bearing_gen_vib", 0.0), data.get("front_bearing_gen_vib2", 0.0),
               data.get("front_bearing_acc", 0.0)
           ))
           cnx.commit()
           counter += 1
           if counter % 5 == 0:
                logging.info(f"Test insert #{counter} for session {session_id}: machine={machine_id}")
           time.sleep(20)
         
   except Exception as e:
       logging.error(f"Test worker exception: {e}")
     
   finally:
       end_time = datetime.now()
       log_session_stop(session_id, start_time, end_time, machine_id, "Test")
     
       # Explicitly close the worker's own connection/cursor
       if cur: cur.close()
       if cnx: cnx.close()
     
       logging.info(f"Test worker finished for session {session_id}")
     
# -------------------------
# FastAPI App & Endpoints
# -------------------------
app = FastAPI()




@app.on_event("startup")
def startup_event():
   ensure_tables()
   try:
       connect_kepware()
   except Exception as e:
       logging.error(f"Startup: Kepware connect issue: {e}")




   # Auto-start spindle session logic
   if running["spindle"]["thread"] is None:
       dynamic_restart_spindle_worker("SSB1080", "Spindle")




# --- RESTART HELPER FUNCTION ---
def dynamic_restart_spindle_worker(machine_id: str, type_reading: str):
   """Stops the current worker and immediately starts a new one."""
 
   type_reading_lower = type_reading.lower()
   current_info = running[type_reading_lower]
 
   # 1. Stop existing thread if running
   if current_info["thread"] is not None:
       logging.info(f"Signaling current {type_reading} worker to stop for restart.")
       current_info["stop_event"].set()
       current_info["thread"].join()
     
   # 2. START new thread
   logging.info(f"Starting new {type_reading} worker for machine {machine_id}.")
   stop_event = threading.Event()
   start_time = datetime.now()
 
   # IMPORTANT: We must ensure the DB schema is up to date BEFORE starting the logger
   ensure_tables()
 
   session_id = log_session_start(machine_id, type_reading)
 
   worker_target = spindle_worker if type_reading == "Spindle" else test_worker
 
   t = threading.Thread(target=worker_target,
                        args=(session_id, machine_id, start_time, stop_event),
                        daemon=True)
                       
   running[type_reading.lower()].update({
       "thread": t,
       "stop_event": stop_event,
       "session_id": session_id,
       "machine": machine_id,
       "start_time": start_time
   })
 
   t.start()
   return session_id




# --- ADDED API ENDPOINT TO TRIGGER RESTART FROM JAVASCRIPT ---
@app.get("/trigger-spindle-restart")
def trigger_spindle_restart(machine: str = "SSB1080"):
   """API endpoint to manually trigger the worker restart and schema update."""
   try:
       session_id = dynamic_restart_spindle_worker(machine, "Spindle")
       return JSONResponse({
           "status": "success",
           "message": f"Spindle worker successfully restarted with new configuration.",
           "session_id": session_id
       })
   except Exception as e:
       logging.error(f"Failed to trigger dynamic restart: {e}")
       return JSONResponse({"status": "error", "message": f"Failed to restart worker: {e}"}, status_code=500)
# -----------------------------------------------------------------------








# --- PARAMETER MANAGEMENT ENDPOINTS ---




@app.get("/parameters")
def get_parameters(machine: str = "SSB1080", rtype: str = "Spindle"):
   """Retrieves all custom parameters from the database. Machine/Type parameters are not supported
      in the backend yet, so this always returns Spindle dynamic tags."""
 
   # NOTE: The current system only stores dynamic tags globally in the 'parameters' table
   # which is merged with BASE_SPINDLE_TAGS.
   # For a full implementation, the 'parameters' table would need machine/type columns.
 
   cnx = get_connection()
   cur = cnx.cursor(dictionary=True)
 
   # Only retrieving global custom parameters
   cur.execute("SELECT id, name, path FROM parameters ORDER BY id DESC")
   rows = cur.fetchall()
 
   cur.close()
   cnx.close()
   return JSONResponse(rows)




@app.post("/parameters/add")
async def add_parameter(
   parameter_name: str = Form(...),
   opc_ua_path: str = Form(...),
   machine: str = Form(...),
   type_reading: str = Form(...)
):
   if not parameter_name or not opc_ua_path:
       return JSONResponse(
           status_code=400,
           content={"status": "error", "message": "Parameter Name and OPC-UA Path cannot be empty."}
       )




   # NOTE: Since the backend only supports dynamic tags for the Spindle table
   # and the logic uses a global 'parameters' table, the machine/type parameters
   # are currently ignored for insertion logic but passed for UI compatibility.
   if type_reading != "Spindle":
       return JSONResponse(
           status_code=400,
           content={"status": "error", "message": "Adding parameters is currently only supported for 'Spindle' type."}
       )
     
   try:
       cnx = get_connection()
       cur = cnx.cursor()




       # Check duplicate NAME
       cur.execute("SELECT id FROM parameters WHERE name = %s", (parameter_name,))
       if cur.fetchone():
           cur.close()
           cnx.close()
           return JSONResponse(
               status_code=409,
               content={"status": "error", "message": f"Parameter '{parameter_name}' already exists."}
           )




       # Check duplicate PATH
       cur.execute("SELECT id, name FROM parameters WHERE path = %s", (opc_ua_path,))
       row = cur.fetchone()
       if row:
           cur.close()
           cnx.close()
           return JSONResponse(
               status_code=409,
               content={"status": "error", "message": f"OPC-UA Path already used by parameter '{row[1]}'."}
           )




       # Insert new parameter if both name and path are unique (Global insert)
       sql = "INSERT INTO parameters (name, path) VALUES (%s, %s)"
       cur.execute(sql, (parameter_name, opc_ua_path))
       cnx.commit()
       cur.close()
       cnx.close()




       # Restart spindle worker and ensure schema update
       dynamic_restart_spindle_worker(machine, type_reading)




       return JSONResponse(content={
           "status": "success",
           "message": f"Parameter '{parameter_name}' added. Spindle worker restarted to include new tag."
       })




   except Exception as e:
       logging.error(f"Failed to add parameter: {e}")
       return JSONResponse(
           status_code=500,
           content={"status": "error", "message": f"Database error: {e}"})
# --- START/STOP ENDPOINTS (Dashboard compatibility shims) ---




@app.get("/start-spindle")
def start_spindle(machine: str = "SSB1080"):
   type_reading = "Spindle"
   if running[type_reading.lower()]["thread"] is not None:
       return JSONResponse({"status": "error", "message": "Spindle already running"})
 
   session_id = dynamic_restart_spindle_worker(machine, type_reading)
   return JSONResponse({"status": "success", "session_id": session_id})




@app.get("/stop-spindle")
def stop_spindle_get(remarks: Optional[str] = ""):
   return stop_worker("spindle", remarks)




@app.get("/start-test")
def start_test(machine: str = "SSB1080"):
   type_reading = "Test"
   if running[type_reading.lower()]["thread"] is not None:
       return JSONResponse({"status": "error", "message": "Test already running"})
 
   # We still use the old start logic for Test worker as it's not dynamic yet
   stop_event = threading.Event()
   start_time = datetime.now()
   session_id = log_session_start(machine, type_reading)
 
   t = threading.Thread(target=test_worker, args=(session_id, machine, start_time, stop_event), daemon=True)
   running[type_reading.lower()].update({"thread": t, "stop_event": stop_event, "session_id": session_id, "machine": machine, "start_time": start_time})
   t.start()
   return JSONResponse({"status": "success", "session_id": session_id})




@app.get("/stop-test")
def stop_test_get(remarks: Optional[str] = ""):
   return stop_worker("test", remarks)




def stop_worker(type_reading: str, remarks: Optional[str] = ""):
   type_reading = type_reading.lower()
   if type_reading not in ("spindle", "test"):
       return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid type"})




   thread_info = running[type_reading]
   if thread_info["thread"] is None:
       return JSONResponse(content={"status": "error", "message": f"{type_reading.capitalize()} reading is not running"})




   try:
       thread_info["stop_event"].set()
       thread_info["thread"].join()




       if remarks:
           try:
               cnx = get_connection()
               cur = cnx.cursor()
               sql = "UPDATE SessionHistory SET remarks=%s WHERE id=%s"
               cur.execute(sql, (remarks, thread_info["session_id"]))
               cnx.commit()
               cur.close()
               cnx.close()
           except Exception as e:
               logging.error(f"Failed to update remarks for session {thread_info['session_id']}: {e}")




       session_id = thread_info["session_id"]
       running[type_reading] = {"thread": None, "stop_event": None, "session_id": None, "machine": None, "start_time": None}




       return JSONResponse(content={"status": "success", "session_id": session_id, "message": f"{type_reading.capitalize()} reading stopped."})




   except Exception as e:
       logging.error(f"Stop worker error: {e}")
       return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})




# --- UTILITY ENDPOINTS ---




def serialize_rows(rows):
   serialized = []
   for row in rows:
       new_row = {}
       for key, value in row.items():
           if isinstance(value, datetime):
               new_row[key] = value.isoformat()
           else:
               new_row[key] = value
       serialized.append(new_row)
   return serialized




@app.get("/records")
def get_records(machine: str = "SSB1080", rtype: str = "Spindle", limit: Optional[int] = None, from_date: Optional[str] = None, to_date: Optional[str] = None):
   cnx = get_connection()
   cur = cnx.cursor(dictionary=True)
 
   # We must ensure we get the full list of columns to query!
   db_tags = {}
   table_name = "spindlereadings" if rtype == "Spindle" else "TestReading"
 
   if rtype == "Spindle":
       try:
           temp_cur = cnx.cursor(dictionary=True)
           temp_cur.execute("SELECT name, path FROM parameters")
           db_tags = {r['name']: r['path'] for r in temp_cur.fetchall()}
           temp_cur.close()
       except Exception:
           pass




       final_tag_list = load_dynamic_spindle_tags(db_tags)
     
       # Build SELECT list:
       all_cols = ["id", "timestamp", "machine_id"] + list(final_tag_list.keys())
       select_cols = ",".join([sql_identifier_from_key(c) for c in all_cols])
     
       query = f"SELECT {select_cols} FROM {table_name} WHERE machine_id=%s"
     
   else: # Test Rig (Static)
       query = f"SELECT * FROM {table_name} WHERE machine_id=%s"




   params = [machine]
 
   # --- DATE FILTERING LOGIC ---
   if from_date:
       query += " AND timestamp >= %s"
       params.append(from_date)
     
   if to_date:
       # The JavaScript increments the 'to' date by 1 day to make the range inclusive.
       # We use '<' here to filter records up to, but not including, the start of the next day.
       query += " AND timestamp < %s"
       params.append(to_date)
   # ----------------------------




   query += " ORDER BY timestamp DESC"




   if limit is not None and limit > 0:
       query += " LIMIT %s"
       params.append(limit)
 
   # Execute the dynamically built query
   try:
       cur.execute(query, tuple(params))
       rows = cur.fetchall()
   except mysql.connector.errors.ProgrammingError as e:
       # This catches errors like "Unknown column 'CLAMP_PRESSURE'"
       logging.error(f"Records query failed (likely missing column): {e}")
       rows = [] # Return empty rows on failure to prevent dashboard crash




   cur.close()
   cnx.close()
   return JSONResponse(serialize_rows(rows))








@app.get("/history")
def get_history(limit: int = 50):
   cnx = get_connection()
   cur = cnx.cursor(dictionary=True)
   cur.execute("SELECT * FROM SessionHistory ORDER BY id DESC LIMIT %s", (limit,))
   rows = cur.fetchall()
   cur.close()
   cnx.close()
   for r in rows:
       for key in ("start_time", "end_time"):
           if r.get(key):
               r[key] = r[key].strftime("%Y-%m-%d %H:%M:%S")
   return JSONResponse(rows)




# -------------------------
# Dashboard HTML (FINAL, CLEANED)
# -------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
   spindle_machines = ["SSB1080", "SSB1081"]
   test_machines = ["Dummy"]




   # --- DYNAMICALLY DETERMINE SPINDLE UI COLUMNS ---
   try:
       cnx_tags = get_connection()
       cur_tags = cnx_tags.cursor(dictionary=True)
       cur_tags.execute("SELECT name, path FROM parameters")
       db_tags = {r['name']: r['path'] for r in cur_tags.fetchall()}
       cnx_tags.close()
   except Exception:
       db_tags = {}
     
   final_spindle_tags_for_ui = load_dynamic_spindle_tags(db_tags)
   spindle_params_display = list(final_spindle_tags_for_ui.keys())
   # --- END DYNAMIC COLUMN DETERMINATION ---
 
   test_params_display = list(tags_test.keys())
 
   spindle_display = ["id", "timestamp", "machine_id"] + spindle_params_display
   test_display = ["id", "timestamp", "machine_id"] + test_params_display
 
   # List of parameters to populate the Visual tab dropdowns
   spindle_visual_options = [f'<option value="{p}">{p.replace("_", " ").title()}</option>' for p in spindle_params_display if p not in ["Spindle_type", "Bearing_Type"]]
   test_visual_options = [f'<option value="{p}">{p.replace("_", " ").title()}</option>' for p in test_params_display]




   # JavaScript parameter array (used for chart filtering)
   js_spindle_params = [p for p in spindle_params_display if p not in ["Spindle_type", "Bearing_Type"]]
   js_test_params = test_params_display




   # Pre-render Python variables for clean JS injection
   spindle_machine_options_html = ''.join(f'<option value="{m}">Spindle: {m}</option>' for m in spindle_machines)
   test_machine_options_html = ''.join(f'<option value="{m}">Test: {m}</option>' for m in test_machines)
 
   # Combined options for Parameter Management tab dropdowns
   param_machine_options_html = ''.join(f'<option value="{m}">{m}</option>' for m in spindle_machines + test_machines)




   spindle_visual_options_html = '\n'.join(spindle_visual_options)
   test_visual_options_html = '\n'.join(test_visual_options)




   # Use json.dumps for safe, robust injection of lists/dicts into JavaScript
   spindle_machines_js = json.dumps(spindle_machines)
   test_machines_js = json.dumps(test_machines)
   column_headers_js = json.dumps({"Spindle": spindle_display, "Test": test_display})
   js_spindle_params_js = json.dumps(js_spindle_params)
   js_test_params_js = json.dumps(js_test_params)




   html = f"""
   <!doctype html>
   <html>
   <head>
     <meta charset="utf-8" />
     <title>Machine Dashboard</title>
     <style>
       body{{font-family:Arial; margin:20px}}
       .card{{border:1px solid #ddd; padding:12px; border-radius:6px; margin-bottom:12px}}
       button{{padding:8px 12px; margin-right:6px; cursor:pointer}}
       table{{border-collapse:collapse; width:100%}}
       th,td{{border:1px solid #ccc; padding:6px; text-align:center; font-size:12px}}
       th{{background:#f3f3f3}}
       .tabcontent{{display:none}}
       .subtabcontent{{display:none}}
       .active{{background:#ddd}}
     </style>
     <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   </head>
   <body>
     <h2>Machine Dashboard</h2>




     <div style="margin-bottom:12px">
       <button class="tablink" onclick="openTab('mainTab', this)">Main</button>
       <button class="tablink" onclick="openTab('paramTab', this)">Parameter Management</button>
       <button class="tablink" onclick="openTab('visual', this)">Visual Representation</button>
     </div>




     <div id="mainTab" class="tabcontent" style="display:block;">
       <div class="card">
         <label>Machine:
           <select id="machineSelect">
             {spindle_machine_options_html}
           </select>
         </label>




         <label style="margin-left:20px">Type:
           <select id="typeSelect">
             <option value="Spindle">Spindle</option>
             <option value="Test">Test</option>
           </select>
         </label>
       
         <div style="margin-top:12px; margin-bottom:12px;">
           <label>From:
             <input type="date" id="fromDate" />
           </label>
           <label style="margin-left:10px">To:
             <input type="date" id="toDate" />
           </label>
         </div>




         <div style="margin-top:12px">
           <button onclick="startWrapper()">Start</button>
           <button onclick="stopPrompt()">Stop</button>
           <button onclick="loadRecords()">Refresh Records</button>
           <span style="margin-left:12px">Total (shown): <b id="count">0</b></span>
         </div>
       </div>




       <div class="card">
         <h3>Latest Records</h3>
         <table id="recordsTable">
           <thead id="recordsHead"></thead>
           <tbody id="recordsBody"></tbody>
         </table>
       </div>




       <div class="card">
         <h3>Session History</h3>
         <table id="historyTable">
           <thead><tr><th>ID</th><th>Machine</th><th>Type</th><th>Start</th><th>End</th><th>Duration(min)</th><th>Records</th><th>Remarks</th></tr></thead>
           <tbody id="historyBody"></tbody>
         </table>
       </div>
     </div>
   
     <div id="paramTab" class="tabcontent">
       <div class="card">
           <h3>Add Parameter</h3>
           <div style="margin-bottom: 12px;">
               <label>Machine:
                   <select id="paramMachineSelect">
                       {param_machine_options_html}
                   </select>
               </label>
               <label style="margin-left:20px">Type:
                   <select id="paramTypeSelect" onchange="loadParameters()">
                       <option value="Spindle">Spindle</option>
                       <option value="Test">Test</option>
                   </select>
               </label>
           </div>
         
           <form id="addParameterForm" onsubmit="addParameter(event)">
               <input type="text" name="parameter_name" placeholder="Parameter Name" required style="padding: 6px; width: 200px;">
               <input type="text" name="opc_ua_path" placeholder="OPC-UA Path (e.g. ns=2;s=...)" required style="padding: 6px; width: 400px; margin-left: 10px;">
               <button type="submit" style="margin-left: 10px;">Add</button>
               <p id="paramWarning" style="color: orange; font-size: 12px; margin-top: 5px;">Note: Adding parameters is currently only supported for 'Spindle' type and will affect all Spindle machines.</p>
           </form>
       </div>
       <div class="card">
           <h4>Custom Parameters List (Spindle/Dynamic Only)</h4>
           <table id="parametersTable">
               <thead><tr><th>ID</th><th>Name</th><th>OPC-UA Path</th></tr></thead>
               <tbody id="parametersBody"></tbody>
           </table>
           <button onclick="loadParameters()" style="margin-top: 10px;">Refresh Parameters List</button>
       </div>
     </div>




     <div id="visual" class="tabcontent">
       <h3>Visual Representation</h3>
       <div style="margin-bottom:12px; display: flex; align-items: center;">
         <button class="subtablink" onclick="openSubTab('visualSpindles', this)">Spindles</button>
         <button class="subtablink" onclick="openSubTab('visualTest', this)">Test</button>
         <button onclick="loadRecords()" style="margin-left: 20px;">Refresh Data</button>
         <label style="margin-left:20px">From:
           <input type="date" id="visualFromDate" onchange="document.getElementById('fromDate').value = this.value; loadRecords();"/>
         </label>
         <label style="margin-left:10px">To:
           <input type="date" id="visualToDate" onchange="document.getElementById('toDate').value = this.value; loadRecords();"/>
         </label>
       </div>




       <div id="visualSpindles" class="subtabcontent" style="display:block;">
         <h4>Spindle Parameters</h4>
         <label>Select Parameter:
           <select id="spindleParam" onchange="redrawCharts('Spindle')">
             <option value="all">All (Core Metrics)</option>
             {spindle_visual_options_html}
           </select>
         </label>
         <div id="spindleCharts"></div>
       </div>




       <div id="visualTest" class="subtabcontent">
         <h4>Test Parameters</h4>
         <label>Select Parameter:
           <select id="testParam" onchange="redrawCharts('Test')">
             <option value="all">All (Core Metrics)</option>
             {test_visual_options_html}
           </select>
         </label>
         <div id="testCharts"></div>
       </div>
     </div>




   <script>
     let currentMachine = 'SSB1080';
     let currentType = 'Spindle';
     let latestData = {{ Spindle: [], Test: [] }};
     let charts = {{ Spindle: {{}}, Test: {{}} }};




     const SPINDLE_MACHINES = {spindle_machines_js};
     const TEST_MACHINES = {test_machines_js};
     const columnHeaders = {column_headers_js};
   
     const spindleParams = {js_spindle_params_js};
     const testParams = {js_test_params_js};




     // --- UTILITY FUNCTIONS FOR CHARTS (FROM YOUR CODE) ---




     function binData(values, bins = 150) {{
         if (values.length <= bins) return values;
         const size = Math.floor(values.length / bins);
         let binned = [];
         for (let i = 0; i < bins; i++) {{
             let chunk = values.slice(i * size, (i + 1) * size);
             let avg = chunk.reduce((a, b) => a + b, 0) / chunk.length;
             binned.push(avg);
         }}
         return binned;
     }}




     function mean(arr) {{ return arr.reduce((a, b) => a + b, 0) / arr.length; }}
     function stdev(arr) {{ let m = mean(arr); return Math.sqrt(arr.reduce((a, b) => a + (b - m) ** 2, 0) / arr.length); }}




     function createChart(ctx, label, color) {{
         return new Chart(ctx, {{
             type: 'line',
             data: {{ labels: [], datasets: [
                 {{ label: label, data: [], borderColor: color, fill: false }},
                 {{ label: 'Outliers', data: [], borderColor: 'red', backgroundColor: 'red', showLine: false, pointRadius: 4, type: 'scatter' }}
             ] }},
             options: {{ responsive: true, scales: {{ x: {{ ticks: {{ maxRotation: 90, minRotation: 45 }} }} }} }}
         }});
     }}




     function updateChart(chart, data, param) {{
         let values = data.map(d => d[param] || 0);
         let labels = data.map(d => new Date(d.timestamp).toLocaleTimeString() || '');
       
         if (values.length > 150) {{
             labels = labels.filter((_, i) => i % (Math.floor(labels.length / 150) || 1) === 0);
             values = binData(values, 150);
         }}




         chart.data.labels = labels;
         chart.data.datasets[0].data = values;
       
         let m = mean(values), s = stdev(values);
         let outliers = values.map((v, i) => (v > m + 2 * s || v < m - 2 * s) ? {{ x: labels[i], y: v }} : null).filter(v => v);
       
         chart.data.datasets[1].data = outliers;
         chart.update();
     }}




     function redrawCharts(type) {{
         const container = type === 'Spindle' ? document.getElementById('spindleCharts') : document.getElementById('testCharts');
         const paramSel = document.getElementById(type === 'Spindle' ? 'spindleParam' : 'testParam').value;
         container.innerHTML = '';
         const params = (type === 'Spindle' ? spindleParams : testParams);
         const filtered = (paramSel === 'all' ? params : [paramSel]);




         filtered.forEach(p => {{
             let canvasDiv = document.createElement('div');
             canvasDiv.style.marginBottom = '20px';
             let canvas = document.createElement('canvas');
             canvasDiv.appendChild(canvas);
             container.appendChild(canvasDiv);
           
             charts[type][p] = createChart(canvas.getContext('2d'), p, 'blue');
             updateChart(charts[type][p], latestData[type], p);
         }});
     }}




     // --- UI/API CONTROL FUNCTIONS ---




     function openTab(tabId, el) {{
       document.querySelectorAll('.tabcontent').forEach(t => t.style.display = 'none');
       document.getElementById(tabId).style.display = 'block';
       document.querySelectorAll('.tablink').forEach(b => b.classList.remove('active'));
       el.classList.add('active');
     
       if (tabId === 'visual') {{
           // Sync main tab dates to visual tab dates
           document.getElementById('visualFromDate').value = document.getElementById('fromDate').value;
           document.getElementById('visualToDate').value = document.getElementById('toDate').value;
         
           const activeSubTab = document.querySelector('#visual .subtablink.active');
           if (!activeSubTab) {{
               const firstSubTab = document.querySelector('#visual .subtablink');
               if (firstSubTab) {{
                   openSubTab(firstSubTab.getAttribute('onclick').match(/'([^']+)'/)[1], firstSubTab);
               }}
           }}
       }} else if (tabId === 'mainTab') {{
           // Sync visual tab dates back to main tab dates
           document.getElementById('fromDate').value = document.getElementById('visualFromDate').value;
           document.getElementById('toDate').value = document.getElementById('visualToDate').value;
           loadRecords();
       }} else if (tabId === 'paramTab') {{
           // Load parameters for the currently selected machine/type in the param tab
           loadParameters();
       }}
     }}
   
     function openSubTab(subTabId, el) {{
       document.querySelectorAll('.subtabcontent').forEach(t => t.style.display = 'none');
       document.getElementById(subTabId).style.display = 'block';
       document.querySelectorAll('.subtablink').forEach(b => b.classList.remove('active'));
       el.classList.add('active');
     
       const type = subTabId.includes('Spindles') ? 'Spindle' : 'Test';
       redrawCharts(type);
     }}
   
     function updateMachineOptions(type) {{
         const machineSelect = document.getElementById('machineSelect');
         const machineList = (type === 'Spindle') ? SPINDLE_MACHINES : TEST_MACHINES;




         machineSelect.innerHTML = '';
         machineList.forEach(m => {{
             const option = document.createElement('option');
             option.value = m;
             option.textContent = (type === 'Spindle' ? 'Spindle: ' : 'Test: ') + m;
             machineSelect.appendChild(option);
         }});




         currentMachine = machineSelect.value;
     }}
   
     document.getElementById('machineSelect').addEventListener('change', (e)=> {{ currentMachine = e.target.value; loadRecords(); }});
   
     document.getElementById('typeSelect').addEventListener('change', (e)=> {{
         currentType = e.target.value;
         updateMachineOptions(currentType);
         loadRecords();
     }});
   
     // Add event listeners to the main date pickers
     document.getElementById('fromDate').addEventListener('change', loadRecords);
     document.getElementById('toDate').addEventListener('change', loadRecords);
   
     updateMachineOptions(currentType);




     async function startWrapper() {{
       const url = currentType === 'Spindle' ? `/start-spindle?machine=${{currentMachine}}` : `/start-test?machine=${{currentMachine}}`;
     
       try {{
           const res = await fetch(url);
           const j = await res.json();




           alert(j.status === 'success' ? `${{currentType}} reading started (Session: ${{j.session_id}})` : j.message || JSON.stringify(j));
           loadRecords();
           loadHistory();
       }} catch (error) {{
           console.error('Start Error:', error);
           alert(`Failed to start worker. Is the server running? Details: ${{error.message}}`);
       }}
     }}
   
     function stopPrompt() {{
         const remarks = prompt("Enter remarks for stopping the session (optional):");
         if (remarks !== null) {{
             stopWrapper(remarks);
         }}
     }}




     async function stopWrapper(remarks){{
       const url = currentType === 'Spindle' ? `/stop-spindle?remarks=${{encodeURIComponent(remarks)}}` : `/stop-test?remarks=${{encodeURIComponent(remarks)}}`;
     
       try {{
           const res = await fetch(url);
         
           // Check if the response is valid JSON before parsing
           const text = await res.text();
           let j;
           try {{
               j = JSON.parse(text);
           }} catch (e) {{
               // If parsing fails (meaning the server sent an HTML error page)
               console.error('Stop Error: Non-JSON response received:', text);
               alert(`Failed to stop worker. Details: Unexpected token 'I', "Internal S"... is not valid JSON. Check Python Console.`);
               return;
           }}
         
           alert(j.status === 'success' ? `${{currentType}} reading stopped (Session: ${{j.session_id}})` : j.message || JSON.stringify(j));
           loadRecords();
           loadHistory();
       }} catch (error) {{
            console.error('Stop Error (Network):', error);
           alert(`Failed to stop worker. Details: ${{error.message}}`);
       }}
     }}
   
     async function addParameter(event) {{
         event.preventDefault();
         const form = event.target;
         const formData = new FormData(form);
       
         const paramMachine = document.getElementById('paramMachineSelect').value;
         const paramType = document.getElementById('paramTypeSelect').value;




         // Append machine and type to form data
         formData.append('machine', paramMachine);
         formData.append('type_reading', paramType);
       
         const res = await fetch('/parameters/add', {{
             method: 'POST',
             body: formData,
         }});
       
         if (res.ok) {{
             const j = await res.json();
           
             // We don't need the trigger-restart API call anymore as it's done within /parameters/add
           
             alert(j.message || j.status);
             form.reset();
             loadParameters();
             loadRecords(); // Reload records to see new columns
         }} else {{
             const j = await res.json();
             alert(j.message || j.status);
         }}
     }}
   
     async function loadParameters() {{
         const paramMachine = document.getElementById('paramMachineSelect').value;
         const paramType = document.getElementById('paramTypeSelect').value;
       
         // Disable listing if type is not Spindle (since only Spindle supports dynamic tags)
         if (paramType !== 'Spindle') {{
             document.getElementById('parametersBody').innerHTML = '<tr><td colspan="3">Dynamic parameter listing is only supported for Spindle type.</td></tr>';
             document.getElementById('paramWarning').style.display = 'block';
             return;
         }}
         document.getElementById('paramWarning').style.display = 'none';




         const res = await fetch(`/parameters?machine=${{paramMachine}}&rtype=${{paramType}}`);
         const data = await res.json();
         const body = document.getElementById('parametersBody');
         body.innerHTML = '';
       
         if (data.length === 0) {{
             body.insertAdjacentHTML('beforeend', '<tr><td colspan="3">No custom parameters added.</td></tr>');
             return;
         }}
       
         data.forEach(p => {{
             const tr = `<tr>
               <td>${{p.id}}</td>
               <td>${{p.name}}</td>
               <td>${{p.path}}</td>
             </tr>`;
             body.insertAdjacentHTML('beforeend', tr);
         }});
     }}
   
     async function loadRecords(){{
       const fromDate = document.getElementById('fromDate').value;
       const toDate = document.getElementById('toDate').value;
     
       let url = `/records?machine=${{currentMachine}}&rtype=${{currentType}}&limit=200`;
       if (fromDate) {{
           url += `&from_date=${{fromDate}}`;
       }}
       if (toDate) {{
           // Add one day to the 'to' date to make the query range inclusive up to the end of the day
           const nextDay = new Date(toDate);
           nextDay.setDate(nextDay.getDate() + 1);
           url += `&to_date=${{nextDay.toISOString().split('T')[0]}}`;
       }}
     
       const res = await fetch(url);
       const data = await res.json();
       latestData[currentType] = data;
       document.getElementById('count').innerText = data.length;
       const head = document.getElementById('recordsHead');
       const body = document.getElementById('recordsBody');
       body.innerHTML = '';




       const keys = columnHeaders[currentType];
       let hrow = '<tr>';
       keys.forEach(k => {{
           if (k === 'timestamp') {{
               hrow += `<th>Date</th><th>Time</th>`;
           }} else {{
               hrow += `<th>${{k}}</th>`;
           }}
       }});
       hrow += '</tr>';
       head.innerHTML = hrow;




       if (data.length === 0) {{
           body.insertAdjacentHTML('beforeend', `<tr><td colspan="${{keys.length + 1}}">No records</td></tr>`);
           return;
       }}




       data.forEach(r => {{
           let row = '<tr>';
           keys.forEach(k => {{
               let val = r[k];
               if (val === null || val === undefined) {{
                   val = '';
               }}
               if (k === 'timestamp' && val) {{
                   let dt = new Date(val);
                   let datePart = dt.toLocaleDateString();
                   let timePart = dt.toLocaleTimeString();
                   row += `<td>${{datePart}}</td><td>${{timePart}}</td>`;
               }} else {{
                   row += `<td>${{val}}</td>`;
               }}
           }});
           row += '</tr>';
           body.insertAdjacentHTML('beforeend', row);
       }});
       redrawCharts(currentType);
   }}




     
       async function loadHistory(){{
           const res = await fetch(`/history?limit=50`);
           const data = await res.json();
           const body = document.getElementById('historyBody');
           body.innerHTML = '';
     
           const headers = document.querySelector('#historyTable thead tr');
           if (data.length > 0 && !headers.innerHTML.includes('<th>Remarks</th>')) {{
               headers.insertAdjacentHTML('beforeend', '<th>Remarks</th>');
           }}




           data.forEach(h => {{
           const tr = `<tr>
               <td>${{h.id}}</td>
               <td>${{h.machine_name}}</td>
               <td>${{h.reading_type}}</td>
               <td>${{h.start_time || ''}}</td>
               <td>${{h.end_time || ''}}</td>
               <td>${{h.duration_minutes !== null ? h.duration_minutes.toFixed(2) : ''}}</td>
               <td>${{h.records_logged || ''}}</td>
               <td>${{h.remarks || ''}}</td>
           </tr>`;
           body.insertAdjacentHTML('beforeend', tr);
           }});
       }}
   
     // Initial Setup
     document.querySelector('.tablink').classList.add('active');
     openTab('mainTab', document.querySelector('.tablink'));




     loadRecords();
     loadHistory();
     setInterval(loadRecords, 5000);
     setInterval(loadHistory, 15000);
   </script>
   </body>
   </html>
   """
   return HTMLResponse(content=html)








# Server startup has been moved to server.py
# if __name__ == "__main__":
#     import uvicorn
#     import os
#     ssl_keyfile = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')
#     ssl_certfile = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
#     uvicorn.run(
#         "modern:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         ssl_keyfile=ssl_keyfile,
#         ssl_certfile=ssl_certfile
#     )












# -------------------------
# Basic config / logging
# -------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(base_dir, "spindle_log.txt")




logging.basicConfig(
   filename=log_file,
   level=logging.INFO,
   format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("modern.py logging initialized")




# -------------------------
# MySQL config (HARDCODED - AVOID IN PRODUCTION)
# -------------------------
MYSQL_CONFIG = {
   "host": "localhost",
   "user": "spindless_user",
   "password": "Admin@123",
   "database": "spindless_db",
   "raise_on_warnings": True
}




def get_connection():
   return mysql.connector.connect(**MYSQL_CONFIG)




# -------------------------
# Kepware / OPC UA URLs (HARDCODED - AVOID IN PRODUCTION)
# -------------------------
KEPWARE_URL = "opc.tcp://163.157.19.134:49320"
NEW_KEPWARE_URL = "opc.tcp://INPUN4CE403CJ6W.corp.skf.net:49320"




kepware_client = None
kepware_new_client = None




# --- THREAD SAFETY FIX: Global Lock to prevent concurrent access to OPC UA clients ---
OPC_UA_LOCK = threading.Lock()




# --- CORE SANITIZATION FUNCTION ---
def sanitize_key(key: str) -> str:
   """Removes trailing/leading whitespace and replaces non-alphanumeric chars with underscores."""
   safe_name = key.strip()
   safe_name = safe_name.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('.', '_').replace(',', '')
   return safe_name




# -------------------------
# BASE TAGS (The 52 authoritative tags - Sanitized by dictionary creation)
# -------------------------
RAW_BASE_SPINDLE_TAGS = {
   # 9 Core Metrics
   "Grinding_spindle_mist_pressure": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding_spindle_mist_pressure",
   "GRINDING_SPINDLE_TEMP": "ns=2;s=IMX.CH_04_SSB1080.GRINDING_SPINDLE_TEMP",
   "GRINDING_SPINDLE_CURRENT": "ns=2;s=IMX.CH_04_SSB1080.GRINDING_SPINDLE_CURRENT",
   "SPINDLE_ACTUAL_SPEED": "ns=2;s=IMX.CH_04_SSB1080.SPINDLE_ACTUAL_SPEED",
   "02_HE4_NDE": "ns=2;s=IMX.CH_04_SSB1080.02_HE4_NDE",
   "02_HV_NDE": "ns=2;s=IMX.CH_04_SSB1080.02_HV_NDE",
   "02_HA_NDE": "ns=2;s=IMX.CH_04_SSB1080.02_HA_NDE",
   "01_HV_DE": "ns=2;s=IMX.CH_04_SSB1080.01_HV_DE",
   "01_HE4_DE": "ns=2;s=IMX.CH_04_SSB1080.01_HE4_DE",
   "01_HA_DE": "ns=2;s=IMX.CH_04_SSB1080.01_HA_DE",
 
   # 43 Application/Process Data Tags
 
    "Worn-out grinding wheel": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Worn-out grinding wheel",
    "WORKHEAD_RPM": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.WORKHEAD_RPM",
    "WAITING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.WAITING TIME",
    "TOTAL GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.TOTAL GRINDING TIME",
    "Spindle_type": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Spindle_type",
    "SPARK OUT TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.SPARK OUT TIME",
    "Sizematic knock-off 2 position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Sizematic knock-off 2 position",
    "Sizematic knock-off 1 position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Sizematic knock-off 1 position",
    "Rough_2_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_2_pwr",
    "Rough_2_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_2_feed_rate",
    "Rough_1_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_1_pwr",
    "Rough_1_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough_1_feed_rate",
    "ROUGH GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.ROUGH GRINDING TIME",
    "Rough- 1 Grinding Distance": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Rough- 1 Grinding Distance",
    "RING CHANGE TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.RING CHANGE TIME",
    "New wheel diameter when dressed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.New wheel diameter when dressed",
    "Maximum Grinding Spindle Speed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Maximum Grinding Spindle Speed",
    "Incremental retreat 1, initial": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Incremental retreat 1, initial",
    "Grinding_servo_torque": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding_servo_torque",
    "Grinding_axis_position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding_axis_position",
    "Grinding Wheel Speed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding Wheel Speed",
    "Grinding Wheel Peripheral Speed": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding Wheel Peripheral Speed",
    "Grinding finish position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding finish position",
    "Grinding compensation interval ctr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding compensation interval ctr",
    "Grinding compensation interval": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding compensation interval",
    "Grinding compensation": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding compensation",
    "Grinding (reference) position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding (reference) position",
    "Fine_grinding_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Fine_grinding_pwr",
    "Fine_grinding_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Fine_grinding_feed_rate",
    "FINE GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.FINE GRINDING TIME",
    "Early limit position finish size": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Early limit position finish size",
    "Dress-off a new wheel": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Dress-off a new wheel",
    "DRESSING_SPARK_OUT_TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_SPARK_OUT_TIME",
    "DRESSING_INTERVAL": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_INTERVAL",
    "DRESSING_INFEED_SPEED": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_INFEED_SPEED",
    "DRESSING_COMPENSATION": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING_COMPENSATION",
    "DRESSING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.DRESSING TIME",
    "Dressing starting position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Dressing starting position",
    "Dressing slide jump in position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Dressing slide jump in position",
    "Constant Grinding Wheel Speed If SA48 = 1": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Constant Grinding Wheel Speed If SA48 = 1",
    "Compensation memory": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Compensation memory",
    "Bearing_Type": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Bearing_Type",
    "Axis_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Axis_feed_rate",
    "Air_grinding_pwr": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Air_grinding_pwr",
    "Air_grinding_feed_rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Air_grinding_feed_rate",
    "AIR GRINDING TIME": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.AIR GRINDING TIME",
    "Actual wheel diameter": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Actual wheel diameter",
    "Marposs Gauge Enter position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Marposs Gauge Enter position",
    "Incremental retreat 2, initial": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Incremental retreat 2, initial",
    "Grinding slide jump in position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Grinding slide jump in position",
    "Gap eliminator safety position": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Gap eliminator safety position",
    "Air grind feed rate": "ns=2;s=Channel4 MITSUBISHI.SSB 1080.spindle analyatics.Air grind feed rate",
}












# --- CRITICAL SANITIZATION STEP APPLIED HERE ---
tags_spindle = {sanitize_key(k): v for k, v in RAW_BASE_SPINDLE_TAGS.items()}
BASE_SPINDLE_TAGS = tags_spindle.copy()




# tags_test (unchanged)
tags_test = {
   "spindle_type": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Type",
   "spindle_temp": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Temp",
   "spindle_speed": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Speed",
   "spindle_resistance": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Resistance",
   "spindle_megger": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Megger",
   "spindle_inductance": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Inductance",
   "spindle_current": "ns=2;s=Spindle_Room.Test_Rig.Spindle_Current",
   "mist_lub_pre_rear": "ns=2;s=Spindle_Room.Test_Rig.Mist_Lub_Pre_Rear",
   "mist_lub_pre_front": "ns=2;s=Spindle_Room.Test_Rig.Mist_Lub_Pre_Front",
   "lub_pump_oil_pre": "ns=2;s=Spindle_Room.Test_Rig.Lub_Pump_Oil_Pre",
   "lub_pump_air_pre": "ns=2;s=Spindle_Room.Test_Rig.Lub_Pump_Air_Pre",
   "chiller_water_pressure": "ns=2;s=Spindle_Room.Test_Rig.Chiller_Water_Pressure",
   "chiller_temp": "ns=2;s=Spindle_Room.Test_Rig.Chiller_Temp",
   "rear_bearing_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_Vibration",
   "rear_bearing_gen_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_gE_03",
   "rear_bearing_gen_vib2": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_gE_04",
   "rear_bearing_acc": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Rear_Acceleration",
   "front_bearing_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_Vibration",
   "front_bearing_gen_vib": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_gE_03",
   "front_bearing_gen_vib2": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_gE_04",
   "front_bearing_acc": "ns=2;s=IMX.SpindleTesting Jig.Spindle_Front_Acceleration",
}
BASE_TEST_TAGS = tags_test.copy()
# -------------------------
# Shared Variables
# -------------------------
last_values_spindle = {k: 0.0 for k in tags_spindle.keys()}
last_values_test = {k: 0.0 for k in tags_test.keys()}




running = {
   "spindle": {"thread": None, "stop_event": None, "session_id": None, "machine": None, "start_time": None},
    "test"  :{"thread" : None, "stop_event": None, "session_id":None,"machine": None, "stsrt_test":None}
}
# -------------------------
# Helper Functions
# -------------------------
def sql_identifier_from_key(key: str) -> str:
   k = key.replace("`", "``")
   return f"`{k}`"




def load_dynamic_spindle_tags(db_tags: Dict[str, str]) -> Dict[str, str]:
   """Loads all custom tags from DB and merges them with the base tags."""
   final_tags = BASE_SPINDLE_TAGS.copy()
   for raw_name, path in db_tags.items():
       # Sanitize the name read from the DB before using it as a key/column name
       safe_name = sanitize_key(raw_name)
       if safe_name:
           final_tags[safe_name] = path
   return final_tags




def ensure_tables():
   cnx = get_connection()
   cur = cnx.cursor()
   db_name = MYSQL_CONFIG["database"]
 
   # --- Helper to safely execute CREATE TABLE and ignore 'already exists' (Error 1050) ---
   def safe_create_table(sql, table_name):
       try:
           cur.execute(sql)
           cnx.commit()
       except mysql.connector.errors.ProgrammingError as e:
           # Error Code 1050: Table '...' already exists
           if e.errno == 1050:
               logging.info(f"Database setup: Table '{table_name}' already exists. Skipping creation.")
           else:
               raise e
       except Exception as e:
           logging.error(f"Error during initial {table_name} CREATE TABLE: {e}")




   # --- 0. Load ALL possible tags to ensure schema is wide enough (for ALTER TABLE below) ---
   db_tags = {}
   safe_create_table("""
   CREATE TABLE IF NOT EXISTS parameters (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       path VARCHAR(255) NOT NULL
   )
   """, "parameters")
 
   try:
       temp_cur = cnx.cursor(dictionary=True)
       temp_cur.execute("SELECT name, path FROM parameters")
       db_tags = {r['name']: r['path'] for r in temp_cur.fetchall()}
       temp_cur.close()
   except Exception:
       pass
     
   all_spindle_tags = load_dynamic_spindle_tags(db_tags)
 
   # --- 1. spindlereadings Table: Create/Alter (FULLY DYNAMIC) ---
   spindle_cols_sql = ["id INT AUTO_INCREMENT PRIMARY KEY", "timestamp DATETIME", "machine_id VARCHAR(100)"]
   for orig_key in all_spindle_tags.keys():
       col_ident = sql_identifier_from_key(orig_key)
       col_type = "VARCHAR(200)" if orig_key in ("Spindle_type", "Bearing_Type") else "DOUBLE"
       spindle_cols_sql.append(f"{col_ident} {col_type}")
         
   cols_sql = ",\n \t".join(spindle_cols_sql)
   create_spindle_sql = f"CREATE TABLE IF NOT EXISTS spindlereadings (\n \t{cols_sql}\n)"
 
   safe_create_table(create_spindle_sql, "spindlereadings")
     
   # Check and Add Missing Spindle Columns
   for col_name in all_spindle_tags.keys():
       col_ident = sql_identifier_from_key(col_name)
       col_type = "VARCHAR(200)" if col_name in ("Spindle_type", "Bearing_Type") else "DOUBLE"
     
       cur.execute("""
           SELECT 1
           FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = %s
             AND TABLE_NAME = 'spindlereadings'
             AND COLUMN_NAME = %s
       """, (db_name, col_name))
     
       if cur.fetchone() is None:
           logging.warning(f"Column '{col_name}' missing from spindlereadings. Adding it...")
           try:
               cur.execute(f"ALTER TABLE spindlereadings ADD COLUMN {col_ident} {col_type} DEFAULT NULL")
               cnx.commit()
               logging.info(f"Successfully added column '{col_name}'.")
           except Exception as e:
               logging.error(f"Failed to ALTER TABLE to add column '{col_name}': {e}")
             
   # --- 2. TestReading Table: Create/Alter (FULLY DYNAMIC) ---
   test_cols_sql = ["id INT AUTO_INCREMENT PRIMARY KEY", "timestamp DATETIME", "machine_id VARCHAR(100)"]
   for orig_key in tags_test.keys():
       col_ident = sql_identifier_from_key(orig_key)
       col_type = "INT" if orig_key == "spindle_type" else "DOUBLE"
       test_cols_sql.append(f"{col_ident} {col_type}")
         
   cols_sql = ",\n \t".join(test_cols_sql)
   create_test_sql = f"CREATE TABLE IF NOT EXISTS TestReading (\n \t{cols_sql}\n)"
 
   safe_create_table(create_test_sql, "TestReading")
     
   # Check and Add Missing Test Columns
   for col_name in tags_test.keys():
       col_ident = sql_identifier_from_key(col_name)
       col_type = "INT" if col_name == "spindle_type" else "DOUBLE"
     
       cur.execute("""
           SELECT 1
           FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = %s
             AND TABLE_NAME = 'TestReading'
             AND COLUMN_NAME = %s
       """, (db_name, col_name))
     
       if cur.fetchone() is None:
           logging.warning(f"Column '{col_name}' missing from TestReading. Adding it...")
           try:
               cur.execute(f"ALTER TABLE TestReading ADD COLUMN {col_ident} {col_type} DEFAULT NULL")
               cnx.commit()
               logging.info(f"Successfully added column '{col_name}'.")
           except Exception as e:
               logging.error(f"Failed to ALTER TABLE to add column '{col_name}': {e}")
             
 
   # --- 4. SessionHistory (FIXED: Checks for 'remarks') ---
   safe_create_table("""
   CREATE TABLE IF NOT EXISTS SessionHistory (
       id INT AUTO_INCREMENT PRIMARY KEY,
       machine_name VARCHAR(100),
       reading_type ENUM('Spindle','Test'),
       start_time DATETIME,
       end_time DATETIME,
       duration_minutes DOUBLE,
       records_logged INT,
       remarks VARCHAR(500)
   )
   """, "SessionHistory")
 
   # Ensure remarks column exists even if old table was missing it
   try:
       cur.execute("""
           SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'SessionHistory' AND COLUMN_NAME = 'remarks'
       """, (db_name, ))
       if cur.fetchone() is None:
            cur.execute("ALTER TABLE SessionHistory ADD COLUMN remarks VARCHAR(500) DEFAULT NULL")
            cnx.commit()
            logging.info("Successfully added missing 'remarks' column to SessionHistory.")
   except Exception as e:
       logging.error(f"Failed to ensure 'remarks' column: {e}")


   # --- 5. spindle_predictions (For ML predictions) ---
   safe_create_table("""
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
   )
   """, "spindle_predictions")


   cnx.commit()
   cur.close()
   cnx.close()




def connect_kepware():
   global kepware_client, kepware_new_client
   try:
       kepware_client = Client(KEPWARE_URL)
       kepware_client.connect()
       logging.info("Connected to Kepware OPC UA server (spindle).")
   except Exception as e:
       logging.error(f"Spindle Kepware connection failed: {e}")
       kepware_client = None




   try:
       kepware_new_client = Client(NEW_KEPWARE_URL)
       kepware_new_client.connect()
       logging.info("Connected to new Kepware (test).")
   except Exception as e:
       logging.error(f"Test Kepware connection failed: {e}")
       kepware_new_client = None
     
def safe_get_node_value(client: Client, nodeid: str, last_values_map: dict, key: str):
   try:
       if client is None:
           return last_values_map.get(key, 0.0)
     
       node = client.get_node(nodeid)
       val = node.get_value()
     
       if key in ("Spindle_type", "Bearing_Type"):
           val = str(val) if val is not None else ""
       elif val is not None:
           try:
               val = float(val)
           except (ValueError, TypeError):
               val = 0.0
       else:
           val = 0.0
         
       last_values_map[key] = val
       return val
   except Exception as e:
       logging.error(f"Failed reading node {nodeid} ({key}): {e}")
       return last_values_map.get(key, 0.0)




def get_kepware_data_for_tags(client: Client, tags: Dict[str, str], last_values_map: dict):
   data = {}
   for param, nodeid in tags.items():
       data[param] = safe_get_node_value(client, nodeid, last_values_map, param)
   return data




def log_session_start(machine_name: str, reading_type: str) -> int:
   cnx = get_connection()
   cur = cnx.cursor()
   start_time = datetime.now()
 
   sql = "INSERT INTO SessionHistory (machine_name, reading_type, start_time, records_logged, remarks) VALUES (%s, %s, %s, %s, %s)"
   cur.execute(sql, (machine_name, reading_type.capitalize(), start_time, 0, None))
 
   session_id = cur.lastrowid
   cnx.commit()
   cur.close()
   cnx.close()
   logging.info(f"Session started: id={session_id}, machine={machine_name}, type={reading_type}")
   return session_id




# FIX: Added try/except for robustness against DB failure during stop
def log_session_stop(session_id: int, start_time: datetime, end_time: datetime, machine_name: str, reading_type: str):
   cnx = None
   cur = None
   records_logged = 0
   duration_min = (end_time - start_time).total_seconds() / 60.0




   try:
       cnx = get_connection()
       cur = cnx.cursor()




       # 1. Get record count
       table_name = "spindlereadings" if reading_type == "Spindle" else "TestReading"
       cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE machine_id=%s AND timestamp BETWEEN %s AND %s",
                      (machine_name, start_time, end_time))
       records_logged = cur.fetchone()[0]
     
       # 2. Update SessionHistory
       cur.execute("""
           UPDATE SessionHistory
           SET end_time=%s, duration_minutes=%s, records_logged=%s
           WHERE id=%s
       """, (end_time, duration_min, records_logged, session_id))
       cnx.commit()
     
   except Exception as e:
       logging.error(f"FATAL DB ERROR: Failed to finalize session {session_id} in log_session_stop: {e}")
     
   finally:
       # Ensure cleanup runs regardless of success or failure
       if cur: cur.close()
       if cnx: cnx.close()
     
       logging.info(f"Session stopped: id={session_id}, records={records_logged}, duration_min={duration_min:.2f}")




# -------------------------
# Worker: Spindle (Handles dynamic tags and robust DB connection management)
# -------------------------
def spindle_worker(session_id: int, machine_id: str, start_time: datetime, stop_event: threading.Event):
   logging.info(f"Spindle worker started for session {session_id}, machine {machine_id}")
 
   cnx = None
   cur = None




   # DYNAMIC TAGS LOADED HERE: This ensures new parameters are picked up
   try:
       cnx_tags = get_connection()
       cur_tags = cnx_tags.cursor(dictionary=True)
       cur_tags.execute("SELECT name, path FROM parameters")
       db_tags = {r['name']: r['path'] for r in cur_tags.fetchall()}
       cnx_tags.close()
     
       # Use the dynamic list inside the worker
       local_tags_spindle = load_dynamic_spindle_tags(db_tags)
       local_last_values = {k: 0.0 for k in local_tags_spindle.keys()}
     
   except Exception as e:
       logging.error(f"Spindle worker FAILED TO LOAD DYNAMIC TAGS: {e}. Using base tags only.")
       local_tags_spindle = BASE_SPINDLE_TAGS.copy()
       local_last_values = {k: 0.0 for k in BASE_SPINDLE_TAGS.keys()}




   try:
       # 1. Open the main DB connection that runs inside the loop
       cnx = get_connection()
       cur = cnx.cursor()




       counter = 0
       while not stop_event.is_set():
           timestamp = datetime.now()
           # USE LOCAL TAGS/LAST VALUES MAPS
           data = get_kepware_data_for_tags(kepware_client, local_tags_spindle, local_last_values)
         
           # Application Logic: Set current to 0.0 if below 5
           current_val = data.get("GRINDING_SPINDLE_CURRENT", 0.0) or 0.0
         
           # ----------------------------------------------------------------------------------
           # NEW REQUIREMENT: Skip insertion if GRINDING_SPINDLE_CURRENT < 5
           # ----------------------------------------------------------------------------------
           if isinstance(current_val, (int, float)) and current_val < 5:
               logging.info(f"Spindle current ({current_val:.2f}) is less than 5. Skipping DB insert for session {session_id}.")
               time.sleep(20)
               continue # Skip the rest of the loop and start the next iteration
           # ----------------------------------------------------------------------------------




           data["GRINDING_SPINDLE_CURRENT"] = current_val




           # Build SQL statement dynamically for the complete tag list
           cols = ["timestamp", "machine_id"] + list(local_tags_spindle.keys())
           col_sql = ",".join([sql_identifier_from_key(c) for c in cols])
           placeholders = ",".join(["%s"] * len(cols))
         
           # Values retrieved here are mapped to the ordered keys
           values = [timestamp, machine_id] + [data.get(k) for k in local_tags_spindle.keys()]
         
           cur.execute(f"INSERT INTO spindlereadings ({col_sql}) VALUES ({placeholders})", tuple(values))
           cnx.commit()
           counter += 1
           if counter % 5 == 0:
               logging.info(f"Spindle insert #{counter} for session {session_id}: machine={machine_id}")
           time.sleep(20)
         
   except Exception as e:
       logging.error(f"Spindle worker exception: {e}")
     
   finally:
       # CRITICAL FIX: Ensure session end is logged and connections are closed
       end_time = datetime.now()
       log_session_stop(session_id, start_time, end_time, machine_id, "Spindle")
     
       # Explicitly close the worker's own connection/cursor
       if cur: cur.close()
       if cnx: cnx.close()
     
       logging.info(f"Spindle worker finished for session {session_id}")








# -------------------------
# Worker: Test (Robust DB connection management)
# -------------------------
def test_worker(session_id: int, machine_id: str, start_time: datetime, stop_event: threading.Event):
   logging.info(f"Test worker started for session {session_id}, machine {machine_id}")
 
   cnx = None
   cur = None
 
   try:
       # Open the main DB connection
       cnx = get_connection()
       cur = cnx.cursor()
     
       counter = 0
       while not stop_event.is_set():
           timestamp = datetime.now()
           data = get_kepware_data_for_tags(kepware_new_client, tags_test, last_values_test)




           cur.execute(f"""
               INSERT INTO TestReading (
                   timestamp, machine_id, spindle_type, spindle_temp, spindle_speed,
                   spindle_resistance, spindle_megger, spindle_inductance, spindle_current,
                   mist_lub_pre_rear, mist_lub_pre_front, lub_pump_oil_pre, lub_pump_air_pre,
                   chiller_water_pressure, chiller_temp, rear_bearing_vib, rear_bearing_gen_vib,
                   rear_bearing_gen_vib2, rear_bearing_acc, front_bearing_vib, front_bearing_gen_vib,
                   front_bearing_gen_vib2, front_bearing_acc
               ) VALUES (
                   %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
               )
           """, (
               timestamp, machine_id, data.get("spindle_type", 0), data.get("spindle_temp", 0.0),
               data.get("spindle_speed", 0.0), data.get("spindle_resistance", 0.0), data.get("spindle_megger", 0.0),
               data.get("spindle_inductance", 0.0), data.get("spindle_current", 0.0), data.get("mist_lub_pre_rear", 0.0),
               data.get("mist_lub_pre_front", 0.0), data.get("lub_pump_oil_pre", 0.0), data.get("lub_pump_air_pre", 0.0),
               data.get("chiller_water_pressure", 0.0), data.get("chiller_temp", 0.0), data.get("rear_bearing_vib", 0.0),
               data.get("rear_bearing_gen_vib", 0.0), data.get("rear_bearing_gen_vib2", 0.0), data.get("rear_bearing_acc", 0.0),
               data.get("front_bearing_vib", 0.0), data.get("front_bearing_gen_vib", 0.0), data.get("front_bearing_gen_vib2", 0.0),
               data.get("front_bearing_acc", 0.0)
           ))
           cnx.commit()
           counter += 1
           if counter % 5 == 0:
                logging.info(f"Test insert #{counter} for session {session_id}: machine={machine_id}")
           time.sleep(20)
         
   except Exception as e:
       logging.error(f"Test worker exception: {e}")
     
   finally:
       end_time = datetime.now()
       log_session_stop(session_id, start_time, end_time, machine_id, "Test")
     
       # Explicitly close the worker's own connection/cursor
       if cur: cur.close()
       if cnx: cnx.close()
     
       logging.info(f"Test worker finished for session {session_id}")
     
# -------------------------
# FastAPI App & Endpoints
# -------------------------
app = FastAPI()




@app.on_event("startup")
def startup_event():
   ensure_tables()
   try:
       connect_kepware()
   except Exception as e:
       logging.error(f"Startup: Kepware connect issue: {e}")




   # Auto-start spindle session logic
   if running["spindle"]["thread"] is None:
       dynamic_restart_spindle_worker("SSB1080", "Spindle")




# --- RESTART HELPER FUNCTION ---
def dynamic_restart_spindle_worker(machine_id: str, type_reading: str):
   """Stops the current worker and immediately starts a new one."""
 
   type_reading_lower = type_reading.lower()
   current_info = running[type_reading_lower]
 
   # 1. Stop existing thread if running
   if current_info["thread"] is not None:
       logging.info(f"Signaling current {type_reading} worker to stop for restart.")
       current_info["stop_event"].set()
       current_info["thread"].join()
     
   # 2. START new thread
   logging.info(f"Starting new {type_reading} worker for machine {machine_id}.")
   stop_event = threading.Event()
   start_time = datetime.now()
 
   # IMPORTANT: We must ensure the DB schema is up to date BEFORE starting the logger
   ensure_tables()
 
   session_id = log_session_start(machine_id, type_reading)
 
   worker_target = spindle_worker if type_reading == "Spindle" else test_worker
 
   t = threading.Thread(target=worker_target,
                        args=(session_id, machine_id, start_time, stop_event),
                        daemon=True)
                       
   running[type_reading.lower()].update({
       "thread": t,
       "stop_event": stop_event,
       "session_id": session_id,
       "machine": machine_id,
       "start_time": start_time
   })
 
   t.start()
   return session_id




# --- ADDED API ENDPOINT TO TRIGGER RESTART FROM JAVASCRIPT ---
@app.get("/trigger-spindle-restart")
def trigger_spindle_restart(machine: str = "SSB1080"):
   """API endpoint to manually trigger the worker restart and schema update."""
   try:
       session_id = dynamic_restart_spindle_worker(machine, "Spindle")
       return JSONResponse({
           "status": "success",
           "message": f"Spindle worker successfully restarted with new configuration.",
           "session_id": session_id
       })
   except Exception as e:
       logging.error(f"Failed to trigger dynamic restart: {e}")
       return JSONResponse({"status": "error", "message": f"Failed to restart worker: {e}"}, status_code=500)
# -----------------------------------------------------------------------








# --- PARAMETER MANAGEMENT ENDPOINTS ---




@app.get("/parameters")
def get_parameters(machine: str = "SSB1080", rtype: str = "Spindle"):
   """Retrieves all custom parameters from the database. Machine/Type parameters are not supported
      in the backend yet, so this always returns Spindle dynamic tags."""
 
   # NOTE: The current system only stores dynamic tags globally in the 'parameters' table
   # which is merged with BASE_SPINDLE_TAGS.
   # For a full implementation, the 'parameters' table would need machine/type columns.
 
   cnx = get_connection()
   cur = cnx.cursor(dictionary=True)
 
   # Only retrieving global custom parameters
   cur.execute("SELECT id, name, path FROM parameters ORDER BY id DESC")
   rows = cur.fetchall()
 
   cur.close()
   cnx.close()
   return JSONResponse(rows)




@app.post("/parameters/add")
async def add_parameter(
   parameter_name: str = Form(...),
   opc_ua_path: str = Form(...),
   machine: str = Form(...),
   type_reading: str = Form(...)
):
   if not parameter_name or not opc_ua_path:
       return JSONResponse(
           status_code=400,
           content={"status": "error", "message": "Parameter Name and OPC-UA Path cannot be empty."}
       )




   # NOTE: Since the backend only supports dynamic tags for the Spindle table
   # and the logic uses a global 'parameters' table, the machine/type parameters
   # are currently ignored for insertion logic but passed for UI compatibility.
   if type_reading != "Spindle":
       return JSONResponse(
           status_code=400,
           content={"status": "error", "message": "Adding parameters is currently only supported for 'Spindle' type."}
       )
     
   try:
       cnx = get_connection()
       cur = cnx.cursor()




       # Check duplicate NAME
       cur.execute("SELECT id FROM parameters WHERE name = %s", (parameter_name,))
       if cur.fetchone():
           cur.close()
           cnx.close()
           return JSONResponse(
               status_code=409,
               content={"status": "error", "message": f"Parameter '{parameter_name}' already exists."}
           )




       # Check duplicate PATH
       cur.execute("SELECT id, name FROM parameters WHERE path = %s", (opc_ua_path,))
       row = cur.fetchone()
       if row:
           cur.close()
           cnx.close()
           return JSONResponse(
               status_code=409,
               content={"status": "error", "message": f"OPC-UA Path already used by parameter '{row[1]}'."}
           )




       # Insert new parameter if both name and path are unique (Global insert)
       sql = "INSERT INTO parameters (name, path) VALUES (%s, %s)"
       cur.execute(sql, (parameter_name, opc_ua_path))
       cnx.commit()
       cur.close()
       cnx.close()




       # Restart spindle worker and ensure schema update
       dynamic_restart_spindle_worker(machine, type_reading)




       return JSONResponse(content={
           "status": "success",
           "message": f"Parameter '{parameter_name}' added. Spindle worker restarted to include new tag."
       })




   except Exception as e:
       logging.error(f"Failed to add parameter: {e}")
       return JSONResponse(
           status_code=500,
           content={"status": "error", "message": f"Database error: {e}"})
# --- START/STOP ENDPOINTS (Dashboard compatibility shims) ---




@app.get("/start-spindle")
def start_spindle(machine: str = "SSB1080"):
   type_reading = "Spindle"
   if running[type_reading.lower()]["thread"] is not None:
       return JSONResponse({"status": "error", "message": "Spindle already running"})
 
   session_id = dynamic_restart_spindle_worker(machine, type_reading)
   return JSONResponse({"status": "success", "session_id": session_id})




@app.get("/stop-spindle")
def stop_spindle_get(remarks: Optional[str] = ""):
   return stop_worker("spindle", remarks)




@app.get("/start-test")
def start_test(machine: str = "SSB1080"):
   type_reading = "Test"
   if running[type_reading.lower()]["thread"] is not None:
       return JSONResponse({"status": "error", "message": "Test already running"})
 
   # We still use the old start logic for Test worker as it's not dynamic yet
   stop_event = threading.Event()
   start_time = datetime.now()
   session_id = log_session_start(machine, type_reading)
 
   t = threading.Thread(target=test_worker, args=(session_id, machine, start_time, stop_event), daemon=True)
   running[type_reading.lower()].update({"thread": t, "stop_event": stop_event, "session_id": session_id, "machine": machine, "start_time": start_time})
   t.start()
   return JSONResponse({"status": "success", "session_id": session_id})




@app.get("/stop-test")
def stop_test_get(remarks: Optional[str] = ""):
   return stop_worker("test", remarks)




def stop_worker(type_reading: str, remarks: Optional[str] = ""):
   type_reading = type_reading.lower()
   if type_reading not in ("spindle", "test"):
       return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid type"})




   thread_info = running[type_reading]
   if thread_info["thread"] is None:
       return JSONResponse(content={"status": "error", "message": f"{type_reading.capitalize()} reading is not running"})




   try:
       thread_info["stop_event"].set()
       thread_info["thread"].join()




       if remarks:
           try:
               cnx = get_connection()
               cur = cnx.cursor()
               sql = "UPDATE SessionHistory SET remarks=%s WHERE id=%s"
               cur.execute(sql, (remarks, thread_info["session_id"]))
               cnx.commit()
               cur.close()
               cnx.close()
           except Exception as e:
               logging.error(f"Failed to update remarks for session {thread_info['session_id']}: {e}")




       session_id = thread_info["session_id"]
       running[type_reading] = {"thread": None, "stop_event": None, "session_id": None, "machine": None, "start_time": None}




       return JSONResponse(content={"status": "success", "session_id": session_id, "message": f"{type_reading.capitalize()} reading stopped."})




   except Exception as e:
       logging.error(f"Stop worker error: {e}")
       return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})




# --- UTILITY ENDPOINTS ---




def serialize_rows(rows):
   serialized = []
   for row in rows:
       new_row = {}
       for key, value in row.items():
           if isinstance(value, datetime):
               new_row[key] = value.isoformat()
           else:
               new_row[key] = value
       serialized.append(new_row)
   return serialized




@app.get("/records")
def get_records(machine: str = "SSB1080", rtype: str = "Spindle", limit: Optional[int] = None, from_date: Optional[str] = None, to_date: Optional[str] = None):
   cnx = get_connection()
   cur = cnx.cursor(dictionary=True)
 
   # We must ensure we get the full list of columns to query!
   db_tags = {}
   table_name = "spindlereadings" if rtype == "Spindle" else "TestReading"
 
   if rtype == "Spindle":
       try:
           temp_cur = cnx.cursor(dictionary=True)
           temp_cur.execute("SELECT name, path FROM parameters")
           db_tags = {r['name']: r['path'] for r in temp_cur.fetchall()}
           temp_cur.close()
       except Exception:
           pass




       final_tag_list = load_dynamic_spindle_tags(db_tags)
     
       # Build SELECT list:
       all_cols = ["id", "timestamp", "machine_id"] + list(final_tag_list.keys())
       select_cols = ",".join([sql_identifier_from_key(c) for c in all_cols])
     
       query = f"SELECT {select_cols} FROM {table_name} WHERE machine_id=%s"
     
   else: # Test Rig (Static)
       query = f"SELECT * FROM {table_name} WHERE machine_id=%s"




   params = [machine]
 
   # --- DATE FILTERING LOGIC ---
   if from_date:
       query += " AND timestamp >= %s"
       params.append(from_date)
     
   if to_date:
       # The JavaScript increments the 'to' date by 1 day to make the range inclusive.
       # We use '<' here to filter records up to, but not including, the start of the next day.
       query += " AND timestamp < %s"
       params.append(to_date)
   # ----------------------------




   query += " ORDER BY timestamp DESC"




   if limit is not None and limit > 0:
       query += " LIMIT %s"
       params.append(limit)
 
   # Execute the dynamically built query
   try:
       cur.execute(query, tuple(params))
       rows = cur.fetchall()
   except mysql.connector.errors.ProgrammingError as e:
       # This catches errors like "Unknown column 'CLAMP_PRESSURE'"
       logging.error(f"Records query failed (likely missing column): {e}")
       rows = [] # Return empty rows on failure to prevent dashboard crash




   cur.close()
   cnx.close()
   return JSONResponse(serialize_rows(rows))








@app.get("/history")
def get_history(limit: int = 50):
   cnx = get_connection()
   cur = cnx.cursor(dictionary=True)
   cur.execute("SELECT * FROM SessionHistory ORDER BY id DESC LIMIT %s", (limit,))
   rows = cur.fetchall()
   cur.close()
   cnx.close()
   for r in rows:
       for key in ("start_time", "end_time"):
           if r.get(key):
               r[key] = r[key].strftime("%Y-%m-%d %H:%M:%S")
   return JSONResponse(rows)




# -------------------------
# Dashboard HTML (FINAL, CLEANED)
# -------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
   spindle_machines = ["SSB1080", "SSB1081"]
   test_machines = ["Dummy"]




   # --- DYNAMICALLY DETERMINE SPINDLE UI COLUMNS ---
   try:
       cnx_tags = get_connection()
       cur_tags = cnx_tags.cursor(dictionary=True)
       cur_tags.execute("SELECT name, path FROM parameters")
       db_tags = {r['name']: r['path'] for r in cur_tags.fetchall()}
       cnx_tags.close()
   except Exception:
       db_tags = {}
     
   final_spindle_tags_for_ui = load_dynamic_spindle_tags(db_tags)
   spindle_params_display = list(final_spindle_tags_for_ui.keys())
   # --- END DYNAMIC COLUMN DETERMINATION ---
 
   test_params_display = list(tags_test.keys())
 
   spindle_display = ["id", "timestamp", "machine_id"] + spindle_params_display
   test_display = ["id", "timestamp", "machine_id"] + test_params_display
 
   # List of parameters to populate the Visual tab dropdowns
   spindle_visual_options = [f'<option value="{p}">{p.replace("_", " ").title()}</option>' for p in spindle_params_display if p not in ["Spindle_type", "Bearing_Type"]]
   test_visual_options = [f'<option value="{p}">{p.replace("_", " ").title()}</option>' for p in test_params_display]




   # JavaScript parameter array (used for chart filtering)
   js_spindle_params = [p for p in spindle_params_display if p not in ["Spindle_type", "Bearing_Type"]]
   js_test_params = test_params_display




   # Pre-render Python variables for clean JS injection
   spindle_machine_options_html = ''.join(f'<option value="{m}">Spindle: {m}</option>' for m in spindle_machines)
   test_machine_options_html = ''.join(f'<option value="{m}">Test: {m}</option>' for m in test_machines)
 
   # Combined options for Parameter Management tab dropdowns
   param_machine_options_html = ''.join(f'<option value="{m}">{m}</option>' for m in spindle_machines + test_machines)




   spindle_visual_options_html = '\n'.join(spindle_visual_options)
   test_visual_options_html = '\n'.join(test_visual_options)




   # Use json.dumps for safe, robust injection of lists/dicts into JavaScript
   spindle_machines_js = json.dumps(spindle_machines)
   test_machines_js = json.dumps(test_machines)
   column_headers_js = json.dumps({"Spindle": spindle_display, "Test": test_display})
   js_spindle_params_js = json.dumps(js_spindle_params)
   js_test_params_js = json.dumps(js_test_params)




   html = f"""
   <!doctype html>
   <html>
   <head>
     <meta charset="utf-8" />
     <title>Machine Dashboard</title>
     <style>
       body{{font-family:Arial; margin:20px}}
       .card{{border:1px solid #ddd; padding:12px; border-radius:6px; margin-bottom:12px}}
       button{{padding:8px 12px; margin-right:6px; cursor:pointer}}
       table{{border-collapse:collapse; width:100%}}
       th,td{{border:1px solid #ccc; padding:6px; text-align:center; font-size:12px}}
       th{{background:#f3f3f3}}
       .tabcontent{{display:none}}
       .subtabcontent{{display:none}}
       .active{{background:#ddd}}
     </style>
     <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   </head>
   <body>
     <h2>Machine Dashboard</h2>




     <div style="margin-bottom:12px">
       <button class="tablink" onclick="openTab('mainTab', this)">Main</button>
       <button class="tablink" onclick="openTab('paramTab', this)">Parameter Management</button>
       <button class="tablink" onclick="openTab('visual', this)">Visual Representation</button>
     </div>




     <div id="mainTab" class="tabcontent" style="display:block;">
       <div class="card">
         <label>Machine:
           <select id="machineSelect">
             {spindle_machine_options_html}
           </select>
         </label>




         <label style="margin-left:20px">Type:
           <select id="typeSelect">
             <option value="Spindle">Spindle</option>
             <option value="Test">Test</option>
           </select>
         </label>
       
         <div style="margin-top:12px; margin-bottom:12px;">
           <label>From:
             <input type="date" id="fromDate" />
           </label>
           <label style="margin-left:10px">To:
             <input type="date" id="toDate" />
           </label>
         </div>




         <div style="margin-top:12px">
           <button onclick="startWrapper()">Start</button>
           <button onclick="stopPrompt()">Stop</button>
           <button onclick="loadRecords()">Refresh Records</button>
           <span style="margin-left:12px">Total (shown): <b id="count">0</b></span>
         </div>
       </div>




       <div class="card">
         <h3>Latest Records</h3>
         <table id="recordsTable">
           <thead id="recordsHead"></thead>
           <tbody id="recordsBody"></tbody>
         </table>
       </div>




       <div class="card">
         <h3>Session History</h3>
         <table id="historyTable">
           <thead><tr><th>ID</th><th>Machine</th><th>Type</th><th>Start</th><th>End</th><th>Duration(min)</th><th>Records</th><th>Remarks</th></tr></thead>
           <tbody id="historyBody"></tbody>
         </table>
       </div>
     </div>
   
     <div id="paramTab" class="tabcontent">
       <div class="card">
           <h3>Add Parameter</h3>
           <div style="margin-bottom: 12px;">
               <label>Machine:
                   <select id="paramMachineSelect">
                       {param_machine_options_html}
                   </select>
               </label>
               <label style="margin-left:20px">Type:
                   <select id="paramTypeSelect" onchange="loadParameters()">
                       <option value="Spindle">Spindle</option>
                       <option value="Test">Test</option>
                   </select>
               </label>
           </div>
         
           <form id="addParameterForm" onsubmit="addParameter(event)">
               <input type="text" name="parameter_name" placeholder="Parameter Name" required style="padding: 6px; width: 200px;">
               <input type="text" name="opc_ua_path" placeholder="OPC-UA Path (e.g. ns=2;s=...)" required style="padding: 6px; width: 400px; margin-left: 10px;">
               <button type="submit" style="margin-left: 10px;">Add</button>
               <p id="paramWarning" style="color: orange; font-size: 12px; margin-top: 5px;">Note: Adding parameters is currently only supported for 'Spindle' type and will affect all Spindle machines.</p>
           </form>
       </div>
       <div class="card">
           <h4>Custom Parameters List (Spindle/Dynamic Only)</h4>
           <table id="parametersTable">
               <thead><tr><th>ID</th><th>Name</th><th>OPC-UA Path</th></tr></thead>
               <tbody id="parametersBody"></tbody>
           </table>
           <button onclick="loadParameters()" style="margin-top: 10px;">Refresh Parameters List</button>
       </div>
     </div>




     <div id="visual" class="tabcontent">
       <h3>Visual Representation</h3>
       <div style="margin-bottom:12px; display: flex; align-items: center;">
         <button class="subtablink" onclick="openSubTab('visualSpindles', this)">Spindles</button>
         <button class="subtablink" onclick="openSubTab('visualTest', this)">Test</button>
         <button onclick="loadRecords()" style="margin-left: 20px;">Refresh Data</button>
         <label style="margin-left:20px">From:
           <input type="date" id="visualFromDate" onchange="document.getElementById('fromDate').value = this.value; loadRecords();"/>
         </label>
         <label style="margin-left:10px">To:
           <input type="date" id="visualToDate" onchange="document.getElementById('toDate').value = this.value; loadRecords();"/>
         </label>
       </div>




       <div id="visualSpindles" class="subtabcontent" style="display:block;">
         <h4>Spindle Parameters</h4>
         <label>Select Parameter:
           <select id="spindleParam" onchange="redrawCharts('Spindle')">
             <option value="all">All (Core Metrics)</option>
             {spindle_visual_options_html}
           </select>
         </label>
         <div id="spindleCharts"></div>
       </div>




       <div id="visualTest" class="subtabcontent">
         <h4>Test Parameters</h4>
         <label>Select Parameter:
           <select id="testParam" onchange="redrawCharts('Test')">
             <option value="all">All (Core Metrics)</option>
             {test_visual_options_html}
           </select>
         </label>
         <div id="testCharts"></div>
       </div>
     </div>




   <script>
     let currentMachine = 'SSB1080';
     let currentType = 'Spindle';
     let latestData = {{ Spindle: [], Test: [] }};
     let charts = {{ Spindle: {{}}, Test: {{}} }};




     const SPINDLE_MACHINES = {spindle_machines_js};
     const TEST_MACHINES = {test_machines_js};
     const columnHeaders = {column_headers_js};
   
     const spindleParams = {js_spindle_params_js};
     const testParams = {js_test_params_js};




     // --- UTILITY FUNCTIONS FOR CHARTS (FROM YOUR CODE) ---




     function binData(values, bins = 150) {{
         if (values.length <= bins) return values;
         const size = Math.floor(values.length / bins);
         let binned = [];
         for (let i = 0; i < bins; i++) {{
             let chunk = values.slice(i * size, (i + 1) * size);
             let avg = chunk.reduce((a, b) => a + b, 0) / chunk.length;
             binned.push(avg);
         }}
         return binned;
     }}




     function mean(arr) {{ return arr.reduce((a, b) => a + b, 0) / arr.length; }}
     function stdev(arr) {{ let m = mean(arr); return Math.sqrt(arr.reduce((a, b) => a + (b - m) ** 2, 0) / arr.length); }}




     function createChart(ctx, label, color) {{
         return new Chart(ctx, {{
             type: 'line',
             data: {{ labels: [], datasets: [
                 {{ label: label, data: [], borderColor: color, fill: false }},
                 {{ label: 'Outliers', data: [], borderColor: 'red', backgroundColor: 'red', showLine: false, pointRadius: 4, type: 'scatter' }}
             ] }},
             options: {{ responsive: true, scales: {{ x: {{ ticks: {{ maxRotation: 90, minRotation: 45 }} }} }} }}
         }});
     }}




     function updateChart(chart, data, param) {{
         let values = data.map(d => d[param] || 0);
         let labels = data.map(d => new Date(d.timestamp).toLocaleTimeString() || '');
       
         if (values.length > 150) {{
             labels = labels.filter((_, i) => i % (Math.floor(labels.length / 150) || 1) === 0);
             values = binData(values, 150);
         }}




         chart.data.labels = labels;
         chart.data.datasets[0].data = values;
       
         let m = mean(values), s = stdev(values);
         let outliers = values.map((v, i) => (v > m + 2 * s || v < m - 2 * s) ? {{ x: labels[i], y: v }} : null).filter(v => v);
       
         chart.data.datasets[1].data = outliers;
         chart.update();
     }}




     function redrawCharts(type) {{
         const container = type === 'Spindle' ? document.getElementById('spindleCharts') : document.getElementById('testCharts');
         const paramSel = document.getElementById(type === 'Spindle' ? 'spindleParam' : 'testParam').value;
         container.innerHTML = '';
         const params = (type === 'Spindle' ? spindleParams : testParams);
         const filtered = (paramSel === 'all' ? params : [paramSel]);




         filtered.forEach(p => {{
             let canvasDiv = document.createElement('div');
             canvasDiv.style.marginBottom = '20px';
             let canvas = document.createElement('canvas');
             canvasDiv.appendChild(canvas);
             container.appendChild(canvasDiv);
           
             charts[type][p] = createChart(canvas.getContext('2d'), p, 'blue');
             updateChart(charts[type][p], latestData[type], p);
         }});
     }}




     // --- UI/API CONTROL FUNCTIONS ---




     function openTab(tabId, el) {{
       document.querySelectorAll('.tabcontent').forEach(t => t.style.display = 'none');
       document.getElementById(tabId).style.display = 'block';
       document.querySelectorAll('.tablink').forEach(b => b.classList.remove('active'));
       el.classList.add('active');
     
       if (tabId === 'visual') {{
           // Sync main tab dates to visual tab dates
           document.getElementById('visualFromDate').value = document.getElementById('fromDate').value;
           document.getElementById('visualToDate').value = document.getElementById('toDate').value;
         
           const activeSubTab = document.querySelector('#visual .subtablink.active');
           if (!activeSubTab) {{
               const firstSubTab = document.querySelector('#visual .subtablink');
               if (firstSubTab) {{
                   openSubTab(firstSubTab.getAttribute('onclick').match(/'([^']+)'/)[1], firstSubTab);
               }}
           }}
       }} else if (tabId === 'mainTab') {{
           // Sync visual tab dates back to main tab dates
           document.getElementById('fromDate').value = document.getElementById('visualFromDate').value;
           document.getElementById('toDate').value = document.getElementById('visualToDate').value;
           loadRecords();
       }} else if (tabId === 'paramTab') {{
           // Load parameters for the currently selected machine/type in the param tab
           loadParameters();
       }}
     }}
   
     function openSubTab(subTabId, el) {{
       document.querySelectorAll('.subtabcontent').forEach(t => t.style.display = 'none');
       document.getElementById(subTabId).style.display = 'block';
       document.querySelectorAll('.subtablink').forEach(b => b.classList.remove('active'));
       el.classList.add('active');
     
       const type = subTabId.includes('Spindles') ? 'Spindle' : 'Test';
       redrawCharts(type);
     }}
   
     function updateMachineOptions(type) {{
         const machineSelect = document.getElementById('machineSelect');
         const machineList = (type === 'Spindle') ? SPINDLE_MACHINES : TEST_MACHINES;




         machineSelect.innerHTML = '';
         machineList.forEach(m => {{
             const option = document.createElement('option');
             option.value = m;
             option.textContent = (type === 'Spindle' ? 'Spindle: ' : 'Test: ') + m;
             machineSelect.appendChild(option);
         }});




         currentMachine = machineSelect.value;
     }}
   
     document.getElementById('machineSelect').addEventListener('change', (e)=> {{ currentMachine = e.target.value; loadRecords(); }});
   
     document.getElementById('typeSelect').addEventListener('change', (e)=> {{
         currentType = e.target.value;
         updateMachineOptions(currentType);
         loadRecords();
     }});
   
     // Add event listeners to the main date pickers
     document.getElementById('fromDate').addEventListener('change', loadRecords);
     document.getElementById('toDate').addEventListener('change', loadRecords);
   
     updateMachineOptions(currentType);




     async function startWrapper() {{
       const url = currentType === 'Spindle' ? `/start-spindle?machine=${{currentMachine}}` : `/start-test?machine=${{currentMachine}}`;
     
       try {{
           const res = await fetch(url);
           const j = await res.json();




           alert(j.status === 'success' ? `${{currentType}} reading started (Session: ${{j.session_id}})` : j.message || JSON.stringify(j));
           loadRecords();
           loadHistory();
       }} catch (error) {{
           console.error('Start Error:', error);
           alert(`Failed to start worker. Is the server running? Details: ${{error.message}}`);
       }}
     }}
   
     function stopPrompt() {{
         const remarks = prompt("Enter remarks for stopping the session (optional):");
         if (remarks !== null) {{
             stopWrapper(remarks);
         }}
     }}




     async function stopWrapper(remarks){{
       const url = currentType === 'Spindle' ? `/stop-spindle?remarks=${{encodeURIComponent(remarks)}}` : `/stop-test?remarks=${{encodeURIComponent(remarks)}}`;
     
       try {{
           const res = await fetch(url);
         
           // Check if the response is valid JSON before parsing
           const text = await res.text();
           let j;
           try {{
               j = JSON.parse(text);
           }} catch (e) {{
               // If parsing fails (meaning the server sent an HTML error page)
               console.error('Stop Error: Non-JSON response received:', text);
               alert(`Failed to stop worker. Details: Unexpected token 'I', "Internal S"... is not valid JSON. Check Python Console.`);
               return;
           }}
         
           alert(j.status === 'success' ? `${{currentType}} reading stopped (Session: ${{j.session_id}})` : j.message || JSON.stringify(j));
           loadRecords();
           loadHistory();
       }} catch (error) {{
            console.error('Stop Error (Network):', error);
           alert(`Failed to stop worker. Details: ${{error.message}}`);
       }}
     }}
   
     async function addParameter(event) {{
         event.preventDefault();
         const form = event.target;
         const formData = new FormData(form);
       
         const paramMachine = document.getElementById('paramMachineSelect').value;
         const paramType = document.getElementById('paramTypeSelect').value;




         // Append machine and type to form data
         formData.append('machine', paramMachine);
         formData.append('type_reading', paramType);
       
         const res = await fetch('/parameters/add', {{
             method: 'POST',
             body: formData,
         }});
       
         if (res.ok) {{
             const j = await res.json();
           
             // We don't need the trigger-restart API call anymore as it's done within /parameters/add
           
             alert(j.message || j.status);
             form.reset();
             loadParameters();
             loadRecords(); // Reload records to see new columns
         }} else {{
             const j = await res.json();
             alert(j.message || j.status);
         }}
     }}
   
     async function loadParameters() {{
         const paramMachine = document.getElementById('paramMachineSelect').value;
         const paramType = document.getElementById('paramTypeSelect').value;
       
         // Disable listing if type is not Spindle (since only Spindle supports dynamic tags)
         if (paramType !== 'Spindle') {{
             document.getElementById('parametersBody').innerHTML = '<tr><td colspan="3">Dynamic parameter listing is only supported for Spindle type.</td></tr>';
             document.getElementById('paramWarning').style.display = 'block';
             return;
         }}
         document.getElementById('paramWarning').style.display = 'none';




         const res = await fetch(`/parameters?machine=${{paramMachine}}&rtype=${{paramType}}`);
         const data = await res.json();
         const body = document.getElementById('parametersBody');
         body.innerHTML = '';
       
         if (data.length === 0) {{
             body.insertAdjacentHTML('beforeend', '<tr><td colspan="3">No custom parameters added.</td></tr>');
             return;
         }}
       
         data.forEach(p => {{
             const tr = `<tr>
               <td>${{p.id}}</td>
               <td>${{p.name}}</td>
               <td>${{p.path}}</td>
             </tr>`;
             body.insertAdjacentHTML('beforeend', tr);
         }});
     }}
   
     async function loadRecords(){{
       const fromDate = document.getElementById('fromDate').value;
       const toDate = document.getElementById('toDate').value;
     
       let url = `/records?machine=${{currentMachine}}&rtype=${{currentType}}&limit=200`;
       if (fromDate) {{
           url += `&from_date=${{fromDate}}`;
       }}
       if (toDate) {{
           // Add one day to the 'to' date to make the query range inclusive up to the end of the day
           const nextDay = new Date(toDate);
           nextDay.setDate(nextDay.getDate() + 1);
           url += `&to_date=${{nextDay.toISOString().split('T')[0]}}`;
       }}
     
       const res = await fetch(url);
       const data = await res.json();
       latestData[currentType] = data;
       document.getElementById('count').innerText = data.length;
       const head = document.getElementById('recordsHead');
       const body = document.getElementById('recordsBody');
       body.innerHTML = '';




       const keys = columnHeaders[currentType];
       let hrow = '<tr>';
       keys.forEach(k => {{
           if (k === 'timestamp') {{
               hrow += `<th>Date</th><th>Time</th>`;
           }} else {{
               hrow += `<th>${{k}}</th>`;
           }}
       }});
       hrow += '</tr>';
       head.innerHTML = hrow;




       if (data.length === 0) {{
           body.insertAdjacentHTML('beforeend', `<tr><td colspan="${{keys.length + 1}}">No records</td></tr>`);
           return;
       }}




       data.forEach(r => {{
           let row = '<tr>';
           keys.forEach(k => {{
               let val = r[k];
               if (val === null || val === undefined) {{
                   val = '';
               }}
               if (k === 'timestamp' && val) {{
                   let dt = new Date(val);
                   let datePart = dt.toLocaleDateString();
                   let timePart = dt.toLocaleTimeString();
                   row += `<td>${{datePart}}</td><td>${{timePart}}</td>`;
               }} else {{
                   row += `<td>${{val}}</td>`;
               }}
           }});
           row += '</tr>';
           body.insertAdjacentHTML('beforeend', row);
       }});
       redrawCharts(currentType);
   }}




     
       async function loadHistory(){{
           const res = await fetch(`/history?limit=50`);
           const data = await res.json();
           const body = document.getElementById('historyBody');
           body.innerHTML = '';
     
           const headers = document.querySelector('#historyTable thead tr');
           if (data.length > 0 && !headers.innerHTML.includes('<th>Remarks</th>')) {{
               headers.insertAdjacentHTML('beforeend', '<th>Remarks</th>');
           }}




           data.forEach(h => {{
           const tr = `<tr>
               <td>${{h.id}}</td>
               <td>${{h.machine_name}}</td>
               <td>${{h.reading_type}}</td>
               <td>${{h.start_time || ''}}</td>
               <td>${{h.end_time || ''}}</td>
               <td>${{h.duration_minutes !== null ? h.duration_minutes.toFixed(2) : ''}}</td>
               <td>${{h.records_logged || ''}}</td>
               <td>${{h.remarks || ''}}</td>
           </tr>`;
           body.insertAdjacentHTML('beforeend', tr);
           }});
       }}
   
     // Initial Setup
     document.querySelector('.tablink').classList.add('active');
     openTab('mainTab', document.querySelector('.tablink'));




     loadRecords();
     loadHistory();
     setInterval(loadRecords, 5000);
     setInterval(loadHistory, 15000);
   </script>
   </body>
   </html>
   """
   return HTMLResponse(content=html)








# Server startup has been moved to server.py
if __name__ == "__main__":
    import uvicorn
    import os
    ssl_keyfile = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')
    ssl_certfile = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
    uvicorn.run(
        "modern:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=True,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )









