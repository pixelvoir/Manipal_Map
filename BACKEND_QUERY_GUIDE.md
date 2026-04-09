# Manipal Map Backend Guide

## 1. Database Stack
- Database engine: SQLite
- Python driver: built-in `sqlite3`
- Query style: raw SQL strings with parameters (no ORM)
- Connection setup: `db.py` -> `get_conn()`
- Query log: `query.log` is reset once at session start

## 2. Queries Currently Implemented in the UI

### INSERT Queries
- `register_user`: Auth page -> Register tab -> Create account submission.
- `add_category`: Map page -> Contribution studio -> Add new category.
- `add_location`: Map page -> Contribution studio -> Add new location.
- `add_favorite`: Location spotlight -> Overview tab -> Save favourite.
- `add_review`: Location spotlight -> Reviews tab -> Write a review form.
- `add_image`: Location spotlight -> Gallery tab -> Save uploaded image.

### UPDATE Queries
- `update_location`: Location spotlight -> Overview tab -> Manage location -> Save changes.
- `update_review`: Location spotlight -> Reviews tab -> Edit review.

### DELETE Queries
- `delete_location`: Location spotlight -> Overview tab -> Manage location -> Delete location.
- `remove_favorite`: Location spotlight -> Overview tab -> Remove favourite.
- `delete_review`: Location spotlight -> Reviews tab -> Delete review.

### SELECT Lookup and Filter Queries
- `get_user_by_email`: Auth page -> Sign in tab -> credential lookup.
- `get_categories`: Sidebar category filter and category selection dropdowns in add/edit location forms.
- `get_favorite_location_ids`: Sidebar "Show only my favourites" and spotlight favourite toggle state.
- `search_locations_by_category`: Map page -> category filter result set.
- `get_images_for_location`: Location spotlight -> Gallery tab image feed.
- `get_reviews_for_location`: Location spotlight -> Reviews tab review feed.

### JOIN and Detail Queries
- `get_locations`: Main map dataset (default listing with joined category metadata).
- `get_location_details`: Location spotlight detail panel after marker selection.
- `get_locations_added_by_user`: Profile page -> Locations added section.
- `get_reviews_by_user`: Profile page -> Reviews written section.
- `get_images_uploaded_by_user`: Profile page -> Images uploaded section.

### Aggregate / CTE / Set-Operation Queries
- `top_rated_locations`: Sidebar quick preset -> Highly rated.
- `most_reviewed_locations`: Sidebar quick preset -> Highly reviewed.
- `most_favorited_locations`: Sidebar quick preset -> Most favourited.
- `locations_above_all_in_category`: Sidebar quick preset -> Category leaders.
- `common_favorites_and_reviewed`: Sidebar quick preset -> Saved and reviewed.
- `get_user_contribution_summary`: Profile hero chips and profile metric cards.
- `users_with_most_reviews`: Profile review-rank chip.
- `get_location_spotlight_insights`: Location spotlight insight cards.

## 3. Queries Never Called Anywhere in the Project
- `users_with_five_star_review` (not wired to map/profile/auth/spotlight flow)
- `users_who_reviewed_all_categories` (not wired to map/profile/auth/spotlight flow)
- `best_per_category_correlated` (not wired to map/profile/auth/spotlight flow)
- `locations_popular_but_underrated` (removed from presets)
- `recently_reviewed_locations` (implemented but not currently wired to any visible page)
- `locations_union_high_activity` (used only in non-routed analytics helper)
- `active_but_not_top_rated` (used only in non-routed analytics helper)
- `average_rating_per_location` (used only in non-routed analytics helper)
- `get_category_activity_summary` (used only in non-routed analytics helper)
- `location_rating_bands` (used only in non-routed analytics helper)
- `get_review_logs` (used only in non-routed analytics helper)
- `get_deleted_location_audit` (used only in non-routed analytics helper)
- `flag_low_rated_locations` (used only in non-routed analytics helper)
- `parameterized_category_cursor` (used only in non-routed analytics helper)
- `demo_savepoint_transaction` (used only in non-routed analytics helper)
- `archive_delete_location_transaction` (used only in non-routed analytics helper)

## 4. Queries Not Implemented in UI (Backend-Only)

### Aggregation and Summary
- `average_rating_per_location`
- `get_category_activity_summary`
- `location_rating_bands`

### Trigger / Audit / Runtime Demo Data
- `trg_validate_review_insert` (trigger in `db.py`, backend validation)
- `trg_validate_review_update` (trigger in `db.py`, backend validation)
- `trg_log_review_insert` (trigger in `db.py`, backend audit)
- `trg_log_review_update` (trigger in `db.py`, backend audit)
- `trg_archive_location_delete` (trigger in `db.py`, backend audit)
- `db.reset_query_log()` (backend session log reset)

### Advanced Set/Subquery Analytics
- (none currently kept outside UI presets)

## 5. Triggers and Automation
Defined in `db.py` (`init_db()`):
- `trg_validate_review_insert`: blocks empty review comments on insert.
- `trg_validate_review_update`: blocks empty review comments on update.
- `trg_log_review_insert`: writes insert events into `ReviewLogs`.
- `trg_log_review_update`: writes rating updates into `ReviewLogs`.
- `trg_archive_location_delete`: archives counts in `DeletedLocationAudit` before delete.
- `db.reset_query_log()`: clears SQL trace log at session start.

## 6. Cursors Explained in Basic Terms
A cursor is the object SQLite gives back after running a query. Think of it as:
- the query result handle (it knows the columns), and
- an iterator over rows (you can pull rows one-by-one or all at once).

In this project:
- Simple pattern: run query -> fetch rows -> convert rows into a DataFrame.
- Cursor-style pattern: read rows one at a time and apply logic per row.
  - `flag_low_rated_locations(threshold)` does this by scanning averages row-by-row, then upserting status.
- Parameterized cursor analogue:
  - `parameterized_category_cursor(category_id, threshold)` runs the same query structure with user inputs.

## 7. Transaction Control Implementations
- Savepoint demos:
  - `demo_savepoint_transaction`
  - `archive_delete_location_transaction`
- These explicitly use `BEGIN`, `SAVEPOINT`, `ROLLBACK TO SAVEPOINT`, `RELEASE SAVEPOINT`, `COMMIT`.

---

# Plan: Next Query Integration (Without Table Clutter)

## Goal
Keep the app map-first while using advanced SQL only where it improves user decisions.

## Phase A (Near-term)
- Surface one additional profile insight from backend-only queries:
  - Add optional "five-star reviewer" badge using `users_with_five_star_review`.
- Add one spotlight micro-insight for context:
  - category average benchmark using `best_per_category_correlated` logic in compact form.

## Phase B (Optional Analytics Surface)
- Build a separate analytics area (not on the map page).
- Use cards/charts first and raw tables only on explicit expand.
- Candidate queries for this page:
  - `average_rating_per_location`
  - `get_category_activity_summary`
  - `location_rating_bands`
  - `active_but_not_top_rated`

## Phase C (Dev and Ops Visibility)
- Keep SQL trace backend-only in `query.log`.
- Add optional developer diagnostics toggle to inspect runtime-only outputs.

## UX Guardrails
- Default user UI should not dump raw query tables.
- Every shown insight must answer a clear user question.
- Map interaction and location spotlight stay primary.
