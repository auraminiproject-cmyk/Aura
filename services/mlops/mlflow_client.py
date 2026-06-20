"""MLflow tracking — optional self-hosted (no card). Falls back to local ./mlruns."""

import logging
import os

logger = logging.getLogger(__name__)


def log_training_run(name: str, params: dict, metrics: dict) -> str | None:
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
    try:
        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        with mlflow.start_run(run_name=name):
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            return mlflow.active_run().info.run_id if mlflow.active_run() else None
    except ImportError:
        logger.info("MLflow not installed — metrics: %s %s", params, metrics)
        return None
