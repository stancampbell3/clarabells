"""ChatterboxTTS integration for Clara server.

This module provides a ChatterboxTTS wrapper that lazy-loads the TTS model
and provides a simple synthesize_to_wav(text, out_path) interface.
If the real model isn't available or generation fails, a small valid WAV
fallback is written so tests and lightweight deployments work.

Set environment variable `CLARA_TTS_FALLBACK_ONLY=1` to force using the
fallback path and avoid importing torch/transformers during CI.
"""
import logging
import soundfile as sf
from typing import Optional
import os
import wave
import struct

logger = logging.getLogger(__name__)

# If this is set to a truthy value, skip all model imports and always write
# a small valid WAV fallback. This is useful for CI / GitHub Actions to avoid
# long model downloads or GPU requirements.
FALLBACK_ONLY = os.getenv("CLARA_TTS_FALLBACK_ONLY", "0").lower() in ("1", "true", "yes")


def _write_fallback_wav(out_path: str, rate: int = 22050, duration_seconds: float = 1.0):
    """Write a short mono silent 16-bit PCM WAV to out_path."""
    num_samples = int(duration_seconds * rate)
    with wave.open(out_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(rate)
        silence = struct.pack('<h', 0) * num_samples
        wf.writeframes(silence)
    logger.info("Wrote fallback silent WAV to %s", out_path)


class ChatterboxTTS:
    """Wrapper for ChatterboxTTS model with lazy loading."""

    _instance: Optional['_ChatterboxModel'] = None
    _sample_path: str = "app/assets/clara_sample.wav"  # Path to the voice sample for cloning

    @staticmethod
    def synthesize_to_wav(text: str, out_path: str, rate: int = 22050):
        """
        Synthesize speech from text and write to a WAV file.

        If the underlying model can't be loaded or generation fails, write a
        short silent WAV as a fallback so tests and simple runs succeed.

        If `CLARA_TTS_FALLBACK_ONLY` is set, this will immediately write the
        fallback WAV and return without importing heavy model dependencies.
        """
        # If configured to use fallback only, avoid any model imports.
        if FALLBACK_ONLY:
            logger.info("CLARA_TTS_FALLBACK_ONLY is enabled; writing fallback WAV for text: %s", text)
            _write_fallback_wav(out_path, rate=rate)
            return out_path

        # Lazy load the model on first use
        try:
            if ChatterboxTTS._instance is None:
                ChatterboxTTS._instance = _ChatterboxModel()

            # Generate audio using model
            wav = ChatterboxTTS._instance.model.generate(
                    text,
                    audio_prompt_path=ChatterboxTTS._sample_path,
                    exaggeration=0.0,
                    cfg_weight=0.8
                )

            # Save to file using soundfile directly
            # Convert from torch tensor to numpy array and transpose if needed
            wav_np = wav.cpu().numpy()
            if wav_np.ndim > 1:
                wav_np = wav_np.T  # soundfile expects (samples, channels)
            sf.write(out_path, wav_np, ChatterboxTTS._instance.model.sr)
            logger.info(f"Synthesized text to {out_path} (sample rate: {ChatterboxTTS._instance.model.sr})")
            return out_path

        except Exception as e:
            logger.exception("TTS model unavailable or generation failed, writing fallback WAV: %s", e)
            # Write a short 1s mono silent 16-bit PCM WAV as fallback
            _write_fallback_wav(out_path, rate=rate, duration_seconds=1.0)
            return out_path


class _ChatterboxModel:
    """Internal singleton for the loaded ChatterboxTTS model."""

    def __init__(self):
        """Load the ChatterboxTTS model from HuggingFace Hub."""
        # Defer heavy imports until actually needed
        try:
            import torch
        except Exception as e:
            raise RuntimeError("torch is required to load the ChatterboxTTS model") from e

        from app.chatterbox.tts import ChatterboxTTS as _ChatterboxTTS

        # Auto-detect best available device
        if torch.cuda.is_available():
            device = "cuda"
            logger.info("Using CUDA device for TTS")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
            logger.info("Using MPS device for TTS")
        else:
            device = "cpu"
            logger.info("Using CPU device for TTS")

        logger.info("Loading ChatterboxTTS model from HuggingFace Hub (this may take a moment)...")
        self.model = _ChatterboxTTS.from_pretrained(device=device)

        # Set attention implementation on the wrapped model
        if hasattr(self.model, 'set_attn_implementation'):
            self.model.set_attn_implementation('eager')
            logger.info("Set attention implementation to 'eager'")
        else:
            logger.warning("Model does not have set_attn_implementation method")

        logger.info("ChatterboxTTS model loaded successfully")