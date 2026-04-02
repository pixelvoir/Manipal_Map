# Manipal Location & Review Management System

Simple DBMS mini project aiming for easy user-based viewing and management of various locations in Manipal, and demonstrate the usage of SQL queries.

## Tech Stack
- Python + Streamlit (frontend)
- SQLAlchemy + SQLite (default) or PostgreSQL
- Pandas
- Folium map

## File Structure
- `db.py` -> database connection, schema, constraints, trigger, view
- `queries.py` -> all SQL queries and DB operations
- `sample_data.py` -> sample inserts (Manipal locations)
- `app.py` -> Streamlit UI

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
In the Streamlit sidebar, click **Load Sample Data**.

## Concepts Demonstrated
- Basic queries: SELECT, INSERT, UPDATE, DELETE
- JOIN
- GROUP BY + aggregate
- HAVING
- Subqueries
- Set operations (UNION, INTERSECT)
- View (`location_avg_rating`)
- ORDER BY
- CTE (`WITH` clause)
- Advanced:
  - Procedure/function-style review insertion (PostgreSQL SQL function + SQLite equivalent)
  - Trigger for review insert logging
  - Cursor-style row iteration for stats
