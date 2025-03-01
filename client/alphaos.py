import asyncio
import json
import ssl
import logging
from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)

class MyWebSocketClientProtocol(WebSocketClientProtocol):
    async def onConnect(self, response):
        logging.info("Connected to server: %s", response.peer)

    async def onOpen(self):
        logging.info("WebSocket connection opened")
        message = json.dumps({"message": "Hello, AI Model!"})
        self.sendMessage(message.encode('utf-8'))

    async def onMessage(self, payload, isBinary):
        if not isBinary:
            message = payload.decode('utf-8')
            logging.info("Received message: %s", message)

    async def onClose(self, wasClean, code, reason):
        logging.error(f"WebSocket connection closed: {reason}")

async def connect_to_server(url):
    """
    Connect to the WebSocket server using Autobahn.
    """
    uri = urlparse(url)
    ssl_context = ssl.create_default_context() if uri.scheme == "wss" else None
    factory = WebSocketClientFactory(url)
    factory.protocol = MyWebSocketClientProtocol

    loop = asyncio.get_event_loop()
    conn = loop.create_connection(factory, uri.hostname, uri.port, ssl=ssl_context)
    transport, protocol = await conn
    return protocol

async def main():
    try:
        ws_client = await connect_to_server("wss://derleiti.de:8082")
        await asyncio.sleep(10)  # Keep connection open for demonstration
    except Exception as e:
        logging.error("Error: %s", e)
    finally:
        logging.info("Closing WebSocket connection")

if __name__ == "__main__":
    asyncio.run(main())
