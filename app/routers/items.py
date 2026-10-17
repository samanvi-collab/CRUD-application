from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an item",
)
@router.post(
    "/",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
) -> schemas.ItemResponse:
    """Create a new item with name, optional description, and price."""
    return crud.create_item(db=db, item=item)


@router.get(
    "",
    response_model=List[schemas.ItemResponse],
    summary="Retrieve all items",
)
@router.get(
    "/",
    response_model=List[schemas.ItemResponse],
    include_in_schema=False,
)
def read_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[schemas.ItemResponse]:
    """Retrieve all items with pagination."""
    return crud.get_items(db=db, skip=skip, limit=limit)


@router.get(
    "/{item_id}",
    response_model=schemas.ItemResponse,
    summary="Retrieve an item by ID",
)
def read_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> schemas.ItemResponse:
    """Retrieve a single item by its ID."""
    db_item = crud.get_item(db=db, item_id=item_id)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return db_item


@router.put(
    "/{item_id}",
    response_model=schemas.ItemResponse,
    summary="Update an item by ID",
)
def update_item(
    item_id: int,
    item_update: schemas.ItemUpdate,
    db: Session = Depends(get_db),
) -> schemas.ItemResponse:
    """Update an existing item's fields."""
    db_item = crud.update_item(db=db, item_id=item_id, item_update=item_update)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return db_item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an item by ID",
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Delete an item by its ID."""
    deleted = crud.delete_item(db=db, item_id=item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
