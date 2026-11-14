# (b) Every notebook runs top to bottom offline with no errors.
import json
import os

import nbformat
import pytest
from nbclient import NotebookClient

from conftest import ROOT

NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))


def run_notebook(path, output_dir):
    nb = nbformat.read(path, as_version=4)
    os.environ["KIT_OUTPUT_DIR"] = str(output_dir)
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(path.parent)}}).execute()
    return nb


@pytest.mark.parametrize("path", NOTEBOOKS, ids=[p.name for p in NOTEBOOKS])
def test_notebook_runs(path, tmp_path):
    run_notebook(path, tmp_path)


def test_traces_notebook_writes_backlog(tmp_path):
    run_notebook(ROOT / "notebooks" / "02_traces_pandas.ipynb", tmp_path)
    header = (tmp_path / "failure_backlog.csv").read_text().splitlines()[0]
    for col in ["trace_id", "segment", "layer_guess", "severity"]:
        assert col in header


def test_harness_writes_one_log_line_per_step(tmp_path):
    run_notebook(ROOT / "notebooks" / "06_harness.ipynb", tmp_path)
    lines = (tmp_path / "traces" / "run.jsonl").read_text().splitlines()
    assert lines and all({"input", "decision", "output", "latency_s"} <= set(json.loads(x)) for x in lines)
