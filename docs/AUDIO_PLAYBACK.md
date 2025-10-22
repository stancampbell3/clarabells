# Audio Playback Configuration Guide

## Overview

Clara uses external audio players for reliable playback across different platforms. The system automatically tries multiple players in priority order to ensure maximum compatibility.

## Recommended Audio Players

### Linux (Priority Order)
1. **mpv** (Recommended) - Most reliable, handles all formats
   ```bash
   sudo apt-get install mpv
   # or
   sudo dnf install mpv
   ```

2. **ffplay** (FFmpeg) - Excellent buffering, cross-format support
   ```bash
   sudo apt-get install ffmpeg
   ```

3. **aplay** (ALSA) - Built-in on most systems, optimized with large buffers
   ```bash
   sudo apt-get install alsa-utils
   ```

4. **mpg123** - MP3 specialist, also handles WAV
   ```bash
   sudo apt-get install mpg123
   ```

5. **play** (SoX) - Swiss army knife of audio
   ```bash
   sudo apt-get install sox
   ```

### macOS (Priority Order)
1. **afplay** - Built-in, no installation needed
2. **mpv** - Available via Homebrew
   ```bash
   brew install mpv
   ```
3. **ffplay** - Available via Homebrew
   ```bash
   brew install ffmpeg
   ```

### Windows
Uses built-in `cmd /c start /wait` - no additional installation needed

## Playback Issues & Solutions

### "Your stream is not nice" Error (Linux with aplay)

**Cause**: Buffer underruns when `aplay` uses default small buffers (512 samples)

**Solution**: Clara automatically uses `--buffer-size=8192` when using aplay, but we recommend installing `mpv` or `ffplay` for better results:
```bash
sudo apt-get install mpv
```

### Garbled Audio or Skipping

**Causes**:
- Network latency between client and server
- Insufficient system resources
- Incompatible audio player

**Solutions**:
1. Install `mpv` (most reliable):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mpv
   
   # macOS
   brew install mpv
   ```

2. Check network connectivity:
   ```bash
   ping <server-host>
   ```

3. Verify audio file integrity:
   ```bash
   file audio/*.wav
   # Should show: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz
   ```

### No Audio Player Found

**Solution**: Install at least one player from the recommended list above.

## Audio Format Details

Clara generates WAV files with these specifications:
- **Format**: 16-bit PCM
- **Channels**: Mono
- **Sample Rate**: 24000 Hz (24 kHz)
- **Encoding**: Microsoft PCM (RIFF WAVE)

All recommended players support this format.

## Player Selection Logic

Clara tries players in this order:

**For WAV files (Linux)**:
1. mpv (with `--really-quiet`)
2. ffplay (with `-nodisp -autoexit -loglevel quiet`)
3. aplay (with `--buffer-size=8192`)
4. play (with `-q`)
5. mpg123 (with `-q`)

If a player fails, Clara automatically tries the next available option.

## Custom Player Configuration

You can override the default player by creating `clarasvoice/claras_clutch.json`:

```json
{
  "player_cmd": ["mpv", "--really-quiet"]
}
```

This will be used as the first choice before falling back to defaults.

## Testing Your Setup

1. **Check available players**:
   ```bash
   which mpv ffplay aplay mpg123
   ```

2. **Test playback manually**:
   ```bash
   # With mpv (recommended)
   mpv --really-quiet audio/<some-file>.wav
   
   # With aplay (with large buffer)
   aplay --buffer-size=8192 audio/<some-file>.wav
   
   # With ffplay
   ffplay -nodisp -autoexit -loglevel quiet audio/<some-file>.wav
   ```

3. **Test Clara client**:
   ```bash
   # Test without playback (just verify server response)
   python clarasvoice/speak.py --text "Hello world" --host <server-ip>
   
   # Test with playback
   python clarasvoice/speak.py --text "Hello world" --host <server-ip> --outloud
   ```

4. **Test attention client**:
   ```bash
   python clarasattention/attention.py --host <server-ip>
   # In another terminal, trigger speech:
   python clarasvoice/speak.py --text "Testing attention" --host <server-ip>
   ```

## Performance Tips

1. **For best reliability**: Install `mpv` - it has the most robust buffering
2. **For minimal latency**: Use `aplay` with large buffers
3. **For network playback**: Prefer `mpv` or `ffplay` over `aplay`
4. **For battery life**: Use `afplay` on macOS (most efficient)

## Troubleshooting

### Check Clara logs
```bash
tail -f logs/server.log
```

### Enable verbose player output (for debugging)
Edit the player command to remove quiet flags temporarily:
```python
# In clarasattention/attention.py or clarasvoice/speak.py
# Change:
['mpv', '--really-quiet']
# To:
['mpv', '-v']
```

### Verify audio file format
```bash
file audio/*.wav
ffprobe -hide_banner audio/<file>.wav
```

