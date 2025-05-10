from flask import Flask, jsonify, request, abort, render_template, url_for
import sqlite3
import pandas as pd
import geopy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import logging
import os
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)

# Configuration
DATABASE_PATH = 'data/surveillance.db'
DATA_DIRECTORY = 'data'
UPLOADS_FOLDER = 'uploads'
GEOCODING_DELAY = 1.0
MAX_RETRIES = 3
FALLBACK_COORDS = {
    "VA": (37.9268, -78.0205),
    "IL": (40.0623, -89.3985),
    "GA": (32.8399, -83.5753),
    # Add more states as needed
}
DEBUG_MODE = True

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize geocoder
geolocator = Nominatim(user_agent="police_tech_app")

# Database connection
def get_db_connection():
    """Gets a database connection, with row factory set."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def close_db_connection(conn):
    """Closes a database connection."""
    if conn:
        conn.close()

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
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
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        raise
    finally:
        close_db_connection(conn)

def remove_html_tags(text):
    """Removes HTML tags from a string."""
    if not isinstance(text, str):
        return text
    clean_text = re.sub('<[^>]*>', '', text)
    return clean_text.strip()

def geocode_location(city, state):
    """
    Geocodes a city and state using Nominatim, with retries and error handling.
    """
    city = remove_html_tags(city)
    state = remove_html_tags(state)

    cache_key = f"{city},{state}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude FROM police_data WHERE city = ? AND state = ?", (city, state))
    result = cursor.fetchone()
    close_db_connection(conn)
    if result:
        return result['latitude'], result['longitude']

    for attempt in range(MAX_RETRIES):
        try:
            location = geolocator.geocode(f"{city}, {state}, USA", timeout=10)
            if location:
                latitude, longitude = location.latitude, location.longitude
                # Store the result in the database
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO police_data (city, state, latitude, longitude) VALUES (?, ?, ?, ?)",
                               (city, state, latitude, longitude))
                conn.commit()
                close_db_connection(conn)

                return latitude, longitude
        except GeocoderTimedOut:
            logging.warning(f"Geocoding timed out for {city}, {state}. Retrying in {GEOCODING_DELAY} seconds...")
            time.sleep(GEOCODING_DELAY)
        except GeocoderServiceError as e:
            logging.error(f"Geocoding service error for {city}, {state}: {e}")
            if 'rate limit' in str(e).lower():
                time.sleep(GEOCODING_DELAY)
            else:
                return None, None
        except Exception as e:
            logging.error(f"Geocoding error for {city}, {state}: {e}")
            return None, None

    logging.warning(f"Geocoding failed after {MAX_RETRIES} attempts for {city}, {state}.")
    latitude, longitude = FALLBACK_COORDS.get(state, (None, None))
    if latitude is not None and longitude is not None:
        logging.warning(f"Using fallback coordinates {latitude}, {longitude} for {city}, {state}.")
        return latitude, longitude
    return None, None


def load_data_from_csv(csv_file):
    """
    Loads data from a CSV file, geocodes locations, and stores it in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        df = pd.read_csv(csv_file)

        # Ensure that the CSV has these columns.  Adjust as necessary to match *your* CSV header names.
        required_columns = ['AOSNUMBER', 'City', 'County', 'State', 'Agency', 'Type of LEA', 'Summary',
                            'Type of Juris', 'Technology', 'Vendor', 'Link 1', 'Link 1 Snapshot',
                            'Link 1 Source', 'Link 1 Type', 'Link 1 Date', 'Link 2', 'Link 2 Snapshot',
                            'Link 2 Source', 'Link 2 Type', 'Link 2 Date', 'Link 3', 'Link 3 Snapshot',
                            'Link 3 Source', 'Link 3 Type', 'Link 3 Date', 'Other Links']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"CSV file is missing required column: {col}")

        for _, row in df.iterrows():
            city = remove_html_tags(row.get('City'))
            state = remove_html_tags(row.get('State'))
            latitude, longitude = geocode_location(city, state)

            if latitude is not None and longitude is not None:
                try:
                    cursor.execute('''
                        INSERT INTO police_data (
                            AOSNUMBER, city, county, state, agency, type_of_lea, summary,
                            type_of_juris, technology, vendor, link1, link1_snapshot,
                            link1_source, link1_type, link1_date, link2, link2_snapshot,
                            link2_source, link2_type, link2_date, link3, link3_snapshot,
                            link3_source, link3_type, link3_date, other_links, latitude, longitude
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            row['AOSNUMBER'], city, row['County'], state, row['Agency'],
                            row['Type of LEA'], row['Summary'], row['Type of Juris'],
                            row['Technology'], row['Vendor'], row['Link 1'],
                            row['Link 1 Snapshot'], row['Link 1 Source'], row['Link 1 Type'],
                            row['Link 1 Date'], row['Link 2'], row['Link 2 Snapshot'],
                            row['Link 2 Source'], row['Link 2 Type'], row['Link 2 Date'],
                            row['Link 3'], row['Link 3 Snapshot'], row['Link 3 Source'],
                            row['Link 3 Type'], row['Link 3 Date'], row['Other Links'],
                            latitude, longitude
                        )
                    )
                except sqlite3.Error as e:
                    logging.error(f"Database insertion error: {e}, for row: {row.to_dict()}")
                    conn.rollback()
                    continue
                conn.commit()
            else:
                logging.warning(f"Failed to geocode {city}, {state}. Skipping database insertion for this entry.")

        logging.info(f"Successfully loaded {len(df)} entries into the database.")

    except (pd.errors.EmptyDataError, ValueError, FileNotFoundError) as e:
        logging.error(f"Error reading CSV file: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise
    finally:
        close_db_connection(conn)

@app.route('/api/map_data')
def get_map_data():
    """
    API endpoint to retrieve data for the map, filtered by bounding box.
    """
    conn = get_db_connection()
    try:
        bbox = request.args.get('bbox')
        if not bbox:
            return jsonify({'error': 'Bounding box is required'}), 400
        try:
            min_lng, min_lat, max_lng, max_lat = map(float, bbox.split(','))
        except ValueError:
            return jsonify({'error': 'Invalid bounding box format. Use min_lng,min_lat,max_lng,max_lat'}), 400

        query = '''
            SELECT latitude, longitude, city, state, agency, technology, vendor
            FROM police_data
            WHERE longitude BETWEEN ? AND ?
              AND latitude BETWEEN ? AND ?
        '''
        cursor = conn.execute(query, (min_lng, max_lng, min_lat, max_lat))
        results = cursor.fetchall()
        data = [{'lat': row['latitude'], 'lng': row['longitude'], 'city': row['city'], 'state': row['state'],
                 'agency': row['agency'], 'technology': row['technology'], 'vendor': row['vendor']}
                for row in results]
        return jsonify(data)
    except sqlite3.Error as e:
        logging.error(f"Database query error: {e}")
        return jsonify({'error': f"Database error: {e}"}), 500
    finally:
        close_db_connection(conn)

@app.route('/api/comparison')
def comparison_data():
    """
    API endpoint to retrieve comparison data for Atlas and Border datasets.
    Returns JSON with technology distribution and total agencies.
    """
    conn = get_db_connection()
    try:
        atlas_data = conn.execute('SELECT technology, COUNT(*) as count FROM police_data GROUP BY technology').fetchall()
        border_data = conn.execute('SELECT technology, COUNT(*) as count FROM police_data GROUP BY technology').fetchall()
        return jsonify({
            'tech_distribution': {
                'atlas': {row['technology']: row['count'] for row in atlas_data},
                'border': {row['technology']: row['count'] for row in border_data}
            },
            'total_agencies': {
                'atlas': sum(row['count'] for row in atlas_data),
                'border': sum(row['count'] for row in border_data)
            }
        })
    except sqlite3.Error as e:
        return jsonify({'error': f"Database error: {e}"}), 500
    finally:
        close_db_connection(conn)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    API endpoint to handle file uploads (CSV, JSON).  Returns JSON
    representation of the uploaded data.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

    try:
        file.save(filename)
        
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(filename)
        elif filename.lower().endswith('.json'):
            df = pd.read_json(filename)
        else:
            return jsonify({'error': 'Unsupported file type. Please upload a CSV or JSON file.'}), 400
        
        data = df.to_dict(orient='records')
        return jsonify({
            'filename': file.filename,
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    """Route for the home page (index.html)."""
    return render_template('index.html')

@app.route('/data.html')
def data_page():
    """Route for the data page (data.html)."""
    return render_template('data.html'), 200

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    """Error handler for 404 Not Found errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Error handler for 500 Internal Server Errors"""
    return render_template('500.html'), 500

def initialize_app():
    """
    Initializes the application:
    - Creates required directories (data, uploads).
    - Initializes the database if it doesn't exist.
    - Loads initial data from police_tech_data.json if the database is empty.
    """
    Path(DATA_DIRECTORY).mkdir(exist_ok=True)
    Path(UPLOADS_FOLDER).mkdir(exist_ok=True)

    if not os.path.exists(DATABASE_PATH):
        init_db()
        json_file_path = os.path.join(DATA_DIRECTORY, 'police_tech_data.json')
        if os.path.exists(json_file_path):
            try:
                load_data_from_json(json_file_path)
                logging.info("Successfully loaded initial data from police_tech_data.json")
            except Exception as e:
                logging.error(f"Error loading initial data: {e}")
        else:
            logging.warning("police_tech_data.json not found. Application will run without initial data.")
    else:
        logging.info("Database already exists. Skipping initialization.")

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=8000, debug=DEBUG_MODE)