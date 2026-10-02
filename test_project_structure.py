from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_core_files_exist():
    assert (ROOT / "src" / "app.py").exists()
    assert (ROOT / "sql" / "schema.sql").exists()
    assert (ROOT / "requirements.txt").exists()
    assert (ROOT / "README.md").exists()
