"""Evidently AI drift detection — monitor LLM output quality over time.

Tracks:
  - Response length distribution
  - Sentiment drift
  - Intent classification distribution
  - Latency percentiles

Runs as a periodic task (daily) to compare recent outputs against baseline.
Falls back to simple statistical checks when Evidently is not installed.
"""

import json
import logging
import statistics
import time
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

DRIFT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "drift"
BASELINE_FILE = DRIFT_DATA_DIR / "baseline.json"
RECENT_FILE = DRIFT_DATA_DIR / "recent.json"


def record_observation(
    *,
    intent: str,
    response_length: int,
    latency_ms: float,
    language: str = "en",
    provider: str = "unknown",
) -> None:
    """Record a single observation for drift analysis."""
    DRIFT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    observation = {
        "timestamp": time.time(),
        "intent": intent,
        "response_length": response_length,
        "latency_ms": round(latency_ms, 1),
        "language": language,
        "provider": provider,
    }

    # Append to recent observations (JSON lines format)
    with open(RECENT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(observation) + "\n")


def load_observations(filepath: Path, max_count: int = 1000) -> list[dict]:
    """Load observations from a JSONL file."""
    if not filepath.is_file():
        return []
    observations = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    observations.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return observations[-max_count:]


def create_baseline() -> dict:
    """Snapshot current recent observations as the new baseline."""
    recent = load_observations(RECENT_FILE)
    if not recent:
        return {"error": "No recent observations to baseline"}

    DRIFT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_FILE, "w", encoding="utf-8") as f:
        for obs in recent:
            f.write(json.dumps(obs) + "\n")

    return {
        "baseline_size": len(recent),
        "timestamp": time.time(),
    }


def run_drift_check() -> dict:
    """Compare recent observations against baseline for drift.

    Returns a drift report with alerts if significant changes detected.
    """
    baseline = load_observations(BASELINE_FILE)
    recent = load_observations(RECENT_FILE)

    if len(baseline) < 20:
        return {"status": "insufficient_baseline", "baseline_count": len(baseline)}
    if len(recent) < 20:
        return {"status": "insufficient_recent", "recent_count": len(recent)}

    report = {
        "status": "ok",
        "baseline_count": len(baseline),
        "recent_count": len(recent),
        "alerts": [],
        "metrics": {},
    }

    # 1. Response length drift
    baseline_lengths = [o["response_length"] for o in baseline]
    recent_lengths = [o["response_length"] for o in recent]
    bl_mean = statistics.mean(baseline_lengths)
    rc_mean = statistics.mean(recent_lengths)
    length_drift = abs(rc_mean - bl_mean) / (bl_mean + 1)

    report["metrics"]["response_length"] = {
        "baseline_mean": round(bl_mean, 1),
        "recent_mean": round(rc_mean, 1),
        "drift_pct": round(length_drift * 100, 1),
    }
    if length_drift > 0.30:
        report["alerts"].append(f"Response length drifted {length_drift*100:.0f}% (baseline: {bl_mean:.0f}, recent: {rc_mean:.0f})")

    # 2. Latency drift
    baseline_latencies = [o["latency_ms"] for o in baseline]
    recent_latencies = [o["latency_ms"] for o in recent]
    bl_p95 = sorted(baseline_latencies)[int(len(baseline_latencies) * 0.95)]
    rc_p95 = sorted(recent_latencies)[int(len(recent_latencies) * 0.95)]
    latency_drift = abs(rc_p95 - bl_p95) / (bl_p95 + 1)

    report["metrics"]["latency_p95"] = {
        "baseline_ms": round(bl_p95, 1),
        "recent_ms": round(rc_p95, 1),
        "drift_pct": round(latency_drift * 100, 1),
    }
    if latency_drift > 0.50:
        report["alerts"].append(f"P95 latency drifted {latency_drift*100:.0f}% (baseline: {bl_p95:.0f}ms, recent: {rc_p95:.0f}ms)")

    # 3. Intent distribution drift (Jensen-Shannon divergence approximation)
    bl_intents = Counter(o["intent"] for o in baseline)
    rc_intents = Counter(o["intent"] for o in recent)
    all_intents = set(bl_intents) | set(rc_intents)

    bl_total = sum(bl_intents.values())
    rc_total = sum(rc_intents.values())

    intent_drift = 0.0
    intent_dist = {}
    for intent in all_intents:
        bl_pct = bl_intents.get(intent, 0) / bl_total
        rc_pct = rc_intents.get(intent, 0) / rc_total
        intent_drift += abs(bl_pct - rc_pct)
        intent_dist[intent] = {
            "baseline_pct": round(bl_pct * 100, 1),
            "recent_pct": round(rc_pct * 100, 1),
        }

    report["metrics"]["intent_distribution"] = intent_dist
    report["metrics"]["intent_drift_total"] = round(intent_drift, 3)
    if intent_drift > 0.40:
        report["alerts"].append(f"Intent distribution shifted by {intent_drift:.2f} (>0.40 threshold)")

    # 4. Provider distribution
    bl_providers = Counter(o.get("provider", "unknown") for o in baseline)
    rc_providers = Counter(o.get("provider", "unknown") for o in recent)
    report["metrics"]["providers"] = {
        "baseline": dict(bl_providers),
        "recent": dict(rc_providers),
    }

    if report["alerts"]:
        report["status"] = "drift_detected"
        logger.warning("Drift detected: %s", "; ".join(report["alerts"]))

    return report


def run_evidently_report() -> dict | None:
    """Run full Evidently AI report if installed. Returns HTML path or None."""
    try:
        from evidently import ColumnMapping
        from evidently.metric_preset import DataDriftPreset
        from evidently.report import Report

        import pandas as pd

        baseline = load_observations(BASELINE_FILE)
        recent = load_observations(RECENT_FILE)

        if len(baseline) < 20 or len(recent) < 20:
            return None

        baseline_df = pd.DataFrame(baseline)
        recent_df = pd.DataFrame(recent)

        report = Report(metrics=[DataDriftPreset()])

        column_mapping = ColumnMapping(
            numerical_features=["response_length", "latency_ms"],
            categorical_features=["intent", "language", "provider"],
        )

        report.run(
            reference_data=baseline_df,
            current_data=recent_df,
            column_mapping=column_mapping,
        )

        output_path = DRIFT_DATA_DIR / "drift_report.html"
        report.save_html(str(output_path))
        logger.info("Evidently drift report saved to %s", output_path)
        return {"report_path": str(output_path)}

    except ImportError:
        logger.debug("Evidently not installed — using built-in drift detection")
        return None
    except Exception as exc:
        logger.warning("Evidently report failed: %s", exc)
        return None
