import sqlite3
import shortuuid
from flask import Flask, jsonify, request, g, render_template, redirect, url_for, session, flash
from datetime import datetime
import requests 
import os

# --- AI Model Imports ---
# NOTE: You must install these libraries: pip install torch torchvision transformers Pillow
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import torch
import io

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['DATABASE'] = 'farm_game.db'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Makes API output readable
app.secret_key = "your_secret_key"  # For session management

# --- AI Model Configuration ---
MODEL_NAME = "wambugu71/crop_leaf_diseases_vit"

# Caching: Load the model globally once to avoid slow repeated loading
try:
    print(f"Loading Crop Disease Model: {MODEL_NAME}...")
    # Initialize the processor (for image normalization/resizing)
    # Using 'cpu' as default for broader compatibility, switch to 'cuda' if GPU is available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    disease_processor = ViTImageProcessor.from_pretrained(MODEL_NAME)
    disease_model = ViTForImageClassification.from_pretrained(MODEL_NAME).to(device)
    disease_model.eval() # Set model to evaluation mode
    print("Crop Disease Model loaded successfully.")
except Exception as e:
    print(f"ERROR: Failed to load AI model. Predictions will fail. Make sure you have PyTorch and Hugging Face libraries installed. Error: {e}")
    disease_processor = None
    disease_model = None


# In a real application, you MUST use a secure hashing library.
# from werkzeug.security import generate_password_hash, check_password_hash

# --- Database Connection Management ---
def get_db():
    """Opens a new database connection if there is none for the current context."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Closes the database at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Core Database Logic Functions (omitted for brevity, assume unchanged) ---
def create_tables(conn):
    """Sets up all required tables using shortuuid for primary keys."""
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            phone_number TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            village TEXT NOT NULL,
            district TEXT NOT NULL,
            state TEXT NOT NULL,
            sustainability_score INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            points_reward INTEGER NOT NULL,
            verification_type TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Medium'
        )
    ''')

    # User_tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tasks (
            user_task_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            status TEXT NOT NULL,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_date TIMESTAMP,
            evidence_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
    ''')

    # Badges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            badge_id TEXT PRIMARY KEY,
            badge_name TEXT NOT NULL UNIQUE,
            badge_description TEXT,
            icon_url TEXT
        )
    ''')

    # User_badges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_badges (
            user_badge_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            badge_id TEXT NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (badge_id) REFERENCES badges (badge_id)
        )
    ''')

    # Quiz-related tables
    # Crops table - stores information about different crops
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            crop_id TEXT PRIMARY KEY,
            crop_name TEXT NOT NULL UNIQUE,
            crop_description TEXT,
            icon_class TEXT,
            difficulty_level TEXT DEFAULT 'Medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Quiz categories table - for organizing questions by topic
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_categories (
            category_id TEXT PRIMARY KEY,
            category_name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Quiz questions table - stores all quiz questions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_questions (
            question_id TEXT PRIMARY KEY,
            crop_id TEXT NOT NULL,
            category_id TEXT,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'multiple_choice',
            difficulty TEXT DEFAULT 'Medium',
            explanation TEXT,
            points INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (crop_id) REFERENCES crops (crop_id),
            FOREIGN KEY (category_id) REFERENCES quiz_categories (category_id)
        )
    ''')

    # Quiz answers table - stores possible answers for each question
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_answers (
            answer_id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT 0,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES quiz_questions (question_id)
        )
    ''')

    # User quiz attempts table - tracks user quiz sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_attempts (
            attempt_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            crop_id TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            time_taken INTEGER, -- in seconds
            status TEXT DEFAULT 'IN_PROGRESS', -- IN_PROGRESS, COMPLETED, ABANDONED
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (crop_id) REFERENCES crops (crop_id)
        )
    ''')

    # User quiz responses table - tracks individual question answers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_responses (
            response_id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            answer_id TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            time_taken INTEGER, -- time spent on this question in seconds
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attempt_id) REFERENCES user_quiz_attempts (attempt_id),
            FOREIGN KEY (question_id) REFERENCES quiz_questions (question_id),
            FOREIGN KEY (answer_id) REFERENCES quiz_answers (answer_id)
        )
    ''')

    conn.commit()

# --- DATABASE FUNCTIONS (omitted for brevity, assume unchanged) ---

# --- QUIZ DATABASE FUNCTIONS ---
def get_all_crops(conn):
    """Fetches all available crops for quiz selection."""
    return conn.cursor().execute('SELECT * FROM crops ORDER BY crop_name').fetchall()

def get_crop_by_id(conn, crop_id):
    """Get specific crop information."""
    return conn.cursor().execute('SELECT * FROM crops WHERE crop_id = ?', (crop_id,)).fetchone()

def get_quiz_questions_for_crop(conn, crop_id, limit=10):
    """Get random quiz questions for a specific crop."""
    return conn.cursor().execute('''
        SELECT * FROM quiz_questions 
        WHERE crop_id = ? 
        ORDER BY RANDOM() 
        LIMIT ?
    ''', (crop_id, limit)).fetchall()

def get_question_answers(conn, question_id):
    """Get all possible answers for a specific question."""
    return conn.cursor().execute('''
        SELECT * FROM quiz_answers 
        WHERE question_id = ? 
        ORDER BY answer_id
    ''', (question_id,)).fetchall()

def create_quiz_attempt(conn, user_id, crop_id, total_questions=10):
    """Create a new quiz attempt for a user."""
    attempt_id = shortuuid.uuid()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_quiz_attempts (attempt_id, user_id, crop_id, total_questions)
        VALUES (?, ?, ?, ?)
    ''', (attempt_id, user_id, crop_id, total_questions))
    conn.commit()
    return attempt_id

def save_quiz_response(conn, attempt_id, question_id, answer_id, time_taken=None):
    """Save a user's response to a quiz question."""
    cursor = conn.cursor()
    
    # Check if the answer is correct
    answer = cursor.execute('SELECT is_correct FROM quiz_answers WHERE answer_id = ?', (answer_id,)).fetchone()
    is_correct = answer['is_correct'] if answer else False
    
    # Save the response
    response_id = shortuuid.uuid()
    cursor.execute('''
        INSERT INTO user_quiz_responses (response_id, attempt_id, question_id, answer_id, is_correct, time_taken)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (response_id, attempt_id, question_id, answer_id, is_correct, time_taken))
    
    conn.commit()
    return is_correct

def complete_quiz_attempt(conn, attempt_id, time_taken=None):
    """Complete a quiz attempt and calculate final score."""
    cursor = conn.cursor()
    
    # Calculate correct answers and score
    stats = cursor.execute('''
        SELECT COUNT(*) as total_responses,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
        FROM user_quiz_responses 
        WHERE attempt_id = ?
    ''', (attempt_id,)).fetchone()
    
    correct_answers = stats['correct_answers'] or 0
    total_responses = stats['total_responses'] or 0
    score = int((correct_answers / max(total_responses, 1)) * 100)
    
    # Update the attempt
    cursor.execute('''
        UPDATE user_quiz_attempts 
        SET correct_answers = ?, score = ?, time_taken = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
        WHERE attempt_id = ?
    ''', (correct_answers, score, time_taken, attempt_id))
    
    # Award points to user (optional - integrate with your points system)
    attempt = cursor.execute('SELECT user_id FROM user_quiz_attempts WHERE attempt_id = ?', (attempt_id,)).fetchone()
    if attempt and score >= 70:  # Award points for scores 70% and above
        points_to_award = correct_answers * 5  # 5 points per correct answer
        cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (points_to_award, attempt['user_id']))
    
    conn.commit()
    return {"correct_answers": correct_answers, "total_questions": total_responses, "score": score}

def get_user_quiz_history(conn, user_id, limit=10):
    """Get user's quiz history."""
    cursor = conn.cursor()
    return cursor.execute('''
        SELECT ua.*, c.crop_name 
        FROM user_quiz_attempts ua
        JOIN crops c ON ua.crop_id = c.crop_id
        WHERE ua.user_id = ? AND ua.status = 'COMPLETED'
        ORDER BY ua.completed_at DESC 
        LIMIT ?
    ''', (user_id, limit)).fetchall()

def get_user_by_phone(conn, phone):
    """Finds a user by their phone number for login."""
    return conn.cursor().execute('SELECT * FROM users WHERE phone_number = ?', (phone,)).fetchone()

def get_user_profile_data(conn, user_id):
    """Fetches all profile data for a specific user."""
    return conn.cursor().execute('SELECT user_id, phone_number, full_name, village, district, state, sustainability_score, points FROM users WHERE user_id = ?', (user_id,)).fetchone()

def update_user_task_status(conn, user_task_id, new_status, evidence_path=None):
    """Updates the status of a specific user task."""
    cursor = conn.cursor()
    if evidence_path:
        cursor.execute("UPDATE user_tasks SET status = ?, evidence_path = ? WHERE user_task_id = ?", (new_status, evidence_path, user_task_id))
    else:
        cursor.execute("UPDATE user_tasks SET status = ? WHERE user_task_id = ?", (new_status, user_task_id))
    conn.commit()
    return cursor.rowcount > 0  # Returns True if a row was updated

def verify_task_and_award_points(conn, user_task_id):
    """Finalizes a task, updates status to 'VERIFIED', and awards points."""
    cursor = conn.cursor()
    
    # Get user_id and task_id from the user_task
    user_task = cursor.execute("SELECT user_id, task_id FROM user_tasks WHERE user_task_id = ? AND status = 'COMPLETED'", (user_task_id,)).fetchone()
    if not user_task:
        return None  # Task not found or not ready for verification
    
    # Get points for that task
    task = cursor.execute("SELECT points_reward FROM tasks WHERE task_id = ?", (user_task['task_id'],)).fetchone()
    if not task:
        return None
    
    points_to_add = task['points_reward']
    
    # Update task status to VERIFIED
    cursor.execute("UPDATE user_tasks SET status = 'VERIFIED' WHERE user_task_id = ?", (user_task_id,))
    
    # Award points to the user
    cursor.execute("UPDATE users SET points = points + ?, sustainability_score = sustainability_score + ? WHERE user_id = ?", (points_to_add, points_to_add // 10, user_task['user_id']))
    
    conn.commit()
    return {"user_id": user_task['user_id'], "points_awarded": points_to_add}

def get_leaderboard(conn, limit=10):
    """Get top users for leaderboard."""
    cursor = conn.cursor()
    return cursor.execute('''
        SELECT full_name, points, sustainability_score,
               ROW_NUMBER() OVER (ORDER BY points DESC, sustainability_score DESC) as rank
        FROM users 
        ORDER BY points DESC, sustainability_score DESC 
        LIMIT ?
    ''', (limit,)).fetchall()

# --- Flask CLI Command ---
@app.cli.command("init-db")
def init_db_command():
    """Initializes the database."""
    db = get_db()
    create_tables(db)
    print("Database has been initialized.")

# --- HTML TEMPLATE ROUTES (omitted for brevity, assume unchanged) ---

# Splash screen route
@app.route('/splash')
def splash():
    return render_template('splash.html')

# Root â†’ Redirects to splash
@app.route('/')
def index():
    return redirect(url_for('splash'))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        name = request.form['name']
        village = request.form['village']
        district = request.form['district']
        state = request.form['state']
        
        db = get_db()
        
        # Check if user exists
        existing = db.execute('SELECT * FROM users WHERE phone_number = ?', (phone,)).fetchone()
        if existing:
            flash("User already exists! Try logging in.", "error")
            return redirect(url_for('signup'))
        
        user_id = shortuuid.uuid()
        # In a real app: password_hash = generate_password_hash(password)
        password_hash = password  # Placeholder
        
        db.execute(
            'INSERT INTO users (user_id, phone_number, password_hash, full_name, village, district, state) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, phone, password_hash, name, village, district, state)
        )
        db.commit()
        
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE phone_number = ?', (phone,)).fetchone()
        
        if user and user['password_hash'] == password:  # In a real app, use check_password_hash
            session['user_id'] = user['user_id']
            session['username'] = user['full_name']
            flash("Login successful!", "success")
            return redirect(url_for('welcome'))
        else:
            flash("Invalid credentials! Please try again.", "error")
            return redirect(url_for('login'))
    
    return render_template('login.html')

# Welcome route
@app.route('/welcome')
def welcome():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', username=session.get('username'))

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# Quiz route
@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        flash('Please log in to access the quiz.', 'error')
        return redirect(url_for('login'))
    return render_template('quiz.html')

# Leaderboard route
@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('leaderboard.html', username=session.get('username'))

@app.route('/emergency_levels')
def emergency_levels():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('emergency_levels.html', username=session.get('username'))

@app.route('/marketplace')
def marketplace():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('marketplace.html', username=session.get('username'))

# Badges route (placeholder)
@app.route('/badges')
def badges():
    if 'user_id' not in session:
        flash('Please log in to access badges.', 'error')
        return redirect(url_for('login'))
    return render_template('badges.html', username=session.get('username'))

# Profile route
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    user_data = get_user_profile_data(db, session['user_id'])
    
    # Get completed tasks count
    cursor = db.cursor()
    completed_tasks = cursor.execute(
        "SELECT COUNT(*) FROM user_tasks WHERE user_id = ? AND status = 'VERIFIED'", 
        (session['user_id'],)
    ).fetchone()[0]
    
    return render_template('profile.html', 
                         user_data=user_data, 
                         completed_tasks=completed_tasks)

# Edit Profile route
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.form.get('full_name')
            village = request.form.get('village')
            district = request.form.get('district')
            state = request.form.get('state')
            
            # Update user data
            cursor = db.cursor()
            cursor.execute("""
                UPDATE users SET 
                full_name = ?, village = ?, district = ?, state = ?
                WHERE user_id = ?
            """, (full_name, village, district, state, user_id))
            
            db.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('edit_profile'))
            
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('edit_profile'))
    
    # GET request - fetch user data
    user_data = get_user_profile_data(db, user_id)
    
    # Get completed tasks count
    cursor = db.cursor()
    completed_tasks = cursor.execute(
        "SELECT COUNT(*) FROM user_tasks WHERE user_id = ? AND status = 'VERIFIED'", 
        (user_id,)
    ).fetchone()[0]
    
    return render_template('edit_profile.html', 
                         user_data=user_data, 
                         user_preferences=None,  # Will be None for now
                         completed_tasks=completed_tasks)

# Settings route
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Return JSON for AJAX requests
        if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({'success': True, 'message': 'Settings saved successfully!'})
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
    
    # For GET request, return settings page with default values
    return render_template('settings.html', settings=None)

# Clear cache route (minimal implementation)
@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    return jsonify({'success': True, 'message': 'Cache cleared successfully'})

# Export data route (minimal implementation)
@app.route('/export_data')
def export_data():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    flash('Export functionality will be available soon!', 'info')
    return redirect(url_for('settings'))

# Delete account route (minimal implementation)
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Delete user data in proper order
        cursor.execute("DELETE FROM user_quiz_responses WHERE attempt_id IN (SELECT attempt_id FROM user_quiz_attempts WHERE user_id = ?)", (user_id,))
        cursor.execute("DELETE FROM user_quiz_attempts WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_badges WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_tasks WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        db.commit()
        
        # Clear session
        session.clear()
        
        flash('Your account has been deleted successfully.', 'info')
        return redirect(url_for('signup'))
        
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'error')
        return redirect(url_for('edit_profile'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# --- API ROUTES ---
@app.route('/api')
def api_index():
    return jsonify({
        "message": "KhetSetu Farm Game API",
        "version": "1.0",
        "endpoints": {
            "/api/users": "User management",
            "/api/tasks": "Task management", 
            "/api/quiz": "Quiz functionality",
            "/api/detect_disease": "AI Crop Health Detector" # Added new endpoint
        }
    })

# --- NEW AI CROP HEALTH DETECTION ROUTE ---
@app.route('/api/detect_disease', methods=['POST'])
def detect_disease():
    if not disease_model or not disease_processor:
        # 503 Service Unavailable if model failed to load
        return jsonify({"success": False, "error": "AI Model not initialized on server."}), 503

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No image file provided in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No image selected"}), 400
    
    try:
        # 1. Read the image stream and open it with PIL
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB") # Ensure it's RGB

        # 2. Process the image for the Vision Transformer model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        inputs = disease_processor(images=image, return_tensors="pt").to(device)

        # 3. Perform prediction (inference)
        with torch.no_grad():
            outputs = disease_model(**inputs)
        
        # 4. Get the predicted class label
        logits = outputs.logits
        predicted_class_idx = logits.argmax(-1).item()
        predicted_label = disease_model.config.id2label[predicted_class_idx]
        
        # Extract the raw probability for confidence score
        probabilities = torch.softmax(logits, dim=1)
        confidence = probabilities[0][predicted_class_idx].item()
        
        # 5. Return the result
        return jsonify({
            "success": True,
            "predicted_label": predicted_label,
            "confidence_score": f"{confidence * 100:.2f}%",
            "message": f"Disease Detected: {predicted_label}. Confidence: {confidence * 100:.2f}%"
        })

    except Exception as e:
        app.logger.error(f"Prediction failed: {e}")
        return jsonify({"success": False, "error": f"Internal server error during prediction: {str(e)}"}), 500

your_weatherapi_key = os.environ.get("WEATHERAPI_KEY")

# WeatherAPI key and base URL
API_KEY = "f0320ea1882b47abadb105525250809"
BASE_URL = "http://api.weatherapi.com/v1"

MOCK_DATA = {
    "location": {
        "name": "DemoFarm",
        "region": "Kerala",
        "country": "India",
        "localtime": "2025-09-08 10:00"
    },
    "current": {
        "temp_c": 28,
        "temp_f": 82.4,
        "condition": {"text": "Partly Cloudy", "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png"},
        "humidity": 65,
        "precip_mm": 2.0,
        "wind_kph": 10,
        "wind_dir": "NE"
    },
    "forecast": {
        "forecastday": [
            {
                "date": "2025-09-08",
                "day": {
                    "avgtemp_c": 28,
                    "condition": {"text": "Partly Cloudy", "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png"},
                    "daily_chance_of_rain": 45
                }
            },
            {
                "date": "2025-09-09",
                "day": {
                    "avgtemp_c": 30,
                    "condition": {"text": "Sunny", "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png"},
                    "daily_chance_of_rain": 10
                }
            },
            {
                "date": "2025-09-10",
                "day": {
                    "avgtemp_c": 26,
                    "condition": {"text": "Moderate rain", "icon": "//cdn.weatherapi.com/weather/64x64/day/302.png"},
                    "daily_chance_of_rain": 75
                }
            }
        ]
    }
}
@app.route("/get_weather")
def get_weather():
    location = request.args.get("q", "Delhi")
    try:
        url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={location}&days=3&aqi=yes&alerts=yes"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise Exception(data["error"]["message"])
        return jsonify(data)
    except Exception as e:
        print("⚠️ Using MOCK DATA because API failed:", e)
        return jsonify(MOCK_DATA)

@app.route('/weather')
def weather():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('weather.html', username=session.get('username'))

@app.route('/levels')
def levels():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('levels.html', username=session.get('username'))

if __name__ == "__main__":
    app.run(debug=True)
