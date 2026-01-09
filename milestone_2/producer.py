import pika
import json

RABBITMQ_HOST = "localhost"
QUEUE_NAME = "url_queue"

seed_urls = [
    "https://example.com",
    "https://www.python.org",
    "https://www.wikipedia.org"
]

# ---- Connect to RabbitMQ ----
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST)
)
channel = connection.channel()

# ---- Create Queue (idempotent) ----
channel.queue_declare(queue=QUEUE_NAME, durable=True)

print("\n[PRODUCER] Sending seed URLs...\n")

for url in seed_urls:
    message = json.dumps({"url": url})

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)  # persistent message
    )

    print(f"[SENT] -> {url}")

connection.close()

print("\n[PRODUCER DONE] URLs published successfully.")






