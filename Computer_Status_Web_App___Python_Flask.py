# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import csv
import io
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database setup
DATABASE = 'computer_status.db'

def init_db():
    """Initialize the database with computer data"""
    computers = [
        'WXDKDSA10044W', 'WXDKDSA10173W', 'W7DKDSA05967', 'WXDKDSA10175W', 'WXDKDSA10309W',
        'WXDKDSA05969W', 'WXDKDSA12991W', 'WXDKDSA10043W', 'WXDKDSA05973W', 'WXDKDSA13170W',
        'WXDKDSA00128W', 'WXDKDSA00131W', 'WXDKDSA00356L', 'WXDKDSA11357L', 'WXDKDSA12403W',
        'WXDKDSA12404W', 'WXDKDSA12406W', 'WXDKDSA12407W', 'W7DKDSA05770W', 'WXDKDSA00127W',
        'WXDKDSA00130W', 'WXDKDSA13169W', 'WXDKDSA10063W', 'WXDKDSA10988W', 'WXDKDSA11760W',
        'WXDKDSA00359L', 'WXDKDSA00355L', 'WXDKDSA05970W', 'WXDKDSA13189W', 'WXDKDSA13188W'
    ]
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_id TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT DEFAULT ''
        )
    ''')
    
    # Insert computers if they don't exist
    for computer_id in computers:
        cursor.execute('''
            INSERT OR IGNORE INTO computers (computer_id, status) 
            VALUES (?, 'pending')
        ''', (computer_id,))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main page"""
    conn = get_db_connection()
    computers = conn.execute('''
        SELECT * FROM computers ORDER BY computer_id
    ''').fetchall()
    conn.close()
    
    return render_template('index.html', computers=computers)

@app.route('/api/toggle_status', methods=['POST'])
def toggle_status():
    """Toggle computer status between pending and ready"""
    data = request.get_json()
    computer_id = data.get('computer_id')
    
    conn = get_db_connection()
    # Get current status
    current = conn.execute('''
        SELECT status FROM computers WHERE computer_id = ?
    ''', (computer_id,)).fetchone()
    
    if current:
        new_status = 'ready' if current['status'] == 'pending' else 'pending'
        conn.execute('''
            UPDATE computers 
            SET status = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE computer_id = ?
        ''', (new_status, computer_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_status': new_status})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Computer not found'})

@app.route('/api/bulk_update', methods=['POST'])
def bulk_update():
    """Update all computers to specified status"""
    data = request.get_json()
    status = data.get('status')  # 'ready' or 'pending'
    
    if status not in ['ready', 'pending']:
        return jsonify({'success': False, 'error': 'Invalid status'})
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE computers 
        SET status = ?, last_updated = CURRENT_TIMESTAMP
    ''', (status,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_notes', methods=['POST'])
def update_notes():
    """Update notes for a computer"""
    data = request.get_json()
    computer_id = data.get('computer_id')
    notes = data.get('notes', '')
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE computers 
        SET notes = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE computer_id = ?
    ''', (notes, computer_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    conn = get_db_connection()
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) as ready,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
        FROM computers
    ''').fetchone()
    conn.close()
    
    return jsonify({
        'total': stats['total'],
        'ready': stats['ready'],
        'pending': stats['pending']
    })

@app.route('/export/csv')
def export_csv():
    """Export data as CSV"""
    conn = get_db_connection()
    computers = conn.execute('''
        SELECT computer_id, status, last_updated, notes 
        FROM computers ORDER BY computer_id
    ''').fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Computer ID', 'Status', 'Last Updated', 'Notes'])
    
    for computer in computers:
        writer.writerow([
            computer['computer_id'],
            computer['status'],
            computer['last_updated'],
            computer['notes']
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'computer_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/export/json')
def export_json():
    """Export data as JSON"""
    conn = get_db_connection()
    computers = conn.execute('''
        SELECT computer_id, status, last_updated, notes 
        FROM computers ORDER BY computer_id
    ''').fetchall()
    conn.close()
    
    data = []
    for computer in computers:
        data.append({
            'computer_id': computer['computer_id'],
            'status': computer['status'],
            'last_updated': computer['last_updated'],
            'notes': computer['notes']
        })
    
    output = io.StringIO()
    json.dump(data, output, indent=2)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'computer_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)