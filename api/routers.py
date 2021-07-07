"""
This module contains routing functions implementing the web API.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import database
from game.pathfinding import follow_parent_pointers, multi_target_bfs, single_target_bfs
from game.utilities import id_to_title, title_to_id
from .schemas import ArticlePath, ArticleWrapper, ManyArticlePaths

router = APIRouter()


@router.get(
    "/single",
    summary="Paths From One Start to One Endpoint",
    responses={status.HTTP_404_NOT_FOUND: {"msg": str}},
    response_model=ArticlePath,
)
async def path_from_src_to_dst(
    src: str = Query(..., description="starting article"),
    dst: str = Query(..., description="destination article"),
    db: Session = Depends(database.get_db),
):
    """
    Find a path of articles which minimizes the number of clicks starting from ``src``
    and ending at ``dst``.
    """
    try:
        path = single_target_bfs(db, src, dst)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find matching article for at least one of {src} and {dst}",
        )
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No path found between {src} and {dst}",
        )
    article_path = []
    for article_title in path:
        article_id = title_to_id(db, article_title)
        article_url = f"https://en.wikipedia.org/?curid={article_id}"
        article_path.append(
            ArticleWrapper(
                id=article_id,
                title=article_title,
                link=article_url,  # type: ignore
            )
        )
    return ArticlePath(articles=article_path)


@router.get(
    "/many", summary="Paths from One Start To Many Endpoints", response_model=ManyArticlePaths
)
async def paths_from_src(
    src: str = Query(..., description="starting article"),
    dsts: list[str] = Query(..., description="destination articles"),
    db: Session = Depends(database.get_db),
):
    """
    Find a shortest path from ``src`` to each destination in ``dsts``, where a shortest path
    minimizes the number of clicks between two articles.
    """
    paths: dict[str, Optional[ArticlePath]] = {}
    ppd = multi_target_bfs(db, src)
    for dst in dsts:
        dst_id = title_to_id(db, dst)
        path = follow_parent_pointers(dst_id, ppd)
        if path is None:
            paths[dst] = None
            continue
        article_path = []
        for article_id in path:
            article_title = id_to_title(db, article_id)
            article_url = f"https://en.wikipedia.org/?curid={article_id}"
            article_path.append(
                ArticleWrapper(
                    id=article_id,
                    title=article_title,
                    link=article_url,  # type: ignore
                )
            )
        paths[dst] = ArticlePath(articles=article_path)
    return ManyArticlePaths(paths=paths)
