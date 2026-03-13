"""Central path constants for the data/ directory structure.

All scripts import from here instead of hardcoding paths.
"""

import os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT, "data")

SCOUT_DIR = os.path.join(DATA_DIR, "scout")
STRATEGY_DIR = os.path.join(DATA_DIR, "strategy")
CONTENT_DIR = os.path.join(DATA_DIR, "content")
METRICS_DIR = os.path.join(DATA_DIR, "metrics")
OUTBOUND_DIR = os.path.join(DATA_DIR, "outbound")
PIPELINE_DIR = os.path.join(DATA_DIR, "pipeline")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
TASKS_DIR = os.path.join(DATA_DIR, "tasks")
MISC_DIR = os.path.join(DATA_DIR, "misc")


def ensure_dirs():
    """Create all subdirectories if they don't exist."""
    for d in [SCOUT_DIR, STRATEGY_DIR, CONTENT_DIR, METRICS_DIR,
              OUTBOUND_DIR, PIPELINE_DIR, REPORTS_DIR, TASKS_DIR, MISC_DIR]:
        os.makedirs(d, exist_ok=True)
