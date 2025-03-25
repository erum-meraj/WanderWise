import datetime
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import firebase_admin
from firebase_admin import credentials, auth
import requests
from flask import jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session security

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

messages = [
        {"role": "system", "content": "You are a helpful travel assistant who creates and updates detailed and personalized travel itineraries. Take feedback and adjust the plan accordingly."}
    ]

api_url = "https://ai-aihackthonhub282549186415.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2025-01-01-preview"
api_key = "Fj1KPt7grC6bAkNja7daZUstpP8wZTXsV6Zjr2FOxkO7wsBQ5SzQJQQJ99BCACHYHv6XJ3w3AAAAACOGL3Xg"


# Image Upload Configuration
UPLOAD_FOLDER = 'static/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload folder exists

db = SQLAlchemy(app)

# Firebase Admin SDK Initialization
cred = credentials.Certificate("we-trail-tales-firebase-adminsdk-fbsvc-270e521c2e.json")  

# cred = credentials.Certificate("we-trail-tales-firebase-adminsdk-fbsvc-8c32fc54f1.json")  
firebase_admin.initialize_app(cred)

# Firebase REST API Endpoint
FIREBASE_WEB_API_KEY = "AIzaSyCFa5nlehx6skERCaS-M2xhjvHh87lNMmg"  
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

# Database Model
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)  # Added
    audio_url = db.Column(db.String(255), nullable=True)  # Added
    date_published = db.Column(db.Date, nullable=False, default=datetime.date.today)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# CHATBOT APIs

@app.route('/start_chat', methods=['GET'])
def start_chat():
    # Check if this is a new conversation (only system message exists)
    if len(session.get('messages', [])) <= 1:
        greeting = "Hello! I'm your travel assistant. How can I help you plan your trip today?"
        session['messages'].append({"role": "assistant", "content": greeting})
        session.modified = True
        return jsonify({"greeting": greeting})
    return jsonify({"greeting": None})
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json  # Get JSON data from frontend
    user_message = data.get("message")
    print(user_message)
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    messages.append({"role": "user", "content": user_message})
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    payload = {
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        ai_response = response.json()["choices"][0]["message"]["content"]
        return jsonify({"response": ai_response})
    else:
        print({response.status_code}, {response.text})
        return jsonify({"error": f"API error: {response.status_code}, {response.text}"}), 500

@app.route('/travel_stories')
def travel_stories():
    category = request.args.get('category', 'all')
    if category == 'all':
        blogs = Blog.query.order_by(Blog.date_published.desc()).all()
    else:
        blogs = Blog.query.filter_by(category=category).order_by(Blog.date_published.desc()).all()
    return render_template('travel_stories.html', blogs=blogs, category=category)

@app.route('/blog/<int:blog_id>')
def view_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('view_blog.html', blog=blog)

@app.route('/create_blog', methods=['GET', 'POST'])
def create_blog():
    if "user_id" not in session:
        flash("You must be logged in to create a blog.", "warning")
        return redirect(url_for("login"))

    if request.method == 'POST':
        category = request.form.get('category')
        title = request.form.get('title')
        content = request.form.get('content')
        image = request.files.get('image')
        video = request.files.get('video')
        audio = request.files.get('audio')

        image_filename = None
        video_filename = None
        audio_filename = None

        if image:
            image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_filename)

        if video:
            video_filename = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
            video.save(video_filename)

        if audio:
            audio_filename = os.path.join(app.config['UPLOAD_FOLDER'], audio.filename)
            audio.save(audio_filename)

        new_blog = Blog(
            category=category,
            title=title,
            content=content if category == 'blog' else '',
            image_url="/" + image_filename if image_filename else None,
            video_url="/" + video_filename if video_filename else None,
            audio_url="/" + audio_filename if audio_filename else None
        )

        db.session.add(new_blog)
        db.session.commit()
        flash("Blog created successfully!", "success")
        return redirect(url_for('travel_stories'))

    return render_template('create_blog.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(f"Login attempt: {email} - {password}")  # Debugging

        try:
            response = requests.post(FIREBASE_AUTH_URL, json={
                "email": email, 
                "password": password, 
                "returnSecureToken": True
            })
            data = response.json()
            
            print(f"Firebase Response: {data}")  # Debugging

            if "idToken" in data:
                user = auth.get_user_by_email(email)
                session["user_id"] = user.uid
                session["id_token"] = data["idToken"]
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                error_message = data.get("error", {}).get("message", "Invalid email or password!")
                flash(f"Login failed: {error_message}", "danger")
                print(f"Login failed: {error_message}")  # Debugging
        except Exception as e:
            flash(f"Login error: {str(e)}", "danger")
            print(f"Login error: {str(e)}")  # Debugging
    
    return render_template("login.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = auth.create_user(email=email, password=password)
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Signup error: {str(e)}", "danger")
    
    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))


@app.route('/plan-your-trip')
def plan_your_trip():
    return render_template('plan_trip.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist
    app.run(debug=True)
