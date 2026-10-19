import sys
import json
import logging
import typer
from pathlib import Path
from typing import Literal, Annotated
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from findex.index import Index, open_index, DocMeta, Posting
from findex.reader import iter_documents
from findex.tokenizer import tokenize
from findex.search import execute_search
from findex.ranking import BM25, TfIdf
from findex.store import save_index_pickle

app = typer.Typer(help="Findex: CLI Search Engine Tool", add_completion=False)
err_console = Console(stderr=True)
console = Console()
log = logging.getLogger("findex")

def setup_logging(verbose: int) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

@app.callback()
def main(
    v: Annotated[int, typer.Option("-v", "--verbose", count=True, help="Збільшити рівень деталізації логів")] = 0
) -> None:
    setup_logging(v)

@app.command()
def index(
    corpus: Annotated[Path, typer.Argument(help="Папка з текстовими файлами")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Шлях для збереження індексу")] = Path("index.bin"),
) -> None:
    """Побудувати інвертований індекс з корпусу документів."""
    if not corpus.exists() or not corpus.is_dir():
        err_console.print(f"[red]Помилка: Папку '{corpus}' не знайдено.[/red]")
        raise typer.Exit(code=1)

    idx = Index()
    doc_id = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=err_console,
    ) as progress:
        task = progress.add_task("Індексація документів...", total=None)
        
        for text in iter_documents(corpus):
            doc_id += 1
            tokens = list(tokenize(text))
            doc_len = len(tokens)
            
            idx.documents[doc_id] = DocMeta(doc_id=doc_id, title=f"Doc_{doc_id}", length=doc_len)
            
            counts: dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
                
            for term, freq in counts.items():
                if term not in idx.index:
                    idx.index[term] = []
                idx.index[term].append(Posting(doc_id=doc_id, term_frequency=freq))
                
            progress.update(task, advance=1, description=f"Оброблено документів: {doc_id}")

    save_index_pickle(idx, out)
    console.print(f"[green]Успішно заіндексовано {doc_id} документів у '{out}'.[/green]")

@app.command()
def search(
    index_path: Annotated[Path, typer.Argument(help="Шлях до файлу індексу")],
    query: Annotated[str, typer.Argument(help="Пошуковий запит")],
    k: Annotated[int, typer.Option("--k", "-k", help="Кількість результатів")] = 10,
    scorer_name: Annotated[Literal["bm25", "tfidf"], typer.Option("--scorer", help="Алгоритм ранжування")] = "bm25",
    output_json: Annotated[bool, typer.Option("--json", help="Формат виводу JSON для пайпів")] = False,
) -> None:
    """Виконати пошук у завантаженому індексі."""
    if not index_path.exists():
        err_console.print(f"[red]Помилка: Файл індексу '{index_path}' не існує.[/red]")
        raise typer.Exit(code=1)

    try:
        ranker = BM25() if scorer_name == "bm25" else TfIdf()
        with open_index(index_path) as idx:
            results = execute_search(query, idx, ranker, k=k)

            if output_json:
                data = [{"rank": i, "score": r.score, "doc_id": r.doc_id, "title": r.title} for i, r in enumerate(results, 1)]
                print(json.dumps(data, ensure_ascii=False, indent=2))
                return

            if not results:
                console.print("[yellow]Нічого не знайдено.[/yellow]")
                return

            table = Table(title=f"Результати пошуку для: '{query}'")
            table.add_column("№", justify="right", style="cyan")
            table.add_column("Score", style="magenta")
            table.add_column("Doc ID", style="green")
            table.add_column("Title", style="bold")

            for rank, res in enumerate(results, 1):
                table.add_row(str(rank), f"{res.score:.4f}", str(res.doc_id), res.title)

            console.print(table)

    except Exception as e:
        err_console.print(f"[red]Помилка під час виконання запиту: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def stats(index_path: Annotated[Path, typer.Argument(help="Шлях до файлу індексу")]) -> None:
    """Показати статистику індексу."""
    if not index_path.exists():
        err_console.print(f"[red]Помилка: Файл індексу '{index_path}' не існує.[/red]")
        raise typer.Exit(code=1)

    with open_index(index_path) as idx:
        table = Table(title="Статистика Індексу")
        table.add_column("Метрика", style="bold cyan")
        table.add_column("Значення", style="green")

        table.add_row("Загалом документів", str(idx.num_docs))
        table.add_row("Унікальних термінів", str(len(idx)))
        table.add_row("Середня довжина документа", f"{idx.avg_doc_length:.2f}")

        console.print(table)
         
if __name__ == "__main__":
    app()