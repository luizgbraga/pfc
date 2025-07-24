import json
import os

import pika

from main import generate_playbook

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS")


def process_alert_message(alert_json, output_file=None, export=False, display=True):
    """Process alert by calling the main generate_playbook function directly."""
    try:
        result = generate_playbook(
            alert=alert_json, output_file=output_file, export=export, display=display
        )
        print(f"[x] Playbook generated successfully: {result}")
        return result
    except Exception as e:
        print(f"[!] Error generating playbook: {e}")
        return None


def callback(ch, method, properties, body):
    print(f"[x] Received message: {body}")
    try:
        message = json.loads(body)
        alert = message.get("alert")
        output_file = message.get("output_file")
        export = message.get("export", False)
        display = message.get("display", True)

        if alert is None:
            print("[!] Message missing 'alert' field.")
            return

        process_alert_message(alert, output_file, export, display)
    except Exception as e:
        print(f"[!] Error processing message: {e}")


def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=900,
        )
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
