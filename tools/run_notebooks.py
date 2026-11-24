"""Execute all team notebooks in order and stop at the first error.

Usage:
    .venv\\Scripts\\python tools\\run_notebooks.py            # all notebooks
    .venv\\Scripts\\python tools\\run_notebooks.py 03 04a     # only notebooks whose name starts with these
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.stamp_notebooks import stamp  # noqa: E402

ORDER = [
    "01_data_cleaning",
    "02_eda",
    "03_feature_engineering",
    "04a_model_training",
    "04b_evaluation_and_evasion",
    "05_deployment",
]
TIMEOUT_S = 3600


def run(only: list[str]) -> None:
    stamp(verbose=False)
    for stem in ORDER:
        if only and not any(stem.startswith(o) for o in only):
            continue
        path = ROOT / "notebooks" / f"{stem}.ipynb"
        print(f"-> executing {path.name} ...", flush=True)
        start = time.time()
        cmd = [
            sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
            f"--ExecutePreprocessor.timeout={TIMEOUT_S}",
            "--ExecutePreprocessor.kernel_name=fraud-detection",
            str(path),
        ]
        result = subprocess.run(cmd, cwd=str(path.parent), capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr[-4000:])
            raise SystemExit(f"FAILED: {path.name}")
        size_mb = path.stat().st_size / 1e6
        print(f"   done in {time.time() - start:.0f} s, {size_mb:.2f} MB", flush=True)
    stamp(verbose=False)
    print("All requested notebooks executed and stamped.")


if __name__ == "__main__":
    run(sys.argv[1:])
