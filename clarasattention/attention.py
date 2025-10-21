import asyncio
import websockets
import subprocess
import argparse
import os
import requests
import tempfile
import json
import platform
import shutil


def get_player_cmd():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'clarasvoice', 'claras_clutch.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        return config['player_cmd']
    else:
        system = platform.system()
        if system == 'Linux':
            player_cmd = ['mpg123']
        elif system == 'Darwin':
            player_cmd = ['afplay']
        elif system == 'Windows':
            player_cmd = ['cmd', '/c', 'start', '/wait']
        else:
            raise RuntimeError(f"Unsupported OS: {system}")

        if system in ['Linux', 'Darwin'] and not shutil.which(player_cmd[0]):
            raise RuntimeError(f"Audio player '{player_cmd[0]}' not found.")

        config = {'player_cmd': player_cmd}
        with open(config_path, 'w') as f:
            json.dump(config, f)
        return player_cmd


async def listen_and_play(host: str, port: int):
    uri = f"ws://{host}:{port}/ws/notify"
    player_cmd = get_player_cmd()

    async with websockets.connect(uri) as websocket:
        print("Connected to server for notifications.")
        async for guid in websocket:
            print(f"Received GUID: {guid}")
            # Fetch audio stream
            api_url = f"http://{host}:{port}/audio/{guid}"
            try:
                response = requests.get(api_url, stream=True)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                # Play locally
                subprocess.run(player_cmd + [temp_file_path], check=True)
                os.unlink(temp_file_path)
                print("Audio played successfully.")
            except Exception as e:
                print(f"Failed to fetch or play audio: {e}")

def main():
    parser = argparse.ArgumentParser(description="Attention listener for Clara notifications.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    asyncio.run(listen_and_play(args.host, args.port))

if __name__ == "__main__":
    main()