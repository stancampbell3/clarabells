"""Lightweight 'Chatterbox' TTS adapter.
This module provides a ChatterboxTTS.synthesize_to_wav(text, out_path) function that
writes a valid WAV file containing a short tone whose length depends on the text length.

This is a deterministic, dependency-free placeholder for a real TTS engine.
"""
import wave
import struct
import math

class ChatterboxTTS:
    @staticmethod
    def synthesize_to_wav(text: str, out_path: str, rate: int = 22050):
        """
        Synthesize a short WAV file from `text` and write to `out_path`.
        The generated audio is a simple sine wave; duration scales with text length.
        """
        # normalize text and compute a deterministic frequency and duration
        if not text:
            text = " "
        text_len = max(1, len(text))
        duration = min(10.0, 0.05 * text_len + 0.5)  # between 0.55s and ~10s
        # frequency derived from text chars (in range ~220-880Hz)
        freq = 220 + (sum(ord(c) for c in text) % 660)

        n_samples = int(rate * duration)
        amplitude = 16000  # for 16-bit audio

        with wave.open(out_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(rate)

            for i in range(n_samples):
                t = float(i) / rate
                # simple sine wave; add mild envelope to avoid clicks
                envelope = 1.0
                # fade in/out 50ms
                fade_ms = 0.05
                fade_samples = int(rate * fade_ms)
                if i < fade_samples:
                    envelope = i / fade_samples
                elif i > n_samples - fade_samples:
                    envelope = (n_samples - i) / fade_samples

                sample = amplitude * envelope * math.sin(2.0 * math.pi * freq * t)
                wf.writeframes(struct.pack('<h', int(sample)))

        return out_path

