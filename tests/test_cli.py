from typer.testing import CliRunner
from findex.cli import app
from pathlib import Path

runner = CliRunner()

def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Findex" in result.stdout

def test_cli_search_missing_index() -> None:
    result = runner.invoke(app, ["search", "non_existent.bin", "query"])
    assert result.exit_code != 0

def test_cli_full_workflow(sample_corpus_dir: Path, tmp_path: Path) -> None:
    index_file = tmp_path / "test_index.bin"
    
    # 1. findex index
    res_idx = runner.invoke(app, ["index", str(sample_corpus_dir), "--out", str(index_file)])
    assert res_idx.exit_code == 0
    assert index_file.exists()

    # 2. findex search (перевіряємо що таблиця вивелась або є результати)
    res_search = runner.invoke(app, ["search", str(index_file), "python"])
    assert res_search.exit_code == 0
    assert "Score" in res_search.stdout or "Doc ID" in res_search.stdout

    # 3. findex search --json
    res_json = runner.invoke(app, ["search", str(index_file), "python", "--json"])
    assert res_json.exit_code == 0
    assert "[" in res_json.stdout

    # 4. findex stats
    res_stats = runner.invoke(app, ["stats", str(index_file)])
    assert res_stats.exit_code == 0