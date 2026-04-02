"""AI audio generation adapter.

Uses external API when available, falls back to generating silent placeholder WAV files
for development/testing (mock mode).
"""
import os
import struct
import tempfile
import logging

logger = logging.getLogger(__name__)


async def generate_audio_candidates(
    prompt: str,
    count: int = 3,
    duration_ms: int = 1000,
    sample_rate: int = 48000,
    bit_depth: int = 24,
) -> list[dict]:
    """Generate audio candidate files.

    In MVP/development mode, generates placeholder WAV files with silence.
    In production, this would call an external AI audio generation API.

    Returns list of dicts with keys: file_path, duration_ms, source_model, generation_params
    """
    candidates = []
    for i in range(count):
        try:
            file_path = _generate_placeholder_wav(
                duration_ms=duration_ms,
                sample_rate=sample_rate,
                channels=1,
            )
            candidates.append({
                "file_path": file_path,
                "duration_ms": duration_ms,
                "source_model": "placeholder_v1",
                "generation_params": {
                    "prompt": prompt[:500],  # Truncate for storage
                    "candidate_index": i,
                    "sample_rate": sample_rate,
                    "bit_depth": bit_depth,
                },
            })
        except Exception as e:
            logger.error(f"Failed to generate candidate {i}: {e}")

    return candidates


def _generate_placeholder_wav(
    duration_ms: int = 1000,
    sample_rate: int = 48000,
    channels: int = 1,
) -> str:
    """Generate a silent WAV file as placeholder for development.

    Creates a valid 16-bit PCM WAV file filled with near-silence
    (very low amplitude noise to avoid being flagged as completely silent).
    """
    import random

    num_samples = int(sample_rate * duration_ms / 1000)

    # Generate very low amplitude noise (not pure silence, to be more realistic)
    samples = bytes(
        b for s in range(num_samples)
        for b in struct.pack('<h', random.randint(-10, 10))
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=tempfile.gettempdir())

    # Write WAV header (16-bit PCM)
    data_size = len(samples)
    header_size = 44

    tmp.write(b'RIFF')
    tmp.write(struct.pack('<I', data_size + header_size - 8))
    tmp.write(b'WAVE')
    tmp.write(b'fmt ')
    tmp.write(struct.pack('<I', 16))  # chunk size
    tmp.write(struct.pack('<H', 1))   # PCM format
    tmp.write(struct.pack('<H', channels))
    tmp.write(struct.pack('<I', sample_rate))
    tmp.write(struct.pack('<I', sample_rate * channels * 2))  # byte rate
    tmp.write(struct.pack('<H', channels * 2))  # block align
    tmp.write(struct.pack('<H', 16))  # bits per sample
    tmp.write(b'data')
    tmp.write(struct.pack('<I', data_size))
    tmp.write(samples)

    tmp.close()
    return tmp.name
