# SmartParking/init.py
# הגדרות כלליות ו-Topics

# פרטי ברוקר MQTT (התאם לפי הסביבה שלך)
broker_ip   = "127.0.0.1"
broker_port = "1883"
username    = ""          # אם אין משתמש, השאר ריק
password    = ""

# בסיס הנושאים
comm_topic  = "smartparking/"

# חלון זמן (בדקות) שבו תשלום תקף אחרי כניסה
valid_payment_window_min = 5

# שם קובץ ה-DB
db_path = "parking.db"
