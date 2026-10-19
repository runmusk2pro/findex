import re
from dataclasses import dataclass
from findex.index import Index, Posting

class QueryNode:
    def __and__(self, other: "QueryNode") -> "And":
        return And(self, other)

    def __or__(self, other: "QueryNode") -> "Or":
        return Or(self, other)

    def __invert__(self) -> "Not":
        return Not(self)
    
    def evaluate(self, index: Index) -> set[int]:
        raise NotImplementedError

@dataclass(frozen=True)
class Term(QueryNode):
    term: str

    def evaluate(self, index: Index) -> set[int]:
        postings: list[Posting] = index.get(self.term, [])
        return {p.doc_id for p in postings}

@dataclass(frozen=True)
class Phrase(QueryNode):
    terms: list[str]

    def evaluate(self, index: Index) -> set[int]:
        if not self.terms:
            return set[int]()
        
        term_docs: list[set[int]] = [Term(t).evaluate(index) for t in self.terms]
        if not term_docs:
            return set[int]()
        
        doc_ids: set[int] = set[int].intersection(*term_docs)
        result: set[int] = set[int]()
        
        for doc_id in doc_ids:
            positions: list[list[int]] = []
            for t in self.terms:
                postings: list[Posting] = index[t]
                p_list: list[list[int]] = [p.positions for p in postings if p.doc_id == doc_id]
                if p_list:
                    positions.append(p_list[0])
            
            if len(positions) == len(self.terms) and positions[0]:
                for start_pos in positions[0]:
                    if all((start_pos + i) in positions[i] for i in range(1, len(self.terms))):
                        result.add(doc_id)
                        break

        return result

@dataclass(frozen=True)
class And(QueryNode):
    left: QueryNode
    right: QueryNode

    def evaluate(self, index: Index) -> set[int]:
        return self.left.evaluate(index) & self.right.evaluate(index)

@dataclass(frozen=True)
class Or(QueryNode):
    left: QueryNode
    right: QueryNode

    def evaluate(self, index: Index) -> set[int]:
        return self.left.evaluate(index) | self.right.evaluate(index)

@dataclass(frozen=True)
class Not(QueryNode):
    child: QueryNode

    def evaluate(self, index: Index) -> set[int]:
        all_docs: set[int] = set[int](index.documents.keys())
        return all_docs - self.child.evaluate(index)

# === Парсер рекурсивного спуску ===

def tokenize_query(query_str: str) -> list[str]:
    pattern = r'(".*?"|\(|\)|AND|OR|NOT|[^\s()"]+)'
    matches: list[str] = re.findall(pattern, query_str)
    return [t for t in matches if t.strip()]

def parse(query_str: str) -> QueryNode:
    tokens: list[str] = tokenize_query(query_str)
    pos: int = 0

    def peek() -> str | None:
        return tokens[pos] if pos < len(tokens) else None

    def consume() -> str:
        nonlocal pos
        token = peek()
        if token is None:
            raise ValueError("Несподіваний кінець запиту")
        pos += 1
        return token

    def parse_or() -> QueryNode:
        node: QueryNode = parse_and()
        while peek() == 'OR':
            _ = consume()
            node = Or(node, parse_and())
        return node

    def parse_and() -> QueryNode:
        node: QueryNode = parse_not()
        while True:
            next_token = peek()
            if next_token is None or next_token in ('OR', ')'):
                break
            if next_token == 'AND':
                _ = consume()
            node = And(node, parse_not())
        return node

    def parse_not() -> QueryNode:
        if peek() == 'NOT':
            _ = consume()
            return Not(parse_atom())
        return parse_atom()

    def parse_atom() -> QueryNode:
        token: str = consume()
        if token == '(':
            node: QueryNode = parse_or()
            if peek() == ')':
                _ = consume()
            return node
        elif token.startswith('"') and token.endswith('"'):
            words: list[str] = token.strip('"').split()
            return Phrase(words)
        else:
            return Term(token.lower())

    return parse_or()