
CREATE TABLE IF NOT EXISTS police_data (
    id INTEGER PRIMARY KEY,
    AOSNUMBER TEXT,
    city TEXT,
    county TEXT,
    state TEXT,
    agency TEXT,
    type_of_lea TEXT,
    summary TEXT,
    type_of_juris TEXT,
    technology TEXT,
    vendor TEXT,
    link1 TEXT,
    link1_snapshot TEXT,
    link1_source TEXT,
    link1_type TEXT,
    link1_date TEXT,
    link2 TEXT,
    link2_snapshot TEXT,
    link2_source TEXT,
    link2_type TEXT,
    link2_date TEXT,
    link3 TEXT,
    link3_snapshot TEXT,
    link3_source TEXT,
    link3_type TEXT,
    link3_date TEXT,
    other_links TEXT,
    latitude REAL,
    longitude REAL
);

CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    timestamp DATETIME,
    event_type TEXT,
    page_url TEXT,
    event_details TEXT
);

CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    upload_date DATETIME,
    file_size INTEGER,
    file_format TEXT
);
