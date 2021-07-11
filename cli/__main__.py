#!/usr/bin/env python3
"""
Start the CLI app.
"""
from typing import Optional

import typer
from sqlalchemy.orm.session import Session

from database import get_db
from game.pathfinding import follow_parent_pointers, multi_target_bfs, bidi_bfs
from game.utilities import id_to_title, title_to_id

app = typer.Typer()


@app.command("single")
def single_target(
    src: str = typer.Argument(..., help="Starting article"),
    dst: str = typer.Argument(..., help="Ending article"),
) -> None:
    """
    Find a shortest path of articles between src and dst.
    """
    session: Session = next(get_db())
    try:
        path = bidi_bfs(session, src, dst)
    except ValueError as e:
        msg = typer.style(e, fg=typer.colors.WHITE, bg=typer.colors.RED)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)
    typer.echo(_display_path(src, dst, path))


@app.command("multi")
def multi_target(
    src: str = typer.Argument(..., help="Starting article"),
    dsts: list[str] = typer.Argument(..., help="Ending articles"),
) -> None:
    """
    Find a shortest path of articles between src and destination, for each destination in dsts.
    """
    session: Session = next(get_db())
    try:
        parents = multi_target_bfs(session, src)
    except ValueError as e:
        msg = typer.style(e, fg=typer.colors.WHITE, bg=typer.colors.RED)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)
    for dst in dsts:
        try:
            dst_id = title_to_id(session, dst)
        except ValueError as e:
            msg = typer.style(e, fg=typer.colors.WHITE, bg=typer.colors.RED)
            typer.echo(msg, err=True)
        else:
            path = follow_parent_pointers(dst_id, parents)
            article_path = (
                None if path is None else [id_to_title(session, id_) for id_ in path]
            )
            typer.echo(_display_path(src, dst, article_path))


def _display_path(src: str, dst: str, path: Optional[list[str]]) -> str:
    return (
        f"No path found between {src} and {dst}"
        if path is None
        else f"Path from {src} to {dst}: {path}"
    )


if __name__ == "__main__":
    app(prog_name="wikigame")
