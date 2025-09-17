import json
import os
from typing import Any, Dict, Optional

import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS")


def generate_playbook_controller(
    alert: Dict[str, Any],
    output_file: Optional[str],
    export: bool,
    display: bool,
    graph_rag_enabled: bool,
) -> Dict[str, str]:
    """Send alert to queue for processing instead of calling main function directly."""
    try:
        print(
            f"[DEBUG] Attempting to connect to RabbitMQ at {RABBITMQ_HOST} with user {RABBITMQ_USER}"
        )

        message = {
            "alert": alert,
            "output_file": output_file,
            "export": export,
            "display": display,
            "graph_rag_enabled": graph_rag_enabled,
        }

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

        connection.close()

        return {
            "status": "success",
            "message": f"Alert sent to queue '{RABBITMQ_QUEUE}' for processing",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send alert to queue: {str(e)}",
        }
