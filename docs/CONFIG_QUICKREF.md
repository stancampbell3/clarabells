# Clara Configuration Quick Reference

## Create Configuration File

```bash
cp clara_config.json.example clara_config.json
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `host` | `"0.0.0.0"` | Network interface (0.0.0.0 = all, 127.0.0.1 = local only) |
| `port` | `8000` | Server port |
| `audio_cache_ttl_seconds` | `3600` | Auto-delete audio files older than this (0 = never delete) |
| `audio_cache_cleanup_interval_seconds` | `300` | How often to check for expired files |
| `bearer_token` | `"mysecrettoken"` | API authentication token (CHANGE THIS!) |

## Environment Variable Overrides

```bash
export CLARA_HOST="127.0.0.1"
export CLARA_PORT=9000
export CLARA_AUDIO_TTL=7200
export CLARA_BEARER_TOKEN="your-secure-token"
```

## Common Configurations

### Development (local, keep files 30 min)
```json
{
  "host": "127.0.0.1",
  "port": 8000,
  "audio_cache_ttl_seconds": 1800,
  "bearer_token": "dev-token"
}
```

### Production (network, keep files 1 hour)
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "audio_cache_ttl_seconds": 3600,
  "bearer_token": "CHANGE-ME-TO-SECURE-TOKEN"
}
```

### Low storage (keep files 5 min, check every minute)
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "audio_cache_ttl_seconds": 300,
  "audio_cache_cleanup_interval_seconds": 60,
  "bearer_token": "your-token"
}
```

### Never delete (TTL = 0)
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "audio_cache_ttl_seconds": 0,
  "bearer_token": "your-token"
}
```

## Starting the Server

The start script automatically reads `clara_config.json`:

```bash
./scripts/start_server.sh              # Use config file settings
./scripts/start_server.sh --foreground # Show logs in console
```

Override with command-line:
```bash
HOST=127.0.0.1 PORT=9000 ./scripts/start_server.sh
```

## Monitoring Cleanup

```bash
tail -f logs/server.log | grep -E "cleanup|expired|Deleted"
```

## Security

**IMPORTANT**: Change the default bearer token in production!

```bash
# Generate a secure token
openssl rand -hex 32

# Set it in config or environment
export CLARA_BEARER_TOKEN="your-generated-token-here"
```

Protect the config file:
```bash
chmod 600 clara_config.json
```

## Documentation

- Full guide: [docs/CONFIGURATION.md](CONFIGURATION.md)
- Audio setup: [docs/AUDIO_PLAYBACK.md](AUDIO_PLAYBACK.md)

