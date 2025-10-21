"""ChatterboxTTS integration for Clara server.

This module provides a ChatterboxTTS wrapper that lazy-loads the TTS model
and provides a simple synthesize_to_wav(text, out_path) interface.
"""
import logging
import torch
import soundfile as sf
from typing import Optional

logger = logging.getLogger(__name__)


class ChatterboxTTS:
    """Wrapper for ChatterboxTTS model with lazy loading."""

    _instance: Optional['_ChatterboxModel'] = None
    _sample_path: str = "app/assets/clara_sample.wav"  # Path to the voice sample for cloning

    @staticmethod
    def synthesize_to_wav(text: str, out_path: str, rate: int = 22050):
        """
        Synthesize speech from text and write to a WAV file.

        Args:
            text: The text to synthesize
            out_path: Path where the WAV file should be written
            rate: Sample rate (ignored - uses model's native rate)

        Returns:
            The output path
        """
        # Lazy load the model on first use
        if ChatterboxTTS._instance is None:
            ChatterboxTTS._instance = _ChatterboxModel()

        # Generate audio
        # wav = ChatterboxTTS._instance.model.generate(text)
        wav = ChatterboxTTS._instance.model.generate(
                text,
                audio_prompt_path= ChatterboxTTS._sample_path,
                exaggeration=1.0,
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


class _ChatterboxModel:
    """Internal singleton for the loaded ChatterboxTTS model."""

    def __init__(self):
        """Load the ChatterboxTTS model from HuggingFace Hub."""
        from app.chatterbox.tts import ChatterboxTTS as _ChatterboxTTS

        # Auto-detect best available device
        if torch.cuda.is_available():
            device = "cuda"
            logger.info("Using CUDA device for TTS")
        elif torch.backends.mps.is_available():
            device = "mps"
            logger.info("Using MPS device for TTS")
        else:
            device = "cpu"
            logger.info("Using CPU device for TTS")

        logger.info("Loading ChatterboxTTS model from HuggingFace Hub (this may take a moment)...")
        self.model = _ChatterboxTTS.from_pretrained(device=device)
        logger.info("ChatterboxTTS model loaded successfully")
