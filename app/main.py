import os
import threading
import time
import pika

rabbitmq_host = os.environ.get("RABBITMQ_HOST") or "rabbitmq"
rabbitmq_port = os.environ.get("RABBITMQ_PORT") or 5672
rabbitmq_virtual_host = "/"
rabbitmq_username = os.environ.get("RABBITMQ_DEFAULT_USER") or "guest"
rabbitmq_password = os.environ.get("RABBITMQ_DEFAULT_PASS") or "guest"

num_connections = 10

connections_and_channels = []


def create_rabbitmq_connection():
    try:
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            virtual_host=rabbitmq_virtual_host,
            credentials=credentials,
            heartbeat=600,
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        return connection, channel
    except Exception:
        return None, None


def wait_for_rabbitmq():
    while True:
        try:
            connection, _ = create_rabbitmq_connection()
            if connection and connection.is_open:
                return
        except Exception as e:
            print(f"Waiting for RabbitMQ to become available: {e}")
            time.sleep(5)


wait_for_rabbitmq()


def maintain_connection(connection, channel):
    while True:
        if not connection or not connection.is_open:
            print("Connection closed. Re-establishing...")
            connection, channel = create_rabbitmq_connection()
            if connection and connection.is_open:
                connections_and_channels.append((connection, channel))
        time.sleep(5)


for _ in range(num_connections):
    connection, channel = create_rabbitmq_connection()
    if connection and connection.is_open:
        connections_and_channels.append((connection, channel))
        thread = threading.Thread(
            target=maintain_connection, args=(connection, channel)
        )
        thread.daemon = True
        thread.start()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

for connection, _ in connections_and_channels:
    connection.close()
