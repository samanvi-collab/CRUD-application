import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is on sys.path so 'app' is importable regardless of runner
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, get_db
from app import models
from app.main import app

# Dedicated in-memory SQLite database for testing (isolated from app.db)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create fresh database tables for each test and drop them afterward."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient fixture with get_db overridden to use the in-memory test database."""
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient):
    """Test health check returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_item_success(client: TestClient):
    """Test creating a valid item successfully."""
    payload = {
        "name": "Mechanical Keyboard",
        "description": "RGB backlight, blue switches",
        "price": 89.99,
    }
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["price"] == payload["price"]


def test_create_item_without_description(client: TestClient):
    """Test creating an item where description is optional and omitted."""
    payload = {
        "name": "Wireless Mouse",
        "price": 29.50,
    }
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["description"] is None
    assert data["price"] == payload["price"]


def test_get_all_items_empty(client: TestClient):
    """Test retrieving all items when the database is empty."""
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_items(client: TestClient):
    """Test retrieving all items returns the full list."""
    client.post("/items", json={"name": "Item 1", "price": 10.0})
    client.post("/items", json={"name": "Item 2", "description": "Desc 2", "price": 20.0})

    response = client.get("/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert items[0]["name"] == "Item 1"
    assert items[1]["name"] == "Item 2"


def test_get_item_by_id(client: TestClient):
    """Test retrieving an existing item by its ID."""
    create_resp = client.post(
        "/items",
        json={"name": "Monitor", "description": "4K Ultra HD", "price": 350.0},
    )
    item_id = create_resp.json()["id"]

    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["name"] == "Monitor"
    assert data["description"] == "4K Ultra HD"
    assert data["price"] == 350.0


def test_get_nonexistent_item_returns_404(client: TestClient):
    """Test retrieving an item with a non-existent ID returns 404."""
    response = client.get("/items/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_update_item_success(client: TestClient):
    """Test updating an existing item's fields successfully."""
    create_resp = client.post(
        "/items",
        json={"name": "Initial Name", "description": "Initial Desc", "price": 50.0},
    )
    item_id = create_resp.json()["id"]

    update_payload = {
        "name": "Updated Name",
        "description": "Updated Desc",
        "price": 65.50,
    }
    update_resp = client.put(f"/items/{item_id}", json=update_payload)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["id"] == item_id
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated Desc"
    assert data["price"] == 65.50

    # Verify retrieval returns updated data
    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Updated Name"
    assert get_resp.json()["price"] == 65.50


def test_update_nonexistent_item_returns_404(client: TestClient):
    """Test updating a non-existent item returns 404."""
    payload = {"name": "Ghost Item", "price": 10.0}
    response = client.put("/items/99999", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_delete_item_success(client: TestClient):
    """Test deleting an existing item returns 204."""
    create_resp = client.post("/items", json={"name": "Item to Delete", "price": 15.0})
    item_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/items/{item_id}")
    assert delete_resp.status_code == 204
    assert delete_resp.text == ""

    # Verify item is deleted
    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_item_returns_404(client: TestClient):
    """Test deleting a non-existent item returns 404."""
    response = client.delete("/items/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_deleted_item_cannot_be_retrieved_in_list(client: TestClient):
    """Test that deleted items do not appear in the all-items list."""
    create_resp = client.post("/items", json={"name": "Item A", "price": 10.0})
    item_a_id = create_resp.json()["id"]
    client.post("/items", json={"name": "Item B", "price": 20.0})

    # Delete Item A
    client.delete(f"/items/{item_a_id}")

    # Retrieve all items
    list_resp = client.get("/items")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["name"] == "Item B"


def test_reject_negative_price_on_create(client: TestClient):
    """Test that creating an item with negative price returns 422."""
    payload = {"name": "Invalid Price Item", "price": -10.0}
    response = client.post("/items", json=payload)
    assert response.status_code == 422


def test_reject_negative_price_on_update(client: TestClient):
    """Test that updating an item with negative price returns 422."""
    create_resp = client.post("/items", json={"name": "Valid Item", "price": 10.0})
    item_id = create_resp.json()["id"]

    response = client.put(f"/items/{item_id}", json={"name": "Valid Item", "price": -5.0})
    assert response.status_code == 422


def test_reject_missing_required_name(client: TestClient):
    """Test that creating an item missing the required name field returns 422."""
    payload = {"price": 10.0}
    response = client.post("/items", json=payload)
    assert response.status_code == 422


def test_reject_missing_required_price(client: TestClient):
    """Test that creating an item missing the required price field returns 422."""
    payload = {"name": "No Price Item"}
    response = client.post("/items", json=payload)
    assert response.status_code == 422


def test_reject_empty_name(client: TestClient):
    """Test that creating an item with an empty string name returns 422."""
    payload = {"name": "", "price": 10.0}
    response = client.post("/items", json=payload)
    assert response.status_code == 422


def test_confirm_data_persistence_in_test_db(client: TestClient, db_session: Session):
    """Test that created item actually persists in the database session."""
    payload = {
        "name": "Persistent Item",
        "description": "Stored in DB",
        "price": 123.45,
    }
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    item_id = response.json()["id"]

    # Direct query against the test database session
    db_item = db_session.query(models.Item).filter(models.Item.id == item_id).first()
    assert db_item is not None
    assert db_item.name == "Persistent Item"
    assert db_item.description == "Stored in DB"
    assert db_item.price == 123.45
