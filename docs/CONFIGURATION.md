# Clara Server Configuration Guide

## Configuration File

Clara uses a `clara_config.json` file in the project root for server configuration. If the file doesn't exist, the server uses default values.

### Creating Your Configuration

Copy the example template:
```bash
cp clara_config.json.example clara_config.json
```

Edit `clara_config.json` to customize your deployment:

```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "audio_cache_ttl_seconds": 3600,
  "audio_cache_cleanup_interval_seconds": 300,
  "bearer_token": "mysecrettoken"
}
```

## Configuration Options

### Server Settings

**`host`** (string, default: `"0.0.0.0"`)
- Network interface to bind to
- `"0.0.0.0"` = all interfaces (accessible from network)
- `"127.0.0.1"` = localhost only (local access only)

**`port`** (integer, default: `8000`)
- TCP port for the server to listen on

### Audio Cache Settings

**`audio_cache_ttl_seconds`** (integer, default: `3600`)
- Time-to-live for generated audio files in seconds
- Files older than this will be automatically deleted
- Default: 3600 seconds (1 hour)
- Set to `0` to disable automatic cleanup
- Examples:
  - `300` = 5 minutes
  - `1800` = 30 minutes
  - `3600` = 1 hour
  - `86400` = 24 hours
  - `0` = never delete (cleanup disabled)

**`audio_cache_cleanup_interval_seconds`** (integer, default: `300`)
- How often to check for expired files (in seconds)
- Default: 300 seconds (5 minutes)
- Lower values = more frequent cleanup, slightly higher CPU usage
- Higher values = less frequent cleanup, files may linger longer

### Authentication

**`bearer_token`** (string, default: `"mysecrettoken"`)
- Bearer token for API authentication
- **Important**: Change this from the default in production!
- Used in Authorization header: `Authorization: Bearer <token>`

## Environment Variable Overrides

Environment variables take precedence over the config file:

```bash
# Override host
export CLARA_HOST="127.0.0.1"

# Override port
export CLARA_PORT=9000

# Override audio TTL (in seconds)
export CLARA_AUDIO_TTL=7200

# Override bearer token
export CLARA_BEARER_TOKEN="your-secure-token-here"
```

## Configuration Priority

Configuration values are loaded in this order (later overrides earlier):
1. Default values (hardcoded)
2. `clara_config.json` file
3. Environment variables

## Audio Cleanup Behavior

The cleanup system works as follows:

1. **Background Task**: Runs every `audio_cache_cleanup_interval_seconds`
2. **File Scanning**: Checks all `.wav` files in the `./audio` directory
3. **Age Check**: Compares file modification time against `audio_cache_ttl_seconds`
4. **Protected Files**: Never deletes files in `./app/assets/` (system files)
5. **Deletion**: Removes expired files and logs the action

### Example Scenarios

**Default (1 hour TTL, 5 minute checks)**:
- Generated audio files are kept for 1 hour
- Every 5 minutes, the system checks for files older than 1 hour
- Expired files are deleted automatically

**Quick cleanup (5 minute TTL)**:
```json
{
  "audio_cache_ttl_seconds": 300,
  "audio_cache_cleanup_interval_seconds": 60
}
```
- Audio files expire after 5 minutes
- Cleanup runs every minute

**Long-term storage (24 hours)**:
```json
{
  "audio_cache_ttl_seconds": 86400,
  "audio_cache_cleanup_interval_seconds": 3600
}
```
- Audio files kept for 24 hours
- Cleanup runs every hour

**Disable cleanup**:
```json
{
  "audio_cache_ttl_seconds": 0
}
```
- Audio files are never automatically deleted
- Manual cleanup required

## Deployment Examples

### Development (local only)
```json
{
  "host": "127.0.0.1",
  "port": 8000,
  "audio_cache_ttl_seconds": 1800,
  "bearer_token": "dev-token-123"
}
```

### Production (network accessible)
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "audio_cache_ttl_seconds": 3600,
  "bearer_token": "use-a-secure-random-token-here"
}
```

### Low-storage device
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "audio_cache_ttl_seconds": 300,
  "audio_cache_cleanup_interval_seconds": 60,
  "bearer_token": "your-token"
}
```

## Starting the Server with Custom Config

The server automatically loads `clara_config.json` if it exists:

```bash
# Using the start script (reads clara_config.json automatically)
./scripts/start_server.sh

# Or manually with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Note**: The `--host` and `--port` flags to uvicorn override the config file values.

To use config file values exclusively:
```bash
# Use Python to read config and start with those values
python -c "from app.config import config; import subprocess; subprocess.run(['uvicorn', 'app.main:app', '--host', config.host, '--port', str(config.port)])"
```

Or update the start script to read from config.

## Monitoring Cleanup

Watch the server logs to see cleanup activity:

```bash
tail -f logs/server.log | grep -E "(cleanup|expired|Deleted)"
```

You'll see messages like:
```
INFO:app.main:Cleaned up 5 expired audio file(s)
INFO:app.main:Deleted expired audio file: -1234567890.wav (age: 3720s)
```

## Security Considerations

1. **Change the bearer token** in production
2. Use a strong, random token (e.g., output of `openssl rand -hex 32`)
3. Consider storing tokens in environment variables instead of the config file
4. Restrict file permissions on `clara_config.json`:
   ```bash
   chmod 600 clara_config.json
   ```

## Troubleshooting

### Config file not loading
- Check the file is named exactly `clara_config.json`
- Verify it's in the project root (where you run the server)
- Check JSON syntax: `python -m json.tool clara_config.json`

### Cleanup not working
- Verify `audio_cache_ttl_seconds > 0`
- Check server logs for cleanup task messages
- Ensure audio directory is writable
- Look for error messages in logs

### Files deleted too quickly
- Increase `audio_cache_ttl_seconds`
- Check system clock is correct (`date`)

### Files not being deleted
- Check `audio_cache_ttl_seconds` is not `0`
- Verify files are truly older than TTL
- Check file permissions in audio directory
- Review server logs for errors

