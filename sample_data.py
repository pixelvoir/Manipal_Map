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
        {"category_id": 2, "category_name": "Restaurant"},
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
        {"user_id": 9, "name": "Vivek Kulkarni", "email": "vivek@mitmanipal.edu"},
        {"user_id": 10, "name": "Riya S",         "email": "riya@mitmanipal.edu"},
        {"user_id": 11, "name": "Aditya Rao",     "email": "aditya@mitmanipal.edu"},
        {"user_id": 12, "name": "Nandini Hegde",  "email": "nandini@mitmanipal.edu"},
        {"user_id": 13, "name": "Taran Kapoor",   "email": "taran@mitmanipal.edu"},
        {"user_id": 14, "name": "Megha Pai",      "email": "megha@mitmanipal.edu"},
        {"user_id": 15, "name": "Kabir Iyer",     "email": "kabir@mitmanipal.edu"},
        {"user_id": 16, "name": "Suhani Das",     "email": "suhani@mitmanipal.edu"},
        {"user_id": 17, "name": "Joel Dsouza",    "email": "joel@mitmanipal.edu"},
        {"user_id": 18, "name": "Ananya Pillai",  "email": "ananya@mitmanipal.edu"},
    ]

    locations = [
        {"location_id": 1,  "name": "MIT Academic Block 5",    "category_id": 1, "address": "MIT Campus Road, Manipal",       "description": "Main lecture halls and faculty rooms.",              "latitude": 13.3526, "longitude": 74.7928, "created_by": 1, "created_at": "2026-01-10 09:00:00"},
        {"location_id": 2,  "name": "MIT Central Library",     "category_id": 1, "address": "MIT Campus Road, Manipal",       "description": "Silent study area with digital resources.",          "latitude": 13.3523, "longitude": 74.7936, "created_by": 2, "created_at": "2026-01-10 09:10:00"},
        {"location_id": 3,  "name": "Student Plaza Food Court","category_id": 6, "address": "Student Plaza, Manipal",         "description": "Popular food court with multiple counters.",         "latitude": 13.3515, "longitude": 74.7921, "created_by": 3, "created_at": "2026-01-10 09:20:00"},
        {"location_id": 4,  "name": "NLH Hostel",              "category_id": 3, "address": "Near MIT Main Gate, Manipal",   "description": "Boys hostel with mess and common rooms.",            "latitude": 13.3494, "longitude": 74.7932, "created_by": 4, "created_at": "2026-01-10 09:30:00"},
        {"location_id": 5,  "name": "KMC Greens Playground",   "category_id": 4, "address": "KMC Greens, Manipal",           "description": "Open ground used for football and events.",          "latitude": 13.3488, "longitude": 74.7897, "created_by": 5, "created_at": "2026-01-10 09:40:00"},
        {"location_id": 6,  "name": "Dr. TMA Pai Hospital",    "category_id": 5, "address": "Tiger Circle Road, Manipal",    "description": "Major teaching hospital and emergency center.",      "latitude": 13.3467, "longitude": 74.7929, "created_by": 6, "created_at": "2026-01-10 09:50:00"},
        {"location_id": 7,  "name": "Cafe Coffee Day Manipal", "category_id": 2, "address": "End Point Road, Manipal",       "description": "Casual restaurant for snacks and coffee.",           "latitude": 13.3459, "longitude": 74.7869, "created_by": 7, "created_at": "2026-01-10 10:00:00"},
        {"location_id": 8,  "name": "Marena Sports Complex",   "category_id": 4, "address": "Inside MAHE Campus, Manipal",  "description": "Indoor stadium, gym and swimming pool.",             "latitude": 13.3537, "longitude": 74.7883, "created_by": 1, "created_at": "2026-01-10 10:10:00"},
        {"location_id": 9,  "name": "FC1 Food Court",          "category_id": 6, "address": "Near MIT Hostels, Manipal",    "description": "Affordable food options for students.",              "latitude": 13.3501, "longitude": 74.7941, "created_by": 2, "created_at": "2026-01-10 10:20:00"},
        {"location_id": 10, "name": "MIT Innovation Center",   "category_id": 1, "address": "Academic Zone, MIT Manipal",   "description": "Startup and project incubation space.",             "latitude": 13.3531, "longitude": 74.7914, "created_by": 3, "created_at": "2026-01-10 10:30:00"},
        {"location_id": 11, "name": "End Point Park View",     "category_id": 4, "address": "End Point Road, Manipal",       "description": "Quiet viewpoint and walking area.",                 "latitude": 13.3428, "longitude": 74.7886, "created_by": 9, "created_at": "2026-01-10 10:40:00"},
        {"location_id": 12, "name": "Tiger Circle Eatery",     "category_id": 2, "address": "Tiger Circle, Manipal",         "description": "Busy student restaurant near transit routes.",      "latitude": 13.3468, "longitude": 74.7907, "created_by": 10, "created_at": "2026-01-10 10:50:00"},
        {"location_id": 13, "name": "KMC Lecture Hall",        "category_id": 1, "address": "KMC Campus, Manipal",           "description": "Lecture hall used for medical classes.",            "latitude": 13.3451, "longitude": 74.7915, "created_by": 11, "created_at": "2026-01-10 11:00:00"},
        {"location_id": 14, "name": "Annapoorna Mess",         "category_id": 6, "address": "MIT Hostel Zone, Manipal",      "description": "Daily meals with quick student service.",           "latitude": 13.3499, "longitude": 74.7939, "created_by": 12, "created_at": "2026-01-10 11:10:00"},
        {"location_id": 15, "name": "AB2 Courtyard",           "category_id": 1, "address": "Academic Block 2, MIT",         "description": "Open courtyard popular for student meetups.",       "latitude": 13.3530, "longitude": 74.7920, "created_by": 13, "created_at": "2026-01-10 11:20:00"},
        {"location_id": 16, "name": "Madhav Kripa School Ground", "category_id": 4, "address": "Near Syndicate Circle",      "description": "Community ground for football and drills.",         "latitude": 13.3439, "longitude": 74.7868, "created_by": 14, "created_at": "2026-01-10 11:30:00"},
        {"location_id": 17, "name": "Student Convenience Store", "category_id": 2, "address": "SP Complex, Manipal",          "description": "Quick bites and essentials in one stop.",           "latitude": 13.3512, "longitude": 74.7924, "created_by": 15, "created_at": "2026-01-10 11:40:00"},
        {"location_id": 18, "name": "Kasturba Medical Canteen", "category_id": 6, "address": "KMC Hospital Wing, Manipal",   "description": "Hospital-side canteen with late hours.",            "latitude": 13.3463, "longitude": 74.7930, "created_by": 16, "created_at": "2026-01-10 11:50:00"},
        {"location_id": 19, "name": "MIT Cricket Nets",        "category_id": 4, "address": "MIT Sports Side, Manipal",      "description": "Practice nets for evening sessions.",               "latitude": 13.3521, "longitude": 74.7898, "created_by": 17, "created_at": "2026-01-10 12:00:00"},
        {"location_id": 20, "name": "Sharada Residency Block", "category_id": 3, "address": "Valencia, Manipal",             "description": "Private student stay with shared facilities.",      "latitude": 13.3478, "longitude": 74.7877, "created_by": 18, "created_at": "2026-01-10 12:10:00"},
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
        {"review_id": 13, "user_id": 9,  "location_id": 11, "rating": 5, "comment": "Best sunset point.",         "date": "2026-01-29"},
        {"review_id": 14, "user_id": 10, "location_id": 12, "rating": 4, "comment": "Good food and quick seating.", "date": "2026-01-30"},
        {"review_id": 15, "user_id": 11, "location_id": 13, "rating": 4, "comment": "Clean and well-lit hall.",   "date": "2026-01-31"},
        {"review_id": 16, "user_id": 12, "location_id": 14, "rating": 3, "comment": "Affordable but crowded.",    "date": "2026-02-01"},
        {"review_id": 17, "user_id": 13, "location_id": 15, "rating": 5, "comment": "Great open space to relax.", "date": "2026-02-02"},
        {"review_id": 18, "user_id": 14, "location_id": 16, "rating": 4, "comment": "Nice training ground.",      "date": "2026-02-03"},
        {"review_id": 19, "user_id": 15, "location_id": 17, "rating": 4, "comment": "Convenient for daily needs.", "date": "2026-02-04"},
        {"review_id": 20, "user_id": 16, "location_id": 18, "rating": 3, "comment": "Decent food options.",       "date": "2026-02-05"},
        {"review_id": 21, "user_id": 17, "location_id": 19, "rating": 5, "comment": "Good nets and pitch feel.",  "date": "2026-02-06"},
        {"review_id": 22, "user_id": 18, "location_id": 20, "rating": 4, "comment": "Comfortable stay overall.",  "date": "2026-02-07"},
        {"review_id": 23, "user_id": 1,  "location_id": 12, "rating": 3, "comment": "Can improve waiting time.",  "date": "2026-02-08"},
        {"review_id": 24, "user_id": 2,  "location_id": 14, "rating": 4, "comment": "Good value meals.",          "date": "2026-02-09"},
        {"review_id": 25, "user_id": 3,  "location_id": 11, "rating": 5, "comment": "Scenic and peaceful.",       "date": "2026-02-10"},
        {"review_id": 26, "user_id": 4,  "location_id": 16, "rating": 4, "comment": "Great for practice.",        "date": "2026-02-11"},
        {"review_id": 27, "user_id": 5,  "location_id": 19, "rating": 4, "comment": "Well maintained nets.",      "date": "2026-02-12"},
        {"review_id": 28, "user_id": 6,  "location_id": 20, "rating": 3, "comment": "Decent but can be quieter.", "date": "2026-02-13"},
        {"review_id": 29, "user_id": 7,  "location_id": 18, "rating": 4, "comment": "Good late-night option.",    "date": "2026-02-14"},
        {"review_id": 30, "user_id": 8,  "location_id": 17, "rating": 5, "comment": "Super handy location.",      "date": "2026-02-15"},
    ]

    images = [
        {"image_id": 1, "location_id": 1,  "image_url": "https://example.com/mit_block5.jpg", "uploaded_by": 1, "uploaded_at": "2026-01-11 09:00:00"},
        {"image_id": 2, "location_id": 2,  "image_url": "https://example.com/mit_library.jpg", "uploaded_by": 2, "uploaded_at": "2026-01-11 09:10:00"},
        {"image_id": 3, "location_id": 3,  "image_url": "https://example.com/student_plaza.jpg", "uploaded_by": 3, "uploaded_at": "2026-01-11 09:20:00"},
        {"image_id": 4, "location_id": 4,  "image_url": "https://example.com/nlh_hostel.jpg", "uploaded_by": 4, "uploaded_at": "2026-01-11 09:30:00"},
        {"image_id": 5, "location_id": 6,  "image_url": "https://example.com/tma_pai_hospital.jpg", "uploaded_by": 6, "uploaded_at": "2026-01-11 09:40:00"},
        {"image_id": 6, "location_id": 7,  "image_url": "https://example.com/ccd_manipal.jpg", "uploaded_by": 7, "uploaded_at": "2026-01-11 09:50:00"},
        {"image_id": 7, "location_id": 8,  "image_url": "https://example.com/marena.jpg", "uploaded_by": 1, "uploaded_at": "2026-01-11 10:00:00"},
        {"image_id": 8, "location_id": 10, "image_url": "https://example.com/innovation_center.jpg", "uploaded_by": 3, "uploaded_at": "2026-01-11 10:10:00"},
        {"image_id": 9,  "location_id": 11, "image_url": "https://images.unsplash.com/photo-1473773508845-188df298d2d1?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 9,  "uploaded_at": "2026-01-11 10:20:00"},
        {"image_id": 10, "location_id": 12, "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 10, "uploaded_at": "2026-01-11 10:30:00"},
        {"image_id": 11, "location_id": 13, "image_url": "https://images.unsplash.com/photo-1588072432836-e10032774350?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 11, "uploaded_at": "2026-01-11 10:40:00"},
        {"image_id": 12, "location_id": 14, "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 12, "uploaded_at": "2026-01-11 10:50:00"},
        {"image_id": 13, "location_id": 15, "image_url": "https://images.unsplash.com/photo-1496307653780-42ee777d4833?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 13, "uploaded_at": "2026-01-11 11:00:00"},
        {"image_id": 14, "location_id": 16, "image_url": "https://images.unsplash.com/photo-1521412644187-c49fa049e84d?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 14, "uploaded_at": "2026-01-11 11:10:00"},
        {"image_id": 15, "location_id": 17, "image_url": "https://images.unsplash.com/photo-1470337458703-46ad1756a187?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 15, "uploaded_at": "2026-01-11 11:20:00"},
        {"image_id": 16, "location_id": 18, "image_url": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 16, "uploaded_at": "2026-01-11 11:30:00"},
        {"image_id": 17, "location_id": 19, "image_url": "https://images.unsplash.com/photo-1521412644187-c49fa049e84d?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 17, "uploaded_at": "2026-01-11 11:40:00"},
        {"image_id": 18, "location_id": 20, "image_url": "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80", "uploaded_by": 18, "uploaded_at": "2026-01-11 11:50:00"},
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
        {"user_id": 9, "location_id": 11},
        {"user_id": 9, "location_id": 12},
        {"user_id": 10, "location_id": 12},
        {"user_id": 10, "location_id": 15},
        {"user_id": 11, "location_id": 13},
        {"user_id": 11, "location_id": 19},
        {"user_id": 12, "location_id": 14},
        {"user_id": 12, "location_id": 18},
        {"user_id": 13, "location_id": 11},
        {"user_id": 13, "location_id": 17},
        {"user_id": 14, "location_id": 16},
        {"user_id": 14, "location_id": 8},
        {"user_id": 15, "location_id": 17},
        {"user_id": 15, "location_id": 3},
        {"user_id": 16, "location_id": 18},
        {"user_id": 16, "location_id": 6},
        {"user_id": 17, "location_id": 19},
        {"user_id": 17, "location_id": 10},
        {"user_id": 18, "location_id": 20},
        {"user_id": 18, "location_id": 2},
    ]

    _bulk_insert("Categories", ["category_id", "category_name"], categories)
    _bulk_insert("Users",      ["user_id", "name", "email"],     users)
    _bulk_insert(
        "Locations",
        ["location_id", "name", "category_id", "address", "description", "latitude", "longitude", "created_by", "created_at"],
        locations,
    )
    _bulk_insert("Reviews",   ["review_id", "user_id", "location_id", "rating", "comment", "date"], reviews)
    _bulk_insert("Images",    ["image_id", "location_id", "image_url", "uploaded_by", "uploaded_at"], images)
    _bulk_insert("Favorites", ["user_id", "location_id"],                                            favorites)


if __name__ == "__main__":
    insert_sample_data()
    print("Sample data inserted successfully.")
