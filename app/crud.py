from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas


def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    """Retrieve a single item by ID."""
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[models.Item]:
    """Retrieve a list of items."""
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    """Create a new item in the database."""
    db_item = models.Item(
        name=item.name,
        description=item.description,
        price=item.price,
    )
    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception:
        db.rollback()
        raise


def update_item(
    db: Session, item_id: int, item_update: schemas.ItemUpdate
) -> Optional[models.Item]:
    """Update an existing item's fields."""
    db_item = get_item(db, item_id)
    if db_item is None:
        return None

    db_item.name = item_update.name
    db_item.description = item_update.description
    db_item.price = item_update.price
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception:
        db.rollback()
        raise


def delete_item(db: Session, item_id: int) -> bool:
    """Delete an item from the database. Returns True if deleted, False if not found."""
    db_item = get_item(db, item_id)
    if db_item is None:
        return False

    try:
        db.delete(db_item)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
