"""
FastAPI web application implementing a prototype marketplace for parents
to connect with children’s sports trainers. The app uses a lightweight
SQLite database (shipped in the repository) to store trainer profiles,
parent information and booking requests. It exposes a handful of
pages for browsing trainers, registering as a trainer and requesting
bookings. The front‑end is rendered via Jinja2 templates and uses
minimal styling defined under static/style.css. To run the app you
need to install the dependencies listed in requirements.txt and start
the uvicorn server:

    pip install -r requirements.txt
    uvicorn main:app --reload

The app will create the database file (db.sqlite3) on first start.
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import pathlib
import urllib.parse

# Determine the base directory of this file. Using pathlib ensures the
# application can locate its templates, static assets and database
# regardless of the working directory from which it is run.
BASE_DIR = pathlib.Path(__file__).resolve().parent

# instantiate FastAPI
app = FastAPI(title="Kids Trainer Marketplace")

# mount static assets (CSS, images, etc.)
static_path = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# set up template rendering
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# location of the SQLite database. It lives in the project directory
DB_PATH = str(BASE_DIR / "db.sqlite3")


def get_db() -> sqlite3.Connection:
    """Return a SQLite connection with row factory enabled.

    Each request should obtain its own connection so concurrent
    requests don’t share cursors. Remember to close the connection
    after you’re done.
    """
    conn = sqlite3.connect(DB_PATH)
    # enable dictionary‑like access on rows
    conn.row_factory = sqlite3.Row
    return conn


def create_tables() -> None:
    """Create database tables if they don’t exist yet.

    We keep our schema deliberately simple: trainers and parents
    hold contact information, while bookings links parents to
    trainers along with a preferred date/time and optional notes.
    """
    conn = get_db()
    cursor = conn.cursor()
    # Table for trainer profiles
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trainers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            sport       TEXT NOT NULL,
            credentials TEXT NOT NULL,
            bio         TEXT NOT NULL,
            price       REAL NOT NULL,
            email       TEXT NOT NULL,
            phone       TEXT NOT NULL
        )
        """
    )
    # Table for parents (we store unique email/phone combinations)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS parents (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            UNIQUE(email, phone)
        )
        """
    )
    # Table for booking requests
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id  INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
            date       TEXT NOT NULL,
            time       TEXT NOT NULL,
            notes      TEXT,
            FOREIGN KEY(parent_id) REFERENCES parents(id),
            FOREIGN KEY(trainer_id) REFERENCES trainers(id)
        )
        """
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def on_startup() -> None:
    """Initialize the database when the server starts."""
    create_tables()


@app.get("/")
def read_home(request: Request):
    """Render the landing page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Home"},
    )


@app.get("/trainers")
def list_trainers(request: Request):
    """List all registered trainers."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trainers")
    trainers = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse(
        "trainer_list.html",
        {"request": request, "title": "Trainers", "trainers": trainers},
    )


@app.get("/register_trainer")
def register_trainer_form(request: Request):
    """Display the trainer registration form."""
    return templates.TemplateResponse(
        "trainer_register.html",
        {"request": request, "title": "Register Trainer"},
    )


@app.post("/register_trainer")
async def register_trainer(request: Request):
    """Handle trainer registration form submission.

    Parse URL‑encoded form data manually to avoid relying on optional
    dependencies (python‑multipart). Store the submitted profile in
    the database and redirect the user back to the trainers list.
    """
    body_bytes = await request.body()
    form_data = urllib.parse.parse_qs(body_bytes.decode())
    # Extract fields with default empty strings if missing
    name = form_data.get("name", [""])[0]
    sport = form_data.get("sport", [""])[0]
    credentials = form_data.get("credentials", [""])[0]
    bio = form_data.get("bio", [""])[0]
    price = form_data.get("price", ["0"])[0]
    email = form_data.get("email", [""])[0]
    phone = form_data.get("phone", [""])[0]
    # Convert price to float if possible
    try:
        price_val = float(price)
    except ValueError:
        price_val = 0.0
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO trainers (name, sport, credentials, bio, price, email, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, sport, credentials, bio, price_val, email, phone),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/trainers", status_code=303)


@app.get("/book/{trainer_id}")
def book_trainer_form(trainer_id: int, request: Request):
    """Display a booking form for a specific trainer."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trainers WHERE id = ?", (trainer_id,))
    trainer = cursor.fetchone()
    conn.close()
    if trainer is None:
        # if trainer does not exist, redirect to list
        return RedirectResponse("/trainers", status_code=303)
    return templates.TemplateResponse(
        "booking.html",
        {"request": request, "title": f"Book {trainer['name']}", "trainer": trainer},
    )


@app.post("/book/{trainer_id}")
async def book_trainer(trainer_id: int, request: Request):
    """Process a booking request.

    Parse URL‑encoded form data manually to avoid optional dependencies.
    Look up (or insert) the parent record then create a new booking.
    Finally redirect to a thank‑you page.
    """
    body_bytes = await request.body()
    form_data = urllib.parse.parse_qs(body_bytes.decode())
    parent_name = form_data.get("parent_name", [""])[0]
    parent_email = form_data.get("parent_email", [""])[0]
    parent_phone = form_data.get("parent_phone", [""])[0]
    date = form_data.get("date", [""])[0]
    time_val = form_data.get("time", [""])[0]
    notes = form_data.get("notes", [""])[0]
    conn = get_db()
    cursor = conn.cursor()
    # Attempt to find existing parent by email and phone
    cursor.execute(
        "SELECT id FROM parents WHERE email = ? AND phone = ?",
        (parent_email, parent_phone),
    )
    row = cursor.fetchone()
    if row:
        parent_id = row["id"]
    else:
        # Insert new parent
        cursor.execute(
            "INSERT INTO parents (name, email, phone) VALUES (?, ?, ?)",
            (parent_name, parent_email, parent_phone),
        )
        parent_id = cursor.lastrowid
    # Insert the booking
    cursor.execute(
        "INSERT INTO bookings (parent_id, trainer_id, date, time, notes) VALUES (?, ?, ?, ?, ?)",
        (parent_id, trainer_id, date, time_val, notes),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/thank_you", status_code=303)


@app.get("/thank_you")
def thank_you(request: Request):
    """Render a simple thank‑you page after a booking."""
    return templates.TemplateResponse(
        "thank_you.html",
        {"request": request, "title": "Thank You"},
    )