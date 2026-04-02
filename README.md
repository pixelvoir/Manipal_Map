# Manipal Location & Review Management System

Map-first Streamlit application for managing Manipal locations, reviews, and favorites with SQL-focused analytics.

## Tech Stack
- Python + Streamlit (frontend)
- SQLAlchemy + SQLite (default) or PostgreSQL
- Pandas
- Folium map

## File Structure
- `db.py` -> database connection, schema, constraints, trigger, view
- `queries.py` -> CRUD, auth, map details, analytics queries
- `sample_data.py` -> sample inserts (Manipal locations)
- `app.py` -> map-first Streamlit UI

## Setup
1. Create and activate a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Database Choice
- Default: SQLite file `manipal_map.db`.
- To use PostgreSQL, set environment variable:
  ```bash
  DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/manipal_map
  ```

## Load Sample Data
Click **Load Sample Data** on the top control row.

## Main UI Flow
- Main map shows all locations as markers
- Click marker to open location details panel below map
- Details panel supports review submission and favorites
- Filter map by category
- Add category and add location using control buttons and expanders
- Login/logout is available at top right

## Authentication
- Register and login are built into the app
- Passwords are stored as hashed values in the `Users.password_hash` column
- Protected actions: add location, add review, add to favorites

## SQL Analytics Page (Map Database)
- Average rating per location
- Top-rated locations (uses HAVING)
- Most reviewed locations (uses CTE)
- Users with most reviews (JOIN + CTE)

## Database Features
- Constraints: PK, FK, UNIQUE, CHECK
- Trigger: logs review inserts in `ReviewLogs`
- View: `location_avg_rating`
- Stored function style review insertion: PostgreSQL function + SQLite equivalent transaction logic
