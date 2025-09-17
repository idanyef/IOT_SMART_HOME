# SmartParking/setup_db.py
from manager_parking import CREATE_SPOTS, CREATE_EVENTS
from init import db_path
import sqlite3

conn = sqlite3.connect(db_path)
conn.execute(CREATE_SPOTS); conn.execute(CREATE_EVENTS)
for i in (1,2,3): conn.execute("INSERT OR IGNORE INTO spots(spot_id) VALUES(?);", (i,))
conn.commit(); conn.close()
print(f"DB initialized at: {db_path}")
