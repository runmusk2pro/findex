import heapq
from dataclasses import dataclass, field
from findex.index import Index
from findex.query import parse, QueryNode, Term, Phrase, And, Or, Not
from findex.ranking import Scorer
from findex.utils import timed

@dataclass(order=True)
class SearchResult:
    score: float
    doc_id: int = field(compare=False)
    snippet: str = field(compare=False)
    title: str = field(compare=False)

def extract_terms_from_ast(node: QueryNode) -> list[str]:
    """Витягує слова з дерева запиту для підсвітки у сніпеті."""
    if isinstance(node, Term):
        return [node.term]
    if isinstance(node, Phrase):
        return list(node.terms)
    if isinstance(node, (And, Or)):
        return extract_terms_from_ast(node.left) + extract_terms_from_ast(node.right)
    if isinstance(node, Not):
        return extract_terms_from_ast(node.child)
    return []

def make_snippet(text: str, query_terms: list[str], window: int = 80) -> str:
    """Вирізає шматок тексту навколо знайденого слова і виділяє його."""
    if not text:
        return ""
    
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
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
    
    for term in query_terms:
        snippet = snippet.replace(term, f"\033[92m{term}\033[0m")
        snippet = snippet.replace(term.capitalize(), f"\033[92m{term.capitalize()}\033[0m")
        
    return snippet

@timed
def execute_search(
    query_str: str,
    index: Index,
    scorer: Scorer,
    corpus: dict[int, str] | None = None,
    k: int = 10
) -> list[SearchResult]:
    corpus_dict: dict[int, str] = corpus if corpus is not None else {}
    
    ast = parse(query_str)
    query_terms = extract_terms_from_ast(ast)
    
    matching_docs = ast.evaluate(index)
    
    scores: dict[int, float] = {doc_id: 0.0 for doc_id in matching_docs}
    for term in query_terms:
        if term in index:
            for posting in index[term]:
                if posting.doc_id in scores:
                    scores[posting.doc_id] += scorer.score(term, posting, index)
                    
    results: list[SearchResult] = []
    for doc_id, score in scores.items():
        text = corpus_dict.get(doc_id, "")
        title = index.documents[doc_id].title if doc_id in index.documents else f"Doc {doc_id}"
        snippet = make_snippet(text, query_terms)
        results.append(SearchResult(score=score, doc_id=doc_id, snippet=snippet, title=title))
        
    return heapq.nlargest(k, results)