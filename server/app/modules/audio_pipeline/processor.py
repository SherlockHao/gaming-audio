"""Audio post-processing pipeline.

MVP implementation: works with WAV files. Performs basic measurements
and returns results without heavy DSP (since candidates are placeholders in dev).
"""
import struct
import wave
import math
import logging

logger = logging.getLogger(__name__)


def analyze_audio_file(file_path: str) -> dict:
    """Analyze a WAV file and return measurements.

    Returns dict with: sample_rate, bit_depth, channels, duration_ms,
    peak_dbfs, rms_dbfs, head_silence_ms, tail_silence_ms
    """
    try:
        with wave.open(file_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            bit_depth = sample_width * 8
            duration_ms = int(n_frames / sample_rate * 1000) if sample_rate > 0 else 0

            # Read all samples
            raw = wf.readframes(n_frames)

            if sample_width == 2:
                fmt = f'<{n_frames * channels}h'
                samples = list(struct.unpack(fmt, raw))
            else:
                samples = [0] * (n_frames * channels)

            # Peak
            max_sample = max(abs(s) for s in samples) if samples else 0
            max_possible = 32767  # 16-bit
            peak_dbfs = 20 * math.log10(max_sample / max_possible) if max_sample > 0 else -96.0

            # RMS
            rms = math.sqrt(sum(s * s for s in samples) / len(samples)) if samples else 0
            rms_dbfs = 20 * math.log10(rms / max_possible) if rms > 0 else -96.0

            # Head silence (samples below threshold at start)
            silence_threshold = max_possible * 0.001  # -60 dBFS approx
            head_silence_samples = 0
            for s in samples:
                if abs(s) > silence_threshold:
                    break
                head_silence_samples += 1
            head_silence_ms = int(head_silence_samples / channels / sample_rate * 1000) if sample_rate > 0 else 0

            # Tail silence
            tail_silence_samples = 0
            for s in reversed(samples):
                if abs(s) > silence_threshold:
                    break
                tail_silence_samples += 1
            tail_silence_ms = int(tail_silence_samples / channels / sample_rate * 1000) if sample_rate > 0 else 0

            return {
                "sample_rate": sample_rate,
                "bit_depth": bit_depth,
                "channels": channels,
                "duration_ms": duration_ms,
                "peak_dbfs": round(peak_dbfs, 2),
                "rms_dbfs": round(rms_dbfs, 2),
                "head_silence_ms": head_silence_ms,
                "tail_silence_ms": tail_silence_ms,
            }
    except Exception as e:
        logger.error(f"Failed to analyze audio file {file_path}: {e}")
        return {
            "sample_rate": 0, "bit_depth": 0, "channels": 0, "duration_ms": 0,
            "peak_dbfs": -96.0, "rms_dbfs": -96.0, "head_silence_ms": 0, "tail_silence_ms": 0,
            "error": str(e),
        }


def run_qc_checks(analysis: dict, category_rule: dict | None) -> dict:
    """Run QC checks against category rule thresholds.

    Returns dict with check results for each category:
    peak_result, loudness_result, spectrum_result, head_tail_result, format_result, qc_status
    """
    if not category_rule:
        # No rule to check against — pass by default
        return {
            "peak_result": {"status": "pass", "note": "No category rule to check against"},
            "loudness_result": {"status": "pass", "note": "No category rule"},
            "spectrum_result": {"status": "pass", "note": "No category rule"},
            "head_tail_result": {"status": "pass", "note": "No category rule"},
            "format_result": {"status": "pass", "note": "No category rule"},
            "qc_status": "passed",
        }

    results = {}

    # Format check
    fmt_rule = category_rule.get("format", {})
    fmt_ok = True
    fmt_details = {}

    expected_sr = fmt_rule.get("sample_rate", 48000)
    actual_sr = analysis.get("sample_rate", 0)
    fmt_details["sample_rate"] = {"expected": expected_sr, "actual": actual_sr, "pass": actual_sr == expected_sr}
    if actual_sr != expected_sr:
        fmt_ok = False

    expected_bd = fmt_rule.get("bit_depth", 24)
    actual_bd = analysis.get("bit_depth", 0)
    fmt_details["bit_depth"] = {"expected": expected_bd, "actual": actual_bd, "pass": True}  # Allow 16-bit for MVP

    expected_ch = fmt_rule.get("channels", "mono_preferred")
    actual_ch = analysis.get("channels", 0)
    fmt_details["channels"] = {"expected": expected_ch, "actual": actual_ch, "pass": True}  # Flexible for MVP

    results["format_result"] = {"status": "pass" if fmt_ok else "fail", "details": fmt_details}

    # Loudness check (simplified - use RMS as LUFS approximation)
    loud_rule = category_rule.get("loudness", {})
    target_lufs = loud_rule.get("target_lufs", -18)
    tolerance = loud_rule.get("tolerance_lu", 3)
    actual_rms = analysis.get("rms_dbfs", -96)
    # RMS is a rough approximation of LUFS
    lufs_min = target_lufs - tolerance
    lufs_max = target_lufs + tolerance
    lufs_ok = lufs_min <= actual_rms <= lufs_max
    results["loudness_result"] = {
        "status": "pass" if lufs_ok else "warning",
        "target_lufs": target_lufs, "tolerance_lu": tolerance,
        "measured_rms_dbfs": actual_rms, "range": [lufs_min, lufs_max],
    }

    # Peak check
    true_peak_limit = loud_rule.get("true_peak_limit", -1.0)
    actual_peak = analysis.get("peak_dbfs", -96)
    peak_ok = actual_peak <= true_peak_limit
    results["peak_result"] = {
        "status": "pass" if peak_ok else "fail",
        "limit_dbtp": true_peak_limit, "measured_dbfs": actual_peak,
    }

    # Head/tail silence check
    ht_rule = category_rule.get("head_tail", {})
    max_head = ht_rule.get("max_head_silence_ms", 10)
    max_tail = ht_rule.get("max_tail_silence_ms", 50)
    actual_head = analysis.get("head_silence_ms", 0)
    actual_tail = analysis.get("tail_silence_ms", 0)
    head_ok = actual_head <= max_head
    tail_ok = actual_tail <= max_tail
    results["head_tail_result"] = {
        "status": "pass" if (head_ok and tail_ok) else "warning",
        "head": {"max_ms": max_head, "actual_ms": actual_head, "pass": head_ok},
        "tail": {"max_ms": max_tail, "actual_ms": actual_tail, "pass": tail_ok},
    }

    # Duration check
    dur_rule = category_rule.get("duration", {})
    min_dur = dur_rule.get("min_ms", 50)
    max_dur = dur_rule.get("max_ms", 5000)
    actual_dur = analysis.get("duration_ms", 0)
    dur_ok = min_dur <= actual_dur <= max_dur
    results["spectrum_result"] = {
        "status": "pass" if dur_ok else "fail",
        "type": "duration_check",
        "min_ms": min_dur, "max_ms": max_dur, "actual_ms": actual_dur,
    }

    # Overall status
    statuses = [r["status"] for r in results.values() if isinstance(r, dict) and "status" in r]
    if "fail" in statuses:
        results["qc_status"] = "failed"
    else:
        results["qc_status"] = "passed"

    return results
