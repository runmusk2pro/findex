import sys
import json
import logging
import time
import concurrent.futures
import typer
from pathlib import Path
from typing import Literal, Annotated
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from findex.index import open_index, build_partial, merge, PartialIndex
from findex.search import execute_search
from findex.ranking import BM25, TfIdf

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

def chunk_list(lst: list[Path], n: int) -> list[list[Path]]:
    """Ділить список на n приблизно рівних частин."""
    if n <= 0:
        return [lst]
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

@app.command()
def index(
    corpus: Annotated[Path, typer.Argument(help="Папка з текстовими файлами")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Шлях для збереження індексу")] = Path("index.bin"),
    workers: Annotated[int, typer.Option("--workers", "-w", help="Кількість воркерів (ядер)")] = 1,
    executor: Annotated[Literal["serial", "threads", "processes"], typer.Option("--executor", "-e", help="Тип паралелізму")] = "serial",
) -> None:
    """Побудувати інвертований індекс з використанням потоків/процесів."""
    if not corpus.exists() or not corpus.is_dir():
        err_console.print(f"[red]Помилка: Папку '{corpus}' не знайдено.[/red]")
        raise typer.Exit(code=1)

    # Збираємо всі .txt файли
    files = list(corpus.rglob("*.txt"))
    if not files:
        err_console.print("[yellow]Попередження: текстових файлів не знайдено.[/yellow]")
        raise typer.Exit(code=0)

    # Розбиваємо файли на чанки (по одному на воркера)
    actual_workers = min(workers, len(files))
    chunks = chunk_list(files, actual_workers)
    
    # Визначаємо стартовий doc_id для кожного чанка, щоб вони були унікальними
    start_ids: list[int] = []
    current_id = 1
    for c in chunks:
        start_ids.append(current_id)
        current_id += len(c)
        
    try:
        gil_status = "УВІМКНЕНО (True)" if sys._is_gil_enabled() else "ВИМКНЕНО (False)"  # type: ignore[reportPrivateUsage]
        console.print(f"[bold cyan]Статус GIL: {gil_status}[/bold cyan]")
    except AttributeError:
        console.print("[bold cyan]Статус GIL: Звичайна збірка (GIL завжди увімкнено)[/bold cyan]")

    t0_wall = time.perf_counter()
    t0_cpu = time.process_time()
    
    partials: list[PartialIndex] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=err_console,
    ) as progress:
        task = progress.add_task(f"Індексація ({executor}, {actual_workers} workers)...", total=len(chunks))

        if executor == "serial":
            for c, sid in zip(chunks, start_ids):
                partials.append(build_partial(c, sid))
                progress.update(task, advance=1)
                
        elif executor == "threads":
            with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as pool:
                futures = [pool.submit(build_partial, c, sid) for c, sid in zip(chunks, start_ids)]
                for fut in concurrent.futures.as_completed(futures):
                    partials.append(fut.result())
                    progress.update(task, advance=1)
                    
        elif executor == "processes":
            with concurrent.futures.ProcessPoolExecutor(max_workers=actual_workers) as pool:
                futures = [pool.submit(build_partial, c, sid) for c, sid in zip(chunks, start_ids)]
                for fut in concurrent.futures.as_completed(futures):
                    partials.append(fut.result())
                    progress.update(task, advance=1)

        progress.update(task, description="Злиття (merge)...", advance=0)
        
        t0_merge = time.perf_counter()
        final_index = merge(partials)
        t_merge = time.perf_counter() - t0_merge
        
        progress.update(task, description="Збереження індексу...", advance=0)
        from findex.store import save_index_pickle
        save_index_pickle(final_index, out)

    t_wall = time.perf_counter() - t0_wall
    t_cpu = time.process_time() - t0_cpu
    
    console.print(f"[green]Успішно![/green] Документів: {final_index.num_docs}")
    console.print(f"Wall time: {t_wall:.2f}s | CPU time: {t_cpu:.2f}s | Merge time: {t_merge:.2f}s")

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