"""Insert sample data for the Manipal Location & Review Management System."""

from __future__ import annotations

from db import get_conn, init_db


def _bulk_insert(table: str, columns: list[str], rows: list[dict]) -> None:
    col_list = ", ".join(columns)
    val_list = ", ".join([f":{c}" for c in columns])
    sql = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({val_list})"

    conn = get_conn()
    try:
        for row in rows:
            conn.execute(sql, row)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_sample_data() -> None:
    init_db()

    categories = [
        {"category_id": 1, "category_name": "Academic"},
        {"category_id": 2, "category_name": "Cafe"},
        {"category_id": 3, "category_name": "Hostel"},
        {"category_id": 4, "category_name": "Sports"},
        {"category_id": 5, "category_name": "Medical"},
        {"category_id": 6, "category_name": "Food Court"},
    ]

    users = [
        {"user_id": 1, "name": "Aarav Shetty",  "email": "aarav@mitmanipal.edu"},
        {"user_id": 2, "name": "Diya Rao",       "email": "diya@mitmanipal.edu"},
        {"user_id": 3, "name": "Rohan Nair",     "email": "rohan@mitmanipal.edu"},
        {"user_id": 4, "name": "Maya Pai",       "email": "maya@mitmanipal.edu"},
        {"user_id": 5, "name": "Nikhil Jain",    "email": "nikhil@mitmanipal.edu"},
        {"user_id": 6, "name": "Sana Khan",      "email": "sana@mitmanipal.edu"},
        {"user_id": 7, "name": "Kiran Bhat",     "email": "kiran@mitmanipal.edu"},
        {"user_id": 8, "name": "Isha Menon",     "email": "isha@mitmanipal.edu"},
    ]

    locations = [
        {"location_id": 1,  "name": "MIT Academic Block 5",    "category_id": 1, "address": "MIT Campus Road, Manipal",       "description": "Main lecture halls and faculty rooms.",              "latitude": 13.3526, "longitude": 74.7928},
        {"location_id": 2,  "name": "MIT Central Library",     "category_id": 1, "address": "MIT Campus Road, Manipal",       "description": "Silent study area with digital resources.",          "latitude": 13.3523, "longitude": 74.7936},
        {"location_id": 3,  "name": "Student Plaza Food Court","category_id": 6, "address": "Student Plaza, Manipal",         "description": "Popular food court with multiple counters.",         "latitude": 13.3515, "longitude": 74.7921},
        {"location_id": 4,  "name": "NLH Hostel",              "category_id": 3, "address": "Near MIT Main Gate, Manipal",   "description": "Boys hostel with mess and common rooms.",            "latitude": 13.3494, "longitude": 74.7932},
        {"location_id": 5,  "name": "KMC Greens Playground",   "category_id": 4, "address": "KMC Greens, Manipal",           "description": "Open ground used for football and events.",          "latitude": 13.3488, "longitude": 74.7897},
        {"location_id": 6,  "name": "Dr. TMA Pai Hospital",    "category_id": 5, "address": "Tiger Circle Road, Manipal",    "description": "Major teaching hospital and emergency center.",      "latitude": 13.3467, "longitude": 74.7929},
        {"location_id": 7,  "name": "Cafe Coffee Day Manipal", "category_id": 2, "address": "End Point Road, Manipal",       "description": "Casual cafe for snacks and coffee.",                 "latitude": 13.3459, "longitude": 74.7869},
        {"location_id": 8,  "name": "Marena Sports Complex",   "category_id": 4, "address": "Inside MAHE Campus, Manipal",  "description": "Indoor stadium, gym and swimming pool.",             "latitude": 13.3537, "longitude": 74.7883},
        {"location_id": 9,  "name": "FC1 Food Court",          "category_id": 6, "address": "Near MIT Hostels, Manipal",    "description": "Affordable food options for students.",              "latitude": 13.3501, "longitude": 74.7941},
        {"location_id": 10, "name": "MIT Innovation Center",   "category_id": 1, "address": "Academic Zone, MIT Manipal",   "description": "Startup and project incubation space.",             "latitude": 13.3531, "longitude": 74.7914},
    ]

    reviews = [
        {"review_id": 1,  "user_id": 1, "location_id": 1,  "rating": 5, "comment": "Great classrooms.",           "date": "2026-01-12"},
        {"review_id": 2,  "user_id": 2, "location_id": 2,  "rating": 4, "comment": "Very quiet and clean.",       "date": "2026-01-15"},
        {"review_id": 3,  "user_id": 3, "location_id": 3,  "rating": 4, "comment": "Good variety of food.",       "date": "2026-01-18"},
        {"review_id": 4,  "user_id": 4, "location_id": 4,  "rating": 3, "comment": "Hostel is okay.",             "date": "2026-01-20"},
        {"review_id": 5,  "user_id": 5, "location_id": 8,  "rating": 5, "comment": "Excellent sports facilities.","date": "2026-01-22"},
        {"review_id": 6,  "user_id": 6, "location_id": 6,  "rating": 4, "comment": "Helpful staff.",              "date": "2026-01-23"},
        {"review_id": 7,  "user_id": 7, "location_id": 7,  "rating": 4, "comment": "Nice vibe.",                  "date": "2026-01-24"},
        {"review_id": 8,  "user_id": 8, "location_id": 9,  "rating": 3, "comment": "Budget friendly.",            "date": "2026-01-24"},
        {"review_id": 9,  "user_id": 1, "location_id": 8,  "rating": 5, "comment": "Love the gym.",               "date": "2026-01-25"},
        {"review_id": 10, "user_id": 2, "location_id": 3,  "rating": 4, "comment": "Fast service.",               "date": "2026-01-26"},
        {"review_id": 11, "user_id": 3, "location_id": 10, "rating": 5, "comment": "Great for projects.",         "date": "2026-01-27"},
        {"review_id": 12, "user_id": 4, "location_id": 1,  "rating": 4, "comment": "Good facilities.",            "date": "2026-01-28"},
    ]

    images = [
        {"image_id": 1, "location_id": 1,  "image_url": "https://example.com/mit_block5.jpg"},
        {"image_id": 2, "location_id": 2,  "image_url": "https://example.com/mit_library.jpg"},
        {"image_id": 3, "location_id": 3,  "image_url": "https://example.com/student_plaza.jpg"},
        {"image_id": 4, "location_id": 4,  "image_url": "https://example.com/nlh_hostel.jpg"},
        {"image_id": 5, "location_id": 6,  "image_url": "https://example.com/tma_pai_hospital.jpg"},
        {"image_id": 6, "location_id": 7,  "image_url": "https://example.com/ccd_manipal.jpg"},
        {"image_id": 7, "location_id": 8,  "image_url": "https://example.com/marena.jpg"},
        {"image_id": 8, "location_id": 10, "image_url": "https://example.com/innovation_center.jpg"},
    ]

    favorites = [
        {"user_id": 1, "location_id": 8},
        {"user_id": 1, "location_id": 3},
        {"user_id": 2, "location_id": 2},
        {"user_id": 2, "location_id": 3},
        {"user_id": 3, "location_id": 1},
        {"user_id": 4, "location_id": 7},
        {"user_id": 5, "location_id": 8},
        {"user_id": 6, "location_id": 6},
        {"user_id": 7, "location_id": 9},
        {"user_id": 8, "location_id": 10},
    ]

    _bulk_insert("Categories", ["category_id", "category_name"], categories)
    _bulk_insert("Users",      ["user_id", "name", "email"],     users)
    _bulk_insert(
        "Locations",
        ["location_id", "name", "category_id", "address", "description", "latitude", "longitude"],
        locations,
    )
    _bulk_insert("Reviews",   ["review_id", "user_id", "location_id", "rating", "comment", "date"], reviews)
    _bulk_insert("Images",    ["image_id", "location_id", "image_url"],                              images)
    _bulk_insert("Favorites", ["user_id", "location_id"],                                            favorites)


if __name__ == "__main__":
    insert_sample_data()
    print("Sample data inserted successfully.")
