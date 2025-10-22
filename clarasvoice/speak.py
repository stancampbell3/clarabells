import requests
import tempfile
import subprocess
import os
import argparse
import platform
import shutil


def detect_format_from_magic(first_bytes, content_type=None):
    if content_type:
        ct = content_type.split(';', 1)[0].strip().lower()
        if ct in ('audio/mpeg', 'audio/mp3'):
            return 'mp3'
        if ct in ('audio/wav', 'audio/x-wav', 'audio/wave', 'audio/vnd.wave'):
            return 'wav'
        if ct == 'audio/ogg':
            return 'ogg'
        if ct == 'audio/flac':
            return 'flac'
    # Fallback to magic bytes
    if first_bytes.startswith(b'ID3') or (len(first_bytes) >= 2 and first_bytes[0] == 0xFF and (first_bytes[1] & 0xE0) == 0xE0):
        return 'mp3'
    if first_bytes.startswith(b'RIFF') and b'WAVE' in first_bytes[:12]:
        return 'wav'
    if first_bytes.startswith(b'OggS'):
        return 'ogg'
    if first_bytes.startswith(b'fLaC'):
        return 'flac'
    return None


def choose_player_cmd(system, audio_format):
    if system == 'Linux':
        if audio_format == 'mp3':
            return ['mpg123']
        # prefer aplay for PCM WAV if available
        if shutil.which('aplay'):
            return ['aplay']
        return ['mpg123']  # fallback
    if system == 'Darwin':
        return ['afplay']
    if system == 'Windows':
        return ['cmd', '/c', 'start', '/wait']
    raise RuntimeError(f"Unsupported OS: {system}")


def main():
    parser = argparse.ArgumentParser(description="Clarabells client to request and play audio.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--text", help="Text to speak (optional)")
    parser.add_argument("--outloud", action="store_true", help="If set, download and play the audio locally")
    args = parser.parse_args()

    api_url = f"http://{args.host}:{args.port}/clara/api/v1/speak"
    bearer_token = "mysecrettoken"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    payload = {"text": args.text} if args.text else {}

    try:
        # Use stream=True so we can inspect headers/magic bytes without necessarily downloading the body
        resp = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)
        resp.raise_for_status()

        # If the user didn't ask to play out loud, just verify we received a GUID header and close
        if not args.outloud:
            guid = resp.headers.get('X-Clara-Audio-GUID')
            content_type = resp.headers.get('content-type', '')
            if guid:
                print(f"OK: server synthesized audio GUID={guid}")
            else:
                # No GUID header: server likely returned a raw audio file (e.g., fallback or existing file).
                # We can detect the content-type to confirm it's audio and avoid downloading.
                if content_type.startswith('audio/'):
                    print(f"OK: server returned audio (Content-Type: {content_type}) but no GUID header")
                else:
                    print(f"OK: server returned status {resp.status_code}")
            # Close the connection without reading the rest of the body
            try:
                resp.close()
            except Exception:
                pass
            return

        # Otherwise, stream and play the audio locally (existing behavior)
        it = resp.iter_content(chunk_size=8192)
        first_chunk = next(it, b'')
        content_type = resp.headers.get('content-type')
        audio_format = detect_format_from_magic(first_chunk, content_type)
        if not audio_format:
            audio_format = 'wav'

        suffix = f".{audio_format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(first_chunk)
            for chunk in it:
                if chunk:
                    tmp.write(chunk)
            temp_file_path = tmp.name

        system = platform.system()
        player_cmd = choose_player_cmd(system, audio_format)

        # Ensure player exists on non-Windows
        if system in ('Linux', 'Darwin') and not shutil.which(player_cmd[0]):
            raise RuntimeError(f"Audio player '{player_cmd[0]}' not found. Install it or update your configuration.")

        subprocess.run(player_cmd + [temp_file_path], check=True)
        os.unlink(temp_file_path)
        print("Audio played successfully.")

    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Playback failed: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()