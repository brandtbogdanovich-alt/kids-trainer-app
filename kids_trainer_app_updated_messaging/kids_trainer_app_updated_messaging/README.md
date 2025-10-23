# Kids Trainer Marketplace Prototype

This repository contains a simple prototype for a marketplace that
connects parents with sports trainers for children. It’s inspired by
platforms like Craigslist and Thumbtack, but focused specifically on
vetting and booking kids’ trainers.

## Features

- **Browse trainers:** View a list of trainers with their sport,
  credentials, biography, contact information and price.
- **Register as a trainer:** Trainers can create their own profile by
  filling out a form with their details and price per session.
- **Book a trainer:** Parents can request a session with a trainer by
  providing their name, contact information, preferred date and time,
  and optional notes. Bookings are stored in the database.
- **SQLite database:** All data is stored in a simple SQLite database
  (`db.sqlite3`) that is created automatically the first time the app
  runs.

## Landing page and images

The home page has been redesigned to more closely match the look and
feel of established care marketplaces like Care.com and UrbanSitter.
It now includes a full‑width hero banner, a grid of popular sports
categories and a features section.  The images used in the hero and
category cards live in `static/images`.  By default these files are
placeholders generated for demonstration purposes; they are not real
photographs.  To personalize the site, replace `hero.jpg`,
`soccer.jpg`, `basketball.jpg`, `swimming.jpg` and `tennis.jpg` with
your own high‑quality photos (e.g. from a royalty‑free service like
Pexels or Unsplash).  Make sure to keep the same file names or update
the `index.html` template accordingly.

## Getting Started

1. **Install dependencies**

   It’s recommended to create a virtual environment, but not
   strictly necessary. Install the required Python packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**

   Start the FastAPI application with uvicorn:

   ```bash
   uvicorn main:app --reload
   ```

   The app will be available at `http://localhost:8000/`. When you
   first run it, a database file (`db.sqlite3`) will be created in the
   project directory.

3. **Explore**

   - Navigate to the home page to see a welcome message and quick
     links.
   - Click **Browse Trainers** to view all registered trainers. If
     there are none, try registering one.
   - Click **Register as Trainer** to create a trainer profile.
   - From the trainers list, click **Book** to request a session with
     a particular trainer. Provide your details and preferred date/time.

## Notes

- This is a prototype and does **not** include authentication,
  background checks, payments or notifications. These would be
  essential for a production system.
- Data is stored unencrypted in a local SQLite database. Do not use
  this prototype in production without proper security measures.

## License

This project is provided for educational and prototyping purposes and
does not include any warranty. Feel free to adapt it for your own
projects.