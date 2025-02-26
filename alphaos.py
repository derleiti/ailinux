import asyncio
import json
import ssl

from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
from urllib.parse import urlparse


class MyWebSocketClientProtocol(WebSocketClientProtocol):
    async def onConnect(self, response):
        print("Connected to server:", response.peer)

    async def onOpen(self):
        print("WebSocket connection opened")
        # Send an initial message if required
        message = json.dumps({"message": "Hello, AI Model!"})
        self.sendMessage(message.encode('utf-8'))

    async def onMessage(self, payload, isBinary):
        if not isBinary:
            message = payload.decode('utf-8')
            print("Received message:", message)

    async def onClose(self, wasClean, code, reason):
        print(f"WebSocket connection closed: {reason}")


async def connect_to_server(url):
    """
    Connect to the WebSocket server using Autobahn.
    """
    uri = urlparse(url)

    # Create SSL context if using wss://
    ssl_context = ssl.create_default_context() if uri.scheme == "wss" else None

    # Set up the WebSocket client
    factory = WebSocketClientFactory(url)
    factory.protocol = MyWebSocketClientProtocol

    loop = asyncio.get_running_loop()
    conn = loop.create_connection(factory, uri.hostname, uri.port, ssl=ssl_context)

    transport, protocol = await conn
    return protocol


async def main():
    try:
        ws_client = await connect_to_server("wss://derleiti.de:8082")
        await asyncio.sleep(10)  # Keep connection open for demonstration
    except Exception as e:
        print("Error:", e)
    finally:
        print("Closing WebSocket connection")


if __name__ == "__main__":
    asyncio.run(main())


def get_recommendation(data):
    """
    Implement your recommendation logic here.
    Example:
    - Process the data received from WebSocket
    - Return a recommendation based on AI model response
    """
    return {"recommendation": "Sample Recommendation"}
