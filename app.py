# app.py - Multi-user Flask app with live database updates
from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import csv
import io
from datetime import datetime
import os
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Database configuration
DATABASE = 'computers.db'
DATABASE_LOCK = threading.Lock()

def get_db():
    """Get database connection with proper configuration"""
    conn = sqlite3.connect(DATABASE, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
    return conn

def init_database():
    """Initialize database with computers table and data"""
    computers = [
        'WXDKDSA10044W', 'WXDKDSA10173W', 'W7DKDSA05967', 'WXDKDSA10175W', 'WXDKDSA10309W',
        'WXDKDSA05969W', 'WXDKDSA12991W', 'WXDKDSA10043W', 'WXDKDSA05973W', 'WXDKDSA13170W',
        'WXDKDSA00128W', 'WXDKDSA00131W', 'WXDKDSA00356L', 'WXDKDSA11357L', 'WXDKDSA12403W',
        'WXDKDSA12404W', 'WXDKDSA12406W', 'WXDKDSA12407W', 'W7DKDSA05770W', 'WXDKDSA00127W',
        'WXDKDSA00130W', 'WXDKDSA13169W', 'WXDKDSA10063W', 'WXDKDSA10988W', 'WXDKDSA11760W',
        'WXDKDSA00359L', 'WXDKDSA00355L', 'WXDKDSA05970W', 'WXDKDSA13189W', 'WXDKDSA13188W'
    ]
    
    with DATABASE_LOCK:
        conn = get_db()
        try:
            # Create computers table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS computers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    computer_id TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create trigger to auto-update updated_at
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS update_computers_timestamp 
                AFTER UPDATE ON computers
                BEGIN
                    UPDATE computers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Insert computers if they don't exist
            for computer_id in computers:
                conn.execute('''
                    INSERT OR IGNORE INTO computers (computer_id, status) 
                    VALUES (?, 'pending')
                ''', (computer_id,))
            
            conn.commit()
            print(f"✅ Database initialized with {len(computers)} computers")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            conn.rollback()
        finally:
            conn.close()

@app.route('/')
def index():
    """Main dashboard - shows current status from database"""
    with DATABASE_LOCK:
        conn = get_db()
        try:
            computers = conn.execute('''
                SELECT computer_id, status, notes, updated_at 
                FROM computers 
                ORDER BY computer_id
            ''').fetchall()
            
            # Get statistics
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) as ready,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM computers
            ''').fetchone()
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
            computers = []
            stats = {'total': 0, 'ready': 0, 'pending': 0}
        finally:
            conn.close()
    
    return render_template('dashboard.html', computers=computers, stats=stats)

@app.route('/api/toggle_status', methods=['POST'])
def toggle_status():
    """Toggle computer status in database"""
    try:
        data = request.get_json()
        computer_id = data.get('computer_id')
        
        if not computer_id:
            return jsonify({'success': False, 'error': 'Computer ID required'})
        
        with DATABASE_LOCK:
            conn = get_db()
            try:
                # Get current status
                current = conn.execute('''
                    SELECT status FROM computers WHERE computer_id = ?
                ''', (computer_id,)).fetchone()
                
                if not current:
                    return jsonify({'success': False, 'error': 'Computer not found'})
                
                # Toggle status
                new_status = 'ready' if current['status'] == 'pending' else 'pending'
                
                # Update database
                conn.execute('''
                    UPDATE computers 
                    SET status = ? 
                    WHERE computer_id = ?
                ''', (new_status, computer_id))
                
                conn.commit()
                
                print(f"✅ {computer_id} status changed to {new_status}")
                
                return jsonify({
                    'success': True, 
                    'new_status': new_status,
                    'computer_id': computer_id,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Toggle status error: {e}")
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)})
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bulk_update', methods=['POST'])
def bulk_update():
    """Update all computers to specified status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['ready', 'pending']:
            return jsonify({'success': False, 'error': 'Invalid status'})
        
        with DATABASE_LOCK:
            conn = get_db()
            try:
                # Update all computers
                result = conn.execute('''
                    UPDATE computers SET status = ?
                ''', (status,))
                
                conn.commit()
                
                print(f"✅ Bulk update: {result.rowcount} computers set to {status}")
                
                return jsonify({
                    'success': True, 
                    'status': status,
                    'updated_count': result.rowcount,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Bulk update error: {e}")
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)})
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ Bulk update API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_notes', methods=['POST'])
def update_notes():
    """Update notes for a computer"""
    try:
        data = request.get_json()
        computer_id = data.get('computer_id')
        notes = data.get('notes', '')
        
        if not computer_id:
            return jsonify({'success': False, 'error': 'Computer ID required'})
        
        with DATABASE_LOCK:
            conn = get_db()
            try:
                # Update notes
                result = conn.execute('''
                    UPDATE computers 
                    SET notes = ? 
                    WHERE computer_id = ?
                ''', (notes, computer_id))
                
                if result.rowcount == 0:
                    return jsonify({'success': False, 'error': 'Computer not found'})
                
                conn.commit()
                
                print(f"✅ Notes updated for {computer_id}")
                
                return jsonify({
                    'success': True,
                    'computer_id': computer_id,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Update notes error: {e}")
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)})
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ Update notes API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    """Get current statistics from database"""
    try:
        with DATABASE_LOCK:
            conn = get_db()
            try:
                stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) as ready,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        MAX(updated_at) as last_update
                    FROM computers
                ''').fetchone()
                
                return jsonify({
                    'total': stats['total'],
                    'ready': stats['ready'],
                    'pending': stats['pending'],
                    'last_update': stats['last_update'],
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Stats query error: {e}")
                return jsonify({'success': False, 'error': str(e)})
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ Stats API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/computers')
def get_computers():
    """Get all computers with current status - for AJAX refresh"""
    try:
        with DATABASE_LOCK:
            conn = get_db()
            try:
                computers = conn.execute('''
                    SELECT computer_id, status, notes, updated_at 
                    FROM computers 
                    ORDER BY computer_id
                ''').fetchall()
                
                computers_list = []
                for comp in computers:
                    computers_list.append({
                        'computer_id': comp['computer_id'],
                        'status': comp['status'],
                        'notes': comp['notes'],
                        'updated_at': comp['updated_at']
                    })
                
                return jsonify({
                    'success': True,
                    'computers': computers_list,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Get computers error: {e}")
                return jsonify({'success': False, 'error': str(e)})
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ Get computers API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export/csv')
def export_csv():
    """Export current data as CSV"""
    try:
        with DATABASE_LOCK:
            conn = get_db()
            try:
                computers = conn.execute('''
                    SELECT computer_id, status, notes, updated_at 
                    FROM computers 
                    ORDER BY computer_id
                ''').fetchall()
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['Computer ID', 'Status', 'Notes', 'Last Updated'])
                
                for comp in computers:
                    writer.writerow([
                        comp['computer_id'],
                        comp['status'],
                        comp['notes'] or '',
                        comp['updated_at'] or ''
                    ])
                
                output.seek(0)
                
                return send_file(
                    io.BytesIO(output.getvalue().encode('utf-8')),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'computers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                )
                
            except Exception as e:
                print(f"❌ CSV export error: {e}")
                return f"Export error: {e}", 500
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ CSV export API error: {e}")
        return f"Export error: {e}", 500

@app.route('/export/json')
def export_json():
    """Export current data as JSON"""
    try:
        with DATABASE_LOCK:
            conn = get_db()
            try:
                computers = conn.execute('''
                    SELECT computer_id, status, notes, updated_at 
                    FROM computers 
                    ORDER BY computer_id
                ''').fetchall()
                
                computers_list = []
                for comp in computers:
                    computers_list.append({
                        'computer_id': comp['computer_id'],
                        'status': comp['status'],
                        'notes': comp['notes'] or '',
                        'updated_at': comp['updated_at'] or ''
                    })
                
                json_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'total_computers': len(computers_list),
                    'computers': computers_list
                }
                
                output = io.StringIO()
                json.dump(json_data, output, indent=2)
                output.seek(0)
                
                return send_file(
                    io.BytesIO(output.getvalue().encode('utf-8')),
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=f'computers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                )
                
            except Exception as e:
                print(f"❌ JSON export error: {e}")
                return f"Export error: {e}", 500
            finally:
                conn.close()
                
    except Exception as e:
        print(f"❌ JSON export API error: {e}")
        return f"Export error: {e}", 500

if __name__ == '__main__':
    print("🚀 Starting Computer Status Management System...")
    print("📊 Initializing database...")
    
    # Initialize database
    init_database()
    
    print("✅ Database ready!")
    print("🌐 Starting web server...")
    print("📍 Access your app at: http://localhost:5000")
    print("🔄 All changes are automatically saved to database!")
    print("👥 Multiple users can access simultaneously!")
    
    # Run Flask app
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True  # Enable threading for multiple users
    )