from findex.query import parse, Term, And, Or, Not, Phrase

def test_parse_single_term() -> None:
    assert parse("python") == Term("python")

def test_parse_implicit_and() -> None:
    assert parse("python async") == And(Term("python"), Term("async"))

def test_parse_explicit_or() -> None:
    assert parse("python OR java") == Or(Term("python"), Term("java"))

def test_parse_not() -> None:
    assert parse("NOT java") == Not(Term("java"))

def test_parse_phrase() -> None:
    assert parse('"event loop"') == Phrase(["event", "loop"])

def test_parse_complex_tree() -> None:
    expected = And(
        And(Term("python"), Or(Term("async"), Term("await"))),
        Not(Term("java")),
    )
    assert parse("python AND (async OR await) NOT java") == expected