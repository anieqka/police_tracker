from flask import Flask, render_template, jsonify, request, send_from_directory
import sqlite3
import os
import pandas as pd
from pathlib import Path

# Initialize Flask app
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('data/surveillance.db')
    conn.row_factory = sqlite3.Row
    return conn

# API Endpoints
@app.route('/api/comparison')
def comparison_data():
    conn = get_db_connection()
    
    # Get Atlas data
    atlas_data = conn.execute('SELECT technology, COUNT(*) as count FROM atlas_data GROUP BY technology').fetchall()
    
    # Get Border data
    border_data = conn.execute('SELECT technology, COUNT(*) as count FROM border_data GROUP BY technology').fetchall()
    
    conn.close()
    
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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        # Convert to list of dictionaries for JSON response
        data = df.to_dict('records')
        return jsonify({
            'filename': file.filename,
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Main Page Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/data')
def data_page():
    return render_template('data.html')

# Static File Handling
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Startup Configuration
def initialize_app():
    # Create required directories
    Path('data').mkdir(exist_ok=True)
    Path('uploads').mkdir(exist_ok=True)
    
    # Initialize database if not exists
    if not os.path.exists('data/surveillance.db'):
        init_db()

def init_db():
    conn = sqlite3.connect('data/surveillance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atlas_data (
            id INTEGER PRIMARY KEY,
            city TEXT,
            state TEXT,
            technology TEXT,
            vendor TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS border_data (
            id INTEGER PRIMARY KEY,
            city TEXT,
            state TEXT,
            technology TEXT,
            vendor TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=8000, debug=True)