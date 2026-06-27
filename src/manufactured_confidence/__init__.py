"""manufactured_confidence: shared harness and memory backends for the study
"Manufactured Confidence: How Memory Consolidation Turns Hearsay into Confident Facts."

The runnable probes live in the top-level ``experiments/`` directory and import from here, e.g.::

    from manufactured_confidence.harness import make_client, MODELS, load_env
    from manufactured_confidence.backends import make_backend, laundered
"""
from .harness import (
    DATA_DIR,
    MODELS,
    REPO_ROOT,
    extract_answer,
    load_env,
    make_client,
)

__all__ = [
    "DATA_DIR",
    "MODELS",
    "REPO_ROOT",
    "extract_answer",
    "load_env",
    "make_client",
]
