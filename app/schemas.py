from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ItemBase(BaseModel):
    """Base schema with common attributes."""

    name: str = Field(..., min_length=1, description="Name of the item (required, non-empty)")
    description: Optional[str] = Field(default=None, description="Optional description of the item")
    price: float = Field(..., ge=0.0, description="Price of the item (required, non-negative)")


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(ItemBase):
    """Schema for updating an existing item's fields."""

    pass


class ItemResponse(ItemBase):
    """Schema for returning an item with its system-assigned id."""

    id: int

    model_config = ConfigDict(from_attributes=True)
