import json
import os

import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE", "alerts")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "password")


def main():
    alert = {
        "alert_name": "Suspicious Login Attempt",
        "incident_type": "Unauthorized Access",
        "severity": "High",
        "source_ip": "192.168.1.100",
        "destination_ip": "10.0.0.5",
        "hostname": "server01",
        "user": "alice",
        "description": "Multiple failed login attempts detected from unusual location.",
        "timestamp": "2024-06-01T12:34:56Z",
        "logs": "Failed password for alice from 192.168.1.100 port 22 ssh2",
    }
    message = {"alert": alert}

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),  # make message persistent
    )
    print(f"[x] Sent mock alert to queue '{RABBITMQ_QUEUE}'")
    connection.close()


if __name__ == "__main__":
    main()
