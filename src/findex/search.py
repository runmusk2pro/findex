import heapq
from functools import lru_cache
from dataclasses import dataclass, field
from findex.index import Index
from findex.query import parse, Term, Phrase
from findex.ranking import Scorer
from findex.utils import timed

@dataclass(order=True)
class SearchResult:
    score: float
    doc_id: int = field(compare=False)
    snippet: str = field(compare=False)
    title: str = field(compare=False)

def extract_terms_from_ast(node) -> list[str]:
    """Витягує слова з дерева запиту для підсвітки у сніпеті."""
    if isinstance(node, Term): return [node.term]
    if isinstance(node, Phrase): return node.terms
    if hasattr(node, 'left'): return extract_terms_from_ast(node.left) + extract_terms_from_ast(node.right)
    if hasattr(node, 'child'): return extract_terms_from_ast(node.child)
    return []

def make_snippet(text: str, query_terms: list[str], window: int = 80) -> str:
    """Вирізає шматок тексту навколо знайденого слова і виділяє його."""
    if not text: return ""
    
    text_lower = text.lower()
    best_pos = -1
    
    for term in query_terms:
        pos = text_lower.find(term)
        if pos != -1:
            best_pos = pos
            break
            
    if best_pos == -1:
        snippet = text[:window * 2] + "..."
    else:
        start = max(0, best_pos - window)
        end = min(len(text), best_pos + window)
        snippet = text[start:end]
        if start > 0: snippet = "..." + snippet
        if end < len(text): snippet = snippet + "..."
    
    for term in query_terms:
        snippet = snippet.replace(term, f"\033[92m{term}\033[0m") # Зелений колір у терміналі
        snippet = snippet.replace(term.capitalize(), f"\033[92m{term.capitalize()}\033[0m")
        
    return snippet

# Ми кешуємо результати за самим запитом.
# @timed виведе в консоль, скільки мілісекунд пішло на пошук.
@timed
#@lru_cache(maxsize=256)
def execute_search(query_str: str, index: Index, scorer: Scorer, corpus: dict[int, str] = None, k: int = 10) -> list[SearchResult]:
    corpus = corpus or {}
    
    ast = parse(query_str)
    query_terms = extract_terms_from_ast(ast)
    
    # 1. Знаходимо всі документи, що відповідають булевій умові (AND/OR/NOT)
    matching_docs = ast.evaluate(index)
    
    # 2. Рахуємо бали для цих документів
    scores = {doc_id: 0.0 for doc_id in matching_docs}
    for term in query_terms:
        if term in index:
            for posting in index[term]:
                if posting.doc_id in scores:
                    scores[posting.doc_id] += scorer.score(term, posting, index)
                    
    # 3. Формуємо результати
    results = []
    for doc_id, score in scores.items():
        text = corpus.get(doc_id, "")
        title = index.documents[doc_id].title if doc_id in index.documents else f"Doc {doc_id}"
        snippet = make_snippet(text, query_terms)
        results.append(SearchResult(score=score, doc_id=doc_id, snippet=snippet, title=title))
        
    # Повертаємо топ-K
    return heapq.nlargest(k, results)