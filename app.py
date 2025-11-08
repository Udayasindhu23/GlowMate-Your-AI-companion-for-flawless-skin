from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import json
import sqlite3
from datetime import datetime
import uuid
import warnings
import logging

# Suppress Flask/Werkzeug development server warnings
logging.getLogger('werkzeug').setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)
os.environ['FLASK_ENV'] = 'development'

from utils.face_detection import detect_face
from utils.skin_analysis import analyze_skin, calculate_skin_health_score
from utils.skin_classifier import classify_skin_type
from utils.recommendations import get_skincare_recommendations
from chatbot.bot_engine import get_chatbot_response
from utils.pdf_generator import generate_pdf_report

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/reports', exist_ok=True)
os.makedirs('models', exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def migrate_database():
    """Migrate database to add user_id columns if they don't exist"""
    conn = sqlite3.connect('skincare.db')
    c = conn.cursor()
    
    try:
        # Check reports table
        c.execute('PRAGMA table_info(reports)')
        reports_columns = [row[1] for row in c.fetchall()]
        
        if 'user_id' not in reports_columns:
            # SQLite doesn't support adding columns with foreign keys easily
            # So we'll create a new table and migrate data
            c.execute('''
                CREATE TABLE reports_new (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    session_id TEXT,
                    image_path TEXT,
                    skin_type TEXT,
                    health_score REAL,
                    analysis_data TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Copy data from old table
            c.execute('SELECT * FROM reports')
            old_data = c.fetchall()
            for row in old_data:
                c.execute('''
                    INSERT INTO reports_new (id, user_id, session_id, image_path, skin_type, health_score, analysis_data, recommendations, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (row[0], None, row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
            
            # Drop old table and rename new one
            c.execute('DROP TABLE reports')
            c.execute('ALTER TABLE reports_new RENAME TO reports')
        
        # Check chat_history table
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        if c.fetchone():
            c.execute('PRAGMA table_info(chat_history)')
            chat_columns = [row[1] for row in c.fetchall()]
            
            if 'user_id' not in chat_columns:
                c.execute('''
                    CREATE TABLE chat_history_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        session_id TEXT,
                        message TEXT,
                        response TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                c.execute('SELECT * FROM chat_history')
                old_data = c.fetchall()
                for row in old_data:
                    c.execute('''
                        INSERT INTO chat_history_new (id, user_id, session_id, message, response, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (row[0], None, row[1], row[2], row[3], row[4]))
                
                c.execute('DROP TABLE chat_history')
                c.execute('ALTER TABLE chat_history_new RENAME TO chat_history')
        
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect('skincare.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create reports table (will be created if doesn't exist)
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            session_id TEXT,
            image_path TEXT,
            skin_type TEXT,
            health_score REAL,
            analysis_data TEXT,
            recommendations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create chat history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            message TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Run migration to add user_id if needed
    migrate_database()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to login if not authenticated, otherwise show home"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        conn = sqlite3.connect('skincare.db')
        c = conn.cursor()
        
        # Check if username or email exists
        c.execute('SELECT id, username, password_hash FROM users WHERE username = ? OR email = ?', 
                  (username, username))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            if remember:
                session.permanent = True
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    # If already logged in, redirect to home
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 4:
            flash('Password must be at least 4 characters', 'error')
            return render_template('register.html')
        
        # Check if user exists
        conn = sqlite3.connect('skincare.db')
        c = conn.cursor()
        
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            conn.close()
            flash('Username or email already exists', 'error')
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        try:
            c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                     (username, email, password_hash))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            
            # Auto login
            session['user_id'] = user_id
            session['username'] = username
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists', 'error')
    
    # If already logged in, redirect to home
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Analyze uploaded image or webcam frame"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Detect face
            face_detected, face_image = detect_face(filepath)
            
            if not face_detected:
                return jsonify({'error': 'No face detected in the image'}), 400
            
            # Analyze skin
            analysis = analyze_skin(filepath, face_image)
            
            # Calculate skin health score
            health_score = calculate_skin_health_score(analysis)
            
            # Classify skin type
            skin_type = classify_skin_type(analysis)
            
            # Get recommendations
            recommendations = get_skincare_recommendations(skin_type, analysis)
            
            # Save to database
            user_id = session.get('user_id')
            session_id = request.cookies.get('session_id', str(uuid.uuid4()))
            report_id = str(uuid.uuid4())
            
            conn = sqlite3.connect('skincare.db')
            c = conn.cursor()
            
            # Check if user_id column exists
            c.execute('PRAGMA table_info(reports)')
            columns = [row[1] for row in c.fetchall()]
            has_user_id = 'user_id' in columns
            
            if has_user_id:
                c.execute('''
                    INSERT INTO reports (id, user_id, session_id, image_path, skin_type, health_score, analysis_data, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_id,
                    user_id,
                    session_id,
                    filepath,
                    skin_type,
                    health_score,
                    json.dumps(analysis),
                    json.dumps(recommendations)
                ))
            else:
                # Fallback for old schema
                c.execute('''
                    INSERT INTO reports (id, session_id, image_path, skin_type, health_score, analysis_data, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_id,
                    session_id,
                    filepath,
                    skin_type,
                    health_score,
                    json.dumps(analysis),
                    json.dumps(recommendations)
                ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'report_id': report_id,
                'skin_type': skin_type,
                'health_score': health_score,
                'analysis': analysis,
                'recommendations': recommendations,
                'image_path': filepath
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chatbot messages"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
            message = data.get('message', '')
        else:
            message = request.form.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        # Get session ID and user ID
        session_id = request.cookies.get('session_id', str(uuid.uuid4()))
        user_id = session.get('user_id')
        
        # Get chatbot response with context
        try:
            response_text = get_chatbot_response(message, session_id)
        except Exception as e:
            print(f"Error getting chatbot response: {e}")
            response_text = "I'm sorry, I encountered an error. Please try again or rephrase your question."
        
        # Save to database
        try:
            conn = sqlite3.connect('skincare.db')
            c = conn.cursor()
            
            # Check if user_id column exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
            if c.fetchone():
                c.execute('PRAGMA table_info(chat_history)')
                columns = [row[1] for row in c.fetchall()]
                has_user_id = 'user_id' in columns
                
                if has_user_id:
                    c.execute('''
                        INSERT INTO chat_history (user_id, session_id, message, response)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, session_id, message, response_text))
                else:
                    # Fallback for old schema
                    c.execute('''
                        INSERT INTO chat_history (session_id, message, response)
                        VALUES (?, ?, ?)
                    ''', (session_id, message, response_text))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if database save fails
        
        # Get user's skin type from context if available
        from chatbot.bot_engine import get_context
        skin_type = get_context(session_id, 'skin_type')
        
        return jsonify({
            'success': True,
            'response': response_text,
            'skin_type': skin_type  # Return detected skin type for UI
        })
    
    except Exception as e:
        print(f"Error in chat route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/history')
@login_required
def get_history():
    """Get user's analysis history"""
    try:
        user_id = session.get('user_id')
        
        conn = sqlite3.connect('skincare.db')
        c = conn.cursor()
        
        # Check if user_id column exists
        c.execute('PRAGMA table_info(reports)')
        columns = [row[1] for row in c.fetchall()]
        has_user_id = 'user_id' in columns
        
        if has_user_id:
            c.execute('''
                SELECT id, image_path, skin_type, health_score, created_at
                FROM reports
                WHERE user_id = ? OR user_id IS NULL
                ORDER BY created_at DESC
                LIMIT 10
            ''', (user_id,))
        else:
            # Fallback for old schema - show all reports (temporary for migration)
            c.execute('''
                SELECT id, image_path, skin_type, health_score, created_at
                FROM reports
                ORDER BY created_at DESC
                LIMIT 10
            ''')
        
        reports = []
        for row in c.fetchall():
            reports.append({
                'id': row[0],
                'image_path': row[1],
                'skin_type': row[2],
                'health_score': row[3],
                'created_at': row[4]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'reports': reports})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/compare', methods=['POST'])
@login_required
def compare():
    """Compare two images (before/after)"""
    try:
        if 'before' not in request.files or 'after' not in request.files:
            return jsonify({'error': 'Both before and after images are required'}), 400
        
        before_file = request.files['before']
        after_file = request.files['after']
        
        # Save both images
        before_filename = f"before_{uuid.uuid4()}.{before_file.filename.rsplit('.', 1)[1].lower()}"
        after_filename = f"after_{uuid.uuid4()}.{after_file.filename.rsplit('.', 1)[1].lower()}"
        
        before_path = os.path.join(app.config['UPLOAD_FOLDER'], before_filename)
        after_path = os.path.join(app.config['UPLOAD_FOLDER'], after_filename)
        
        before_file.save(before_path)
        after_file.save(after_path)
        
        # Analyze both
        before_face_detected, before_face = detect_face(before_path)
        after_face_detected, after_face = detect_face(after_path)
        
        if not before_face_detected or not after_face_detected:
            return jsonify({'error': 'Face not detected in one or both images'}), 400
        
        before_analysis = analyze_skin(before_path, before_face)
        after_analysis = analyze_skin(after_path, after_face)
        
        before_score = calculate_skin_health_score(before_analysis)
        after_score = calculate_skin_health_score(after_analysis)
        
        improvement = after_score - before_score
        
        return jsonify({
            'success': True,
            'before': {
                'analysis': before_analysis,
                'score': before_score,
                'image_path': before_path
            },
            'after': {
                'analysis': after_analysis,
                'score': after_score,
                'image_path': after_path
            },
            'improvement': improvement,
            'improvement_percentage': (improvement / before_score * 100) if before_score > 0 else 0
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/report/<report_id>')
@login_required
def get_report(report_id):
    """Get a specific report"""
    try:
        user_id = session.get('user_id')
        conn = sqlite3.connect('skincare.db')
        c = conn.cursor()
        
        # Get column names to handle both old and new schema
        c.execute('PRAGMA table_info(reports)')
        columns = [row[1] for row in c.fetchall()]
        has_user_id = 'user_id' in columns
        
        if has_user_id:
            c.execute('''
                SELECT id, user_id, session_id, image_path, skin_type, health_score, analysis_data, recommendations, created_at
                FROM reports 
                WHERE id = ? AND (user_id = ? OR user_id IS NULL)
            ''', (report_id, user_id))
            row = c.fetchone()
            if row:
                return jsonify({
                    'success': True,
                    'report': {
                        'id': row[0],
                        'user_id': row[1],
                        'session_id': row[2],
                        'image_path': row[3],
                        'skin_type': row[4],
                        'health_score': row[5],
                        'analysis_data': json.loads(row[6]),
                        'recommendations': json.loads(row[7]),
                        'created_at': row[8]
                    }
                })
        else:
            # Fallback for old schema
            c.execute('''
                SELECT id, session_id, image_path, skin_type, health_score, analysis_data, recommendations, created_at
                FROM reports 
                WHERE id = ?
            ''', (report_id,))
            row = c.fetchone()
            if row:
                return jsonify({
                    'success': True,
                    'report': {
                        'id': row[0],
                        'session_id': row[1],
                        'image_path': row[2],
                        'skin_type': row[3],
                        'health_score': row[4],
                        'analysis_data': json.loads(row[5]),
                        'recommendations': json.loads(row[6]),
                        'created_at': row[7]
                    }
                })
        
        conn.close()
        return jsonify({'error': 'Report not found'}), 404
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_pdf/<report_id>')
@login_required
def generate_pdf(report_id):
    """Generate PDF report"""
    try:
        user_id = session.get('user_id')
        conn = sqlite3.connect('skincare.db')
        c = conn.cursor()
        
        # Get column names to handle both old and new schema
        c.execute('PRAGMA table_info(reports)')
        columns = [row[1] for row in c.fetchall()]
        has_user_id = 'user_id' in columns
        
        report_data = None
        
        if has_user_id:
            c.execute('''
                SELECT id, user_id, session_id, image_path, skin_type, health_score, analysis_data, recommendations, created_at
                FROM reports 
                WHERE id = ? AND (user_id = ? OR user_id IS NULL)
            ''', (report_id, user_id))
            row = c.fetchone()
            if row:
                report_data = {
                    'id': row[0],
                    'user_id': row[1],
                    'session_id': row[2],
                    'image_path': row[3],
                    'skin_type': row[4],
                    'health_score': row[5],
                    'analysis_data': json.loads(row[6]),
                    'recommendations': json.loads(row[7]),
                    'created_at': row[8]
                }
        else:
            # Fallback for old schema
            c.execute('''
                SELECT id, session_id, image_path, skin_type, health_score, analysis_data, recommendations, created_at
                FROM reports 
                WHERE id = ?
            ''', (report_id,))
            row = c.fetchone()
            if row:
                report_data = {
                    'id': row[0],
                    'session_id': row[1],
                    'image_path': row[2],
                    'skin_type': row[3],
                    'health_score': row[4],
                    'analysis_data': json.loads(row[5]),
                    'recommendations': json.loads(row[6]),
                    'created_at': row[7]
                }
        
        conn.close()
        
        if not report_data:
            return jsonify({'error': 'Report not found'}), 404
        
        try:
            pdf_path = generate_pdf_report(report_data)
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                return jsonify({'error': 'PDF generation failed'}), 500
            
            # Use absolute path
            abs_path = os.path.abspath(pdf_path)
            
            return send_file(
                abs_path,
                as_attachment=True,
                download_name=f'report_{report_id}.pdf',
                mimetype='application/pdf',
                conditional=True
            )
        except Exception as pdf_error:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'PDF generation error: {str(pdf_error)}'}), 500
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Additional suppression for runtime
    import sys
    from io import StringIO
    
    # Store original stderr
    original_stderr = sys.stderr
    
    # Create a custom stderr that filters out werkzeug warnings
    class FilteredStderr:
        def __init__(self, original):
            self.original = original
            self.buffer = []
        
        def write(self, message):
            # Filter out the development server warning
            if 'WARNING: This is a development server' in message:
                return
            if 'Do not use it in a production deployment' in message:
                return
            if 'Use a production WSGI server instead' in message:
                return
            # Write other messages normally
            self.original.write(message)
        
        def flush(self):
            self.original.flush()
    
    # Replace stderr with filtered version
    sys.stderr = FilteredStderr(original_stderr)
    
    print("=" * 60)
    print("SmartSkin - AI Skincare Assistant")
    print("=" * 60)
    print("\nInitializing database...")
    init_db()
    print("[OK] Database initialized!")
    print("\nStarting Flask server...")
    print("=" * 60)
    print("🌐 Server is running at: http://localhost:5000")
    print("🌐 Also accessible at: http://127.0.0.1:5000")
    print("=" * 60)
    print("\n📝 Open your web browser and navigate to the URL above")
    print("⏹️  Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    finally:
        # Restore original stderr
        sys.stderr = original_stderr
