import pytest
from pathlib import Path
from findex.index import Index, DocMeta, Posting

@pytest.fixture
def sample_corpus_dir(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "doc1.txt").write_text("python async await event loop", encoding="utf-8")
    (corpus / "doc2.txt").write_text("python web framework fastapi django", encoding="utf-8")
    (corpus / "doc3.txt").write_text("java spring boot framework", encoding="utf-8")
    return corpus

@pytest.fixture
def sample_index() -> Index:
    idx = Index()
    idx.documents[1] = DocMeta(doc_id=1, title="Doc1", length=5)
    idx.documents[2] = DocMeta(doc_id=2, title="Doc2", length=5)
    idx.documents[3] = DocMeta(doc_id=3, title="Doc3", length=4)
    
    idx.index["python"] = [Posting(1, 1, [0]), Posting(2, 1, [0])]
    idx.index["async"] = [Posting(1, 1, [1])]
    idx.index["await"] = [Posting(1, 1, [2])]
    idx.index["framework"] = [Posting(2, 1, [3]), Posting(3, 1, [3])]
    idx.index["java"] = [Posting(3, 1, [0])]
    return idx