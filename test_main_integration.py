import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_borrow_book():
    # Create a user
    user_response = client.post("/users/", params={"username": "borrower", "fullname": "Book Borrower"})
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]

    # Create a book
    book_response = client.post("/books/", params={"title": "Test Book", "firstauthor": "Test Author", "isbn": "1234567890"})
    assert book_response.status_code == 200
    book_id = book_response.json()["id"]

    # Borrow the book
    borrow_response = client.post("/borrowlist/", params={"user_id": user_id, "book_id": book_id})
    assert borrow_response.status_code == 200
    borrow_data = borrow_response.json()
    assert borrow_data["user_id"] == user_id
    assert borrow_data["book_id"] == book_id

def test_view_user_borrow_list():
    # Create a user
    user_response = client.post("/users/", params={"username": "viewer", "fullname": "List Viewer"})
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]

    # Create a book
    book_response = client.post("/books/", params={"title": "Another Test Book", "firstauthor": "Another Author", "isbn": "0987654321"})
    assert book_response.status_code == 200
    book_id = book_response.json()["id"]

    # Borrow the book
    borrow_response = client.post("/borrowlist/", params={"user_id": user_id, "book_id": book_id})
    assert borrow_response.status_code == 200

    # View the user's borrow list
    get_response = client.get(f"/borrowlist/{user_id}")
    assert get_response.status_code == 200
    borrow_list = get_response.json()
    assert isinstance(borrow_list, list)
    assert len(borrow_list) > 0
    assert borrow_list[0]["user_id"] == user_id
    assert borrow_list[0]["book_id"] == book_id