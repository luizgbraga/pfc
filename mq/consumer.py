import json
import os

import pika
import requests

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE", "alerts")
GENERATE_PLAYBOOK_URL = os.environ.get(
    "GENERATE_PLAYBOOK_URL", "http://127.0.0.1:5001/generate-playbook"
)
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "password")


def process_alert_message(alert_json):
    payload = {
        "alert": alert_json,
        "output_file": None,
        "export": False,
        "display": True,
    }
    response = requests.post(GENERATE_PLAYBOOK_URL, json=payload)
    print(
        f"[x] Called generate_playbook, status: {response.status_code}, response: {response.text}"
    )


def callback(ch, method, properties, body):
    print(f"[x] Received message: {body}")
    try:
        message = json.loads(body)
        alert = message.get("alert")
        if alert is None:
            print("[!] Message missing 'alert' field.")
            return
        process_alert_message(alert)
    except Exception as e:
        print(f"[!] Error processing message: {e}")


def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    print(f"[*] Waiting for messages in queue '{RABBITMQ_QUEUE}'. To exit press CTRL+C")
    channel.basic_consume(
        queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True
    )
    channel.start_consuming()


if __name__ == "__main__":
    main()
