import asyncio
import websockets
import subprocess
import argparse
import os

async def listen_and_play(host: str, port: int):
    uri = f"ws://{host}:{port}/ws/notify"
    speak_py_path = os.path.join(os.path.dirname(__file__), '..', 'clarasvoice', 'speak.py')

    async with websockets.connect(uri) as websocket:
        print("Connected to server for notifications.")
        async for message in websocket:
            print(f"Received notification: {message}")
            # Run speak.py with the received text
            try:
                subprocess.run(['python', speak_py_path, '--host', host, '--port', str(port), '--text', message], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to play audio: {e}")

def main():
    parser = argparse.ArgumentParser(description="Attention listener for Clara notifications.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    asyncio.run(listen_and_play(args.host, args.port))

if __name__ == "__main__":
    main()