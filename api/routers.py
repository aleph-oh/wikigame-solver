from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import database
from game.utilities import id_to_title, title_to_id
from .schemas import ArticlePath, ArticleWrapper, ManyArticlePaths
from game.pathfinding import follow_parent_pointers, single_target_bfs, multi_target_bfs

router = APIRouter()


@router.get(
    "/single",
    responses={status.HTTP_404_NOT_FOUND: {"msg": str}},
    response_model=ArticlePath,
)
async def path_from_first_to_second(
    src: str, dst: str, db: Session = Depends(database.get_db)
):
    path = single_target_bfs(db, src, dst)
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


@router.get("/many", response_model=ManyArticlePaths)
async def paths_from_first(
    src: str, dsts: list[str], db: Session = Depends(database.get_db)
):
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
