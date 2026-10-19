import pytest
from findex.index import Index, open_index
from findex.ranking import BM25, TfIdf
from findex.store import save_index_pickle
from pathlib import Path

def test_index_dunder_methods(sample_index: Index) -> None:
    assert len(sample_index) == 5
    assert "python" in sample_index
    assert sample_index["python"][0].doc_id == 1
    assert sample_index.num_docs == 3
    assert sample_index.avg_doc_length == 14.0 / 3.0

def test_index_key_error(sample_index: Index) -> None:
    with pytest.raises(KeyError):
        _ = sample_index["nonexistent"]

def test_tfidf_scorer(sample_index: Index) -> None:
    scorer = TfIdf()
    score = scorer.score("python", sample_index["python"][0], sample_index)
    assert score > 0.0

def test_bm25_scorer(sample_index: Index) -> None:
    scorer = BM25()
    score = scorer.score("python", sample_index["python"][0], sample_index)
    assert score > 0.0

def test_open_index_context_manager(sample_index: Index, tmp_path: Path) -> None:
    path = tmp_path / "test.bin"
    save_index_pickle(sample_index, path)
    with open_index(path) as loaded_idx:
        assert len(loaded_idx) == len(sample_index)