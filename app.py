# self_saving_app.py - Web app that saves status directly to HTML files
from flask import Flask, render_template_string, request, jsonify, send_file
import json
import os
import re
from datetime import datetime
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initial computer list
COMPUTERS = [
    'WXDKDSA10044W', 'WXDKDSA10173W', 'W7DKDSA05967', 'WXDKDSA10175W', 'WXDKDSA10309W',
    'WXDKDSA05969W', 'WXDKDSA12991W', 'WXDKDSA10043W', 'WXDKDSA05973W', 'WXDKDSA13170W',
    'WXDKDSA00128W', 'WXDKDSA00131W', 'WXDKDSA00356L', 'WXDKDSA11357L', 'WXDKDSA12403W',
    'WXDKDSA12404W', 'WXDKDSA12406W', 'WXDKDSA12407W', 'W7DKDSA05770W', 'WXDKDSA00127W',
    'WXDKDSA00130W', 'WXDKDSA13169W', 'WXDKDSA10063W', 'WXDKDSA10988W', 'WXDKDSA11760W',
    'WXDKDSA00359L', 'WXDKDSA00355L', 'WXDKDSA05970W', 'WXDKDSA13189W', 'WXDKDSA13188W'
]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Computer Status Management</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #2B2D30;
            color: #BBBBBB;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #3C3F41;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .header {
            background: #4B5254;
            padding: 20px 30px;
            border-bottom: 1px solid #555759;
        }

        .header h1 {
            color: #FFFFFF;
            font-size: 24px;
            font-weight: 600;
        }

        .stats {
            display: flex;
            gap: 30px;
            margin-top: 15px;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stat-badge {
            background: #4F5658;
            color: #FFFFFF;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }

        .stat-badge.ready {
            background: #499C54;
        }

        .stat-badge.pending {
            background: #CC7832;
        }

        .controls {
            padding: 20px 30px;
            background: #3C3F41;
            border-bottom: 1px solid #555759;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }

        .btn {
            background: #4F5658;
            color: #FFFFFF;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn:hover {
            background: #5A6063;
        }

        .btn.primary {
            background: #4A9EFF;
        }

        .btn.primary:hover {
            background: #2B8EFF;
        }

        .btn.success {
            background: #499C54;
        }

        .btn.success:hover {
            background: #3A7B43;
        }

        .btn.danger {
            background: #CC7832;
        }

        .btn.danger:hover {
            background: #B8692B;
        }

        .search-box {
            flex: 1;
            max-width: 300px;
            padding: 8px 12px;
            background: #2B2D30;
            border: 1px solid #555759;
            border-radius: 4px;
            color: #BBBBBB;
            font-size: 13px;
        }

        .search-box:focus {
            outline: none;
            border-color: #4A9EFF;
        }

        .computer-grid {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 16px;
        }

        .computer-card {
            background: #2B2D30;
            border: 1px solid #555759;
            border-radius: 6px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            user-select: none;
        }

        .computer-card:hover {
            border-color: #4A9EFF;
            background: #2F3133;
        }

        .computer-card.ready {
            border-color: #499C54;
            background: #2F3530;
        }

        .computer-card.ready:hover {
            border-color: #5BAD66;
        }

        .computer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .computer-id {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            font-weight: 600;
            color: #FFFFFF;
        }

        .status-indicator {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #4F5658;
            transition: all 0.2s ease;
        }

        .computer-card.ready .status-indicator {
            background: #499C54;
        }

        .checkmark {
            width: 12px;
            height: 12px;
            opacity: 0;
            transition: opacity 0.2s ease;
        }

        .computer-card.ready .checkmark {
            opacity: 1;
        }

        .computer-details {
            color: #888A8C;
            font-size: 12px;
            margin-bottom: 8px;
        }

        .status-text {
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .computer-card:not(.ready) .status-text {
            color: #CC7832;
        }

        .computer-card.ready .status-text {
            color: #499C54;
        }

        .notes-section {
            margin-top: 8px;
        }

        .notes-input {
            width: 100%;
            background: #1E2124;
            border: 1px solid #555759;
            border-radius: 3px;
            padding: 6px 8px;
            color: #BBBBBB;
            font-size: 11px;
            resize: vertical;
            min-height: 60px;
        }

        .notes-input:focus {
            outline: none;
            border-color: #4A9EFF;
        }

        .notes-input::placeholder {
            color: #666;
        }

        .export-section {
            padding: 20px 30px;
            border-top: 1px solid #555759;
            background: #3C3F41;
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #499C54;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1000;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.error {
            background: #CC7832;
        }

        .save-indicator {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #4A9EFF;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .save-indicator.show {
            opacity: 1;
        }

        @media (max-width: 768px) {
            .computer-grid {
                grid-template-columns: 1fr;
                padding: 20px;
            }
            
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .search-box {
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Computer Status Management</h1>
            <div class="stats">
                <div class="stat-item">
                    <span>Total Computers:</span>
                    <span class="stat-badge" id="totalCount">{{TOTAL_COUNT}}</span>
                </div>
                <div class="stat-item">
                    <span>Ready:</span>
                    <span class="stat-badge ready" id="readyCount">{{READY_COUNT}}</span>
                </div>
                <div class="stat-item">
                    <span>Pending:</span>
                    <span class="stat-badge pending" id="pendingCount">{{PENDING_COUNT}}</span>
                </div>
            </div>
        </div>

        <div class="controls">
            <input type="text" class="search-box" placeholder="Search computer ID..." id="searchBox">
            <button class="btn success" onclick="bulkUpdate('ready')">Mark All Ready</button>
            <button class="btn danger" onclick="bulkUpdate('pending')">Mark All Pending</button>
            <button class="btn primary" onclick="downloadUpdatedHTML()">Download Updated HTML</button>
        </div>

        <div class="computer-grid" id="computerGrid">
            {{COMPUTER_CARDS}}
        </div>

        <div class="export-section">
            <span>Export Data:</span>
            <a href="/export/csv" class="btn">Download CSV</a>
            <a href="/export/json" class="btn">Download JSON</a>
            <span style="margin-left: auto; font-size: 12px; color: #888;">
                Last updated: <span id="lastUpdate">{{LAST_UPDATE}}</span>
            </span>
        </div>
    </div>

    <div id="notification" class="notification"></div>
    <div id="saveIndicator" class="save-indicator">Saving...</div>

    <script>
        // COMPUTER_STATUS_DATA_START
        let computerStatus = {{COMPUTER_STATUS_JSON}};
        // COMPUTER_STATUS_DATA_END

        function showNotification(message, isError = false) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${isError ? 'error' : ''} show`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        function showSaveIndicator() {
            const indicator = document.getElementById('saveIndicator');
            indicator.classList.add('show');
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 1500);
        }

        async function toggleStatus(computerId) {
            try {
                showSaveIndicator();
                
                const response = await fetch('/api/toggle_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ computer_id: computerId })
                });

                const data = await response.json();
                
                if (data.success) {
                    const card = document.querySelector(`[data-id="${computerId}"]`);
                    const statusText = card.querySelector('.status-text');
                    
                    // Update local status
                    computerStatus[computerId] = data.new_status;
                    
                    if (data.new_status === 'ready') {
                        card.classList.add('ready');
                        statusText.textContent = 'Ready';
                    } else {
                        card.classList.remove('ready');
                        statusText.textContent = 'Pending';
                    }
                    
                    updateStats();
                    showNotification(`${computerId} marked as ${data.new_status} - Changes saved to file!`);
                } else {
                    showNotification('Failed to update status', true);
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Connection error', true);
            }
        }

        async function bulkUpdate(status) {
            try {
                showSaveIndicator();
                
                const response = await fetch('/api/bulk_update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status: status })
                });

                const data = await response.json();
                
                if (data.success) {
                    // Update all cards and local status
                    const cards = document.querySelectorAll('.computer-card');
                    cards.forEach(card => {
                        const computerId = card.dataset.id;
                        const statusText = card.querySelector('.status-text');
                        
                        computerStatus[computerId] = status;
                        
                        if (status === 'ready') {
                            card.classList.add('ready');
                            statusText.textContent = 'Ready';
                        } else {
                            card.classList.remove('ready');
                            statusText.textContent = 'Pending';
                        }
                    });
                    
                    updateStats();
                    showNotification(`All computers marked as ${status} - Changes saved to file!`);
                } else {
                    showNotification('Failed to bulk update', true);
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Connection error', true);
            }
        }

        async function updateNotes(computerId, notes) {
            try {
                showSaveIndicator();
                
                const response = await fetch('/api/update_notes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        computer_id: computerId, 
                        notes: notes 
                    })
                });

                const data = await response.json();
                
                if (data.success) {
                    showNotification(`Notes saved for ${computerId}`);
                } else {
                    showNotification('Failed to update notes', true);
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Connection error', true);
            }
        }

        function updateStats() {
            const ready = Object.values(computerStatus).filter(status => status === 'ready').length;
            const total = Object.keys(computerStatus).length;
            const pending = total - ready;
            
            document.getElementById('totalCount').textContent = total;
            document.getElementById('readyCount').textContent = ready;
            document.getElementById('pendingCount').textContent = pending;
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        }

        async function downloadUpdatedHTML() {
            try {
                const response = await fetch('/download_html');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `computer-status-${new Date().toISOString().split('T')[0]}.html`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showNotification('Updated HTML file downloaded! Share this file with others.');
            } catch (error) {
                console.error('Error:', error);
                showNotification('Failed to download HTML', true);
            }
        }

        // Search functionality
        document.getElementById('searchBox').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = document.querySelectorAll('.computer-card');
            
            cards.forEach(card => {
                const computerId = card.dataset.id.toLowerCase();
                if (computerId.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });

        // Initialize stats
        updateStats();
    </script>
</body>
</html>'''

class StatusManager:
    def __init__(self):
        self.status_file = 'computer_status.json'
        self.html_file = 'computer_status.html'
        self.load_status()
    
    def load_status(self):
        """Load status from JSON file or initialize"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    self.computer_status = data.get('status', {})
                    self.computer_notes = data.get('notes', {})
            else:
                self.computer_status = {comp: 'pending' for comp in COMPUTERS}
                self.computer_notes = {comp: '' for comp in COMPUTERS}
                self.save_status()
        except Exception as e:
            print(f"Error loading status: {e}")
            self.computer_status = {comp: 'pending' for comp in COMPUTERS}
            self.computer_notes = {comp: '' for comp in COMPUTERS}
    
    def save_status(self):
        """Save status to JSON file"""
        try:
            data = {
                'status': self.computer_status,
                'notes': self.computer_notes,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.status_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving status: {e}")
    
    def generate_html_file(self):
        """Generate complete HTML file with current status"""
        try:
            # Generate computer cards HTML
            cards_html = ""
            for computer_id in COMPUTERS:
                status = self.computer_status.get(computer_id, 'pending')
                notes = self.computer_notes.get(computer_id, '')
                
                ready_class = 'ready' if status == 'ready' else ''
                status_text = 'Ready' if status == 'ready' else 'Pending'
                
                cards_html += f'''
            <div class="computer-card {ready_class}" data-id="{computer_id}" onclick="toggleStatus('{computer_id}')">
                <div class="computer-header">
                    <div class="computer-id">{computer_id}</div>
                    <div class="status-indicator">
                        <svg class="checkmark" fill="white" viewBox="0 0 20 20">
                            <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                        </svg>
                    </div>
                </div>
                <div class="computer-details">
                    Serial: {computer_id}<br>
                    Last Updated: {datetime.now().strftime('%Y-%m-%d')}
                </div>
                <div class="status-text">
                    {status_text}
                </div>
                <div class="notes-section">
                    <textarea 
                        class="notes-input" 
                        placeholder="Add notes..."
                        onclick="event.stopPropagation()"
                        onblur="updateNotes('{computer_id}', this.value)"
                        onkeydown="if(event.key==='Enter' && event.ctrlKey) this.blur()"
                    >{notes}</textarea>
                </div>
            </div>'''
            
            # Calculate stats
            ready_count = sum(1 for status in self.computer_status.values() if status == 'ready')
            pending_count = len(COMPUTERS) - ready_count
            
            # Replace placeholders in template
            html_content = HTML_TEMPLATE.replace('{{COMPUTER_CARDS}}', cards_html)
            html_content = html_content.replace('{{COMPUTER_STATUS_JSON}}', json.dumps(self.computer_status))
            html_content = html_content.replace('{{TOTAL_COUNT}}', str(len(COMPUTERS)))
            html_content = html_content.replace('{{READY_COUNT}}', str(ready_count))
            html_content = html_content.replace('{{PENDING_COUNT}}', str(pending_count))
            html_content = html_content.replace('{{LAST_UPDATE}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Save HTML file
            with open(self.html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return html_content
        
        except Exception as e:
            print(f"Error generating HTML: {e}")
            return None

# Initialize status manager
status_manager = StatusManager()

@app.route('/')
def index():
    """Main page - generate fresh HTML with current status"""
    html_content = status_manager.generate_html_file()
    if html_content:
        return html_content
    else:
        return "Error generating page", 500

@app.route('/api/toggle_status', methods=['POST'])
def toggle_status():
    """Toggle computer status and save to files"""
    try:
        data = request.get_json()
        computer_id = data.get('computer_id')
        
        if computer_id not in status_manager.computer_status:
            return jsonify({'success': False, 'error': 'Computer not found'})
        
        # Toggle status
        current_status = status_manager.computer_status[computer_id]
        new_status = 'ready' if current_status == 'pending' else 'pending'
        status_manager.computer_status[computer_id] = new_status
        
        # Save to files
        status_manager.save_status()
        status_manager.generate_html_file()
        
        return jsonify({'success': True, 'new_status': new_status})
    
    except Exception as e:
        print(f"Error toggling status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bulk_update', methods=['POST'])
def bulk_update():
    """Update all computers to specified status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['ready', 'pending']:
            return jsonify({'success': False, 'error': 'Invalid status'})
        
        # Update all computers
        for computer_id in COMPUTERS:
            status_manager.computer_status[computer_id] = status
        
        # Save to files
        status_manager.save_status()
        status_manager.generate_html_file()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error bulk updating: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_notes', methods=['POST'])
def update_notes():
    """Update notes for a computer"""
    try:
        data = request.get_json()
        computer_id = data.get('computer_id')
        notes = data.get('notes', '')
        
        if computer_id not in status_manager.computer_notes:
            return jsonify({'success': False, 'error': 'Computer not found'})
        
        # Update notes
        status_manager.computer_notes[computer_id] = notes
        
        # Save to files
        status_manager.save_status()
        status_manager.generate_html_file()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error updating notes: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_html')
def download_html():
    """Download the current HTML file with all status embedded"""
    try:
        # Generate fresh HTML file
        status_manager.generate_html_file()
        
        if os.path.exists(status_manager.html_file):
            return send_file(
                status_manager.html_file,
                as_attachment=True,
                download_name=f'computer-status-{datetime.now().strftime("%Y%m%d_%H%M%S")}.html',
                mimetype='text/html'
            )
        else:
            return "HTML file not found", 404
    
    except Exception as e:
        print(f"Error downloading HTML: {e}")
        return "Error generating download", 500

@app.route('/export/csv')
def export_csv():
    """Export current status as CSV"""
    try:
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Computer ID', 'Status', 'Notes', 'Last Updated'])
        
        for computer_id in COMPUTERS:
            status = status_manager.computer_status.get(computer_id, 'pending')
            notes = status_manager.computer_notes.get(computer_id, '')
            writer.writerow([computer_id, status, notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'computer_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return "Error exporting CSV", 500

@app.route('/export/json')
def export_json():
    """Export current status as JSON"""
    try:
        data = []
        for computer_id in COMPUTERS:
            data.append({
                'computer_id': computer_id,
                'status': status_manager.computer_status.get(computer_id, 'pending'),
                'notes': status_manager.computer_notes.get(computer_id, ''),
                'last_updated': datetime.now().isoformat()
            })
        
        return send_file(
            io.BytesIO(json.dumps(data, indent=2).encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'computer_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    
    except Exception as e:
        print(f"Error exporting JSON: {e}")
        return "Error exporting JSON", 500

if __name__ == '__main__':
    print("Starting Computer Status Management App...")
    print("The app will save all changes directly to HTML files!")
    print("Access at: http://localhost:5000")
    print("Share the generated HTML files with other computers!")
    
    # Generate initial HTML file
    status_manager.generate_html_file()
    
    app.run(debug=True, host='0.0.0.0', port=5000)