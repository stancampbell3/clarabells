import requests
import tempfile
import subprocess
import os
import argparse

def main():
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

        # Play the audio using mpg123
        subprocess.run(["mpg123", temp_file_path], check=True)

        # Clean up
        os.unlink(temp_file_path)
        print("Audio played successfully.")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Playback failed: {e}")

if __name__ == "__main__":
    main()
