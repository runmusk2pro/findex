from hypothesis import given, strategies as st
from findex.tokenizer import tokenize
from findex.index import Index, DocMeta, Posting
from findex.store import save_index_pickle, load_index_pickle
from pathlib import Path

# Властивість 1: Токенізатор ніколи не викликає виключень на будь-якому тексті
@given(st.text())
def test_property_tokenize_never_fails(text: str) -> None:
    _ = list(tokenize(text))

# Властивість 2: Збереження та завантаження індексу зберігає кількість термінів (Round-trip)
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
def test_property_index_save_load_roundtrip(terms: list[str]) -> None:
    idx = Index()
    idx.documents[1] = DocMeta(1, "Doc1", 10)
    for i, t in enumerate(terms):
        idx.index[t] = [Posting(1, i + 1)]
    
    tmp_file = Path("temp_hypo_test.bin")
    try:
        save_index_pickle(idx, tmp_file)
        loaded_idx, _ = load_index_pickle(tmp_file)
        assert len(loaded_idx) == len(idx)
    finally:
        if tmp_file.exists():
            tmp_file.unlink()

# Властивість 3: Двопоінтерне злиття завжди збігається з перетином множин (Oracle property)
@given(
    st.lists(st.integers(min_value=1, max_value=1000), unique=True).map(sorted),
    st.lists(st.integers(min_value=1, max_value=1000), unique=True).map(sorted)
)
def test_property_merge_equals_set_intersection(a: list[int], b: list[int]) -> None:
    res: list[int] = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            res.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    assert res == sorted(list(set(a) & set(b)))