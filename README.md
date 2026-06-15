# Manipal Location & Review Management System

Map-first Streamlit application for managing Manipal locations, reviews, and favorites with advanced SQL-focused analytics. The project features a strict SQLite architecture heavily demonstrating complex standard DBMS principles natively.

## Tech Stack
- **Frontend/UI:** Python + Streamlit, Folium maps (`streamlit-folium`)
- **Backend/DB:** SQLite via SQLAlchemy Core (strict pure SQLite focus)
- **Data Handling:** Pandas DataFrames

## File Structure
- `db.py` -> Database connection, schema, `ON DELETE CASCADE` constraints, triggers, and views.
- `queries.py` -> Full CRUD operations (Insert, Update, Delete), authentication, image hooks, and advanced DBMS analytics queries.
- `sample_data.py` -> Base data seeders providing a realistic spread of Manipal locations.
- `app.py` -> The interactive Streamlit dashboard mapping locations, UI CRUD, Image Uploads, and Advanced SQL features.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Features Deep Dive

### 🗺️ Core Mapping UI
- **Interactive Map:** Pan and explore location markers in Manipal.
- **Location Detail Pane:** Display descriptions, metrics, and an inline layout for reviews.
- **Image Upload:** Upload `.jpg` or `.png` files securely attached to locations (stored locally spanning an interactive gallery view).
- **Authentication System:** Integrated registration & hashing enabling secure actions.

### 🔄 Comprehensive CRUD
- **Create:** Add categories, locations, and append reviews.
- **Read:** Intelligent views exposing metadata.
- **Update:** Users can dynamically manage their own review text/ratings natively.
- **Delete:** Built with robust cascading relations; gracefully purging a location seamlessly drops dependent reviews and images.

### 🧠 Advanced Database Concepts
The database operations specifically simulate strict lab-level DBMS concepts:

- **Set Operations (`UNION`, `EXCEPT`, `INTERSECT`)**
   - e.g. "Noteworthy Locations" leveraging `UNION`.
   - "Top-Rated but Not Popular" computed using `EXCEPT` clauses.

- **Advanced Subqueries**
   - Implementing logic loops representing `EXISTS`, `NOT EXISTS`, `ALL`, and `ANY`.
   - Correlated scalar subqueries pitting location rating vs aggregate category trends.
   - Relational division implementations to isolate universally-focused reviewers.

- **Explicit Transaction Logic (`SAVEPOINT` / `ROLLBACK`)**
   - Contains a simulated update block isolating rollback failures when invalid ratings are supplied midway through an operation. Let's explicit transactional states handle fallback.

- **Cursor Mechanisms**
   - Active Python-level explicit database queries fetching multiple rows iteratively in memory to flag locations sequentially (mirroring explicit PL/SQL execution). 
 
- **Automated Triggers (`AFTER UPDATE`)**
   - Maintains an extensive audit hook inside the `ReviewLogs` table. It listens for `UPDATE` events specifically upon rating modifiers logging `old_rating` contrasting `new_rating` asynchronously. 

## Load Sample Data
Inside the map window interface, simply click **Load Sample Data** located centrally on the navigator to seed the environment instantly.
