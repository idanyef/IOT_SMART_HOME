import paho.mqtt.client as mqtt
import time
import uuid

# ברוקר לבדיקה
BROKER = "test.mosquitto.org"
PORT = 1883

# נושא ייחודי לכל בדיקה
def gen_topic():
    return f"test/mqtt_check/{uuid.uuid4()}"

# בדיקה אחת
def run_test(clean_session, retain, sub_qos, pub_qos):
    topic = gen_topic()
    message = f"msg_cs={clean_session}_r={retain}_sqos={sub_qos}_pqos={pub_qos}"
    result = {"combination": (clean_session, retain, sub_qos, pub_qos), "received": False}

    # שליחת ההודעה
    pub_client = mqtt.Client(client_id="pub", clean_session=clean_session)
    pub_client.connect(BROKER, PORT)
    pub_client.publish(topic, payload=message, qos=pub_qos, retain=retain)
    pub_client.disconnect()
    time.sleep(1)

    # קבלת ההודעה
    def on_message(client, userdata, msg):
        if msg.payload.decode() == message:
            result["received"] = True

    sub_client = mqtt.Client(client_id="sub", clean_session=clean_session)
    sub_client.on_message = on_message
    sub_client.connect(BROKER, PORT)
    sub_client.subscribe(topic, qos=sub_qos)
    sub_client.loop_start()
    time.sleep(2)
    sub_client.loop_stop()
    sub_client.disconnect()

    return result

# כל הקומבינציות האפשריות
combinations = []
for cs in [True, False]:
    for r in [True, False]:
        for sq in [0, 1]:
            for pq in [0, 1]:
                combinations.append((cs, r, sq, pq))

# הרצת כל הבדיקות
print("Running tests...\n")
results = []
for combo in combinations:
    res = run_test(*combo)
    results.append(res)
    print(f"Test {combo} → Received: {res['received']}")

# סיכום
print("\nSummary:")
print("CleanSession | Retain | SubQoS | PubQoS | Received")
for r in results:
    cs, rt, sq, pq = r["combination"]
    rec = r["received"]
    print(f"{str(cs):>12} | {str(rt):>6} | {sq:^7} | {pq:^7} | {'YES' if rec else 'NO '}")

