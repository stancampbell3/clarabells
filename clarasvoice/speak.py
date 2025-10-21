import requests
import tempfile
import subprocess
import os
import argparse
import json
import platform
import shutil

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'claras_clutch.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        player_cmd = config['player_cmd']
    else:
        system = platform.system()
        if system == 'Linux':
            player_cmd = ['mpg123']
        elif system == 'Darwin':
            player_cmd = ['afplay']
        elif system == 'Windows':
            player_cmd = ['cmd', '/c', 'start', '/wait']
        else:
            raise RuntimeError(f"Unsupported OS: {system}. Supported: Linux, macOS, Windows.")

        # Check if the player command is available
        if system in ['Linux', 'Darwin']:
            if not shutil.which(player_cmd[0]):
                raise RuntimeError(f"Audio player '{player_cmd[0]}' not found. Install it (e.g., sudo apt install {player_cmd[0]} on Linux or ensure it's available on macOS).")
        # For Windows, assume 'cmd' is available

        config = {'player_cmd': player_cmd}
        with open(config_path, 'w') as f:
            json.dump(config, f)

    parser = argparse.ArgumentParser(description="Clarabells client to request and play audio.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--text", help="Text to speak (optional)")
    args = parser.parse_args()

    api_url = f"http://{args.host}:{args.port}/clara/api/v1/speak"
    bearer_token = "mysecrettoken"

    headers = {"Authorization": f"Bearer {bearer_token}"}
    payload = {"text": args.text} if args.text else {}
    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        # Save streamed audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        # Play the audio using the detected player
        subprocess.run(player_cmd + [temp_file_path], check=True)

        # Clean up
        os.unlink(temp_file_path)
        print("Audio played successfully.")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Playback failed: {e}")

if __name__ == "__main__":
    main()