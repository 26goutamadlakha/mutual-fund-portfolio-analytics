"""Run the complete mutual fund analytics workflow."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mf_analytics.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline(ROOT)
