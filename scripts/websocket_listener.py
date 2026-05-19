import asyncio
import json

import websockets

# If running on the Jetson itself, use "localhost".
# If running on your laptop, change "localhost" to your Jetson's actual IP address.
GATEWAY_URL = "ws://localhost:9090"


async def monitor_gateway():
    print(f" Connecting to Gateway at {GATEWAY_URL}...")

    try:
        # Open a persistent connection to your GatewayService
        async with websockets.connect(GATEWAY_URL) as websocket:
            print("🟢 Connected! Standing by for real-time data stream...\n")

            # Continuously listen for incoming byte frames
            async for raw_message in websocket:
                try:
                    # Decode the JSON packet structured by your server
                    data = json.loads(raw_message)
                    msg_type = data.get("type")
                    payload = data.get("payload")

                    # Print out the incoming stream cleanly
                    print(f"[{msg_type}] ➔ {payload}")

                except json.JSONDecodeError:
                    print(f"⚠️ Raw Unstructured Message Received: {raw_message}")

    except ConnectionRefusedError:
        print("❌ Connection Refused. Is your GatewayService script running?")
    except websockets.exceptions.ConnectionClosedOK:
        print("\n🛑 Server closed the connection cleanly.")
    except KeyboardInterrupt:
        print("\n👋 Disconnected by user.")


if __name__ == "__main__":
    try:
        asyncio.run(monitor_gateway())
    except KeyboardInterrupt:
        pass
