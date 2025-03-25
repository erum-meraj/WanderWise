import datetime
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session security

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    place = request.args.get('place', 'Bali')  # Default to Bali if no place is specified
    destinations = {
        "Bali": {
            "headerImage": "bali_header.jpg",
            "description": "Explore the tropical paradise of Bali, Indonesia. From breathtaking beaches to rich cultural heritage, Bali has something for every traveler!",
            "cards": [
                {"image": "bali1.jpg", "title": "Beautiful Beaches", "text": "Relax on stunning beaches like Kuta, Seminyak, and Nusa Dua with crystal-clear waters and golden sands."},
                {"image": "bali2.jpg", "title": "Cultural Heritage", "text": "Visit iconic temples like Tanah Lot and Uluwatu to experience Bali's rich spiritual and architectural beauty."},
                {"image": "bali3.jpg", "title": "Adventure & Nature", "text": "Hike up Mount Batur for a sunrise trek or explore the lush rice terraces of Ubud for an unforgettable adventure."}
            ]
        },
        "Paris": {
            "headerImage": "paris_header.jpg",
            "description": "Discover the romantic charm of Paris, France. From the Eiffel Tower to world-class cuisine, Paris is a dream destination for travelers.",
            "cards": [
                {"image": "paris_eiffel.jpg", "title": "Eiffel Tower", "text": "Enjoy breathtaking views from the top of the Eiffel Tower, one of the most famous landmarks in the world."},
                {"image": "paris_louvre.jpg", "title": "The Louvre", "text": "Visit the Louvre Museum to see the Mona Lisa and countless other artistic masterpieces."},
                {"image": "paris_cuisine.jpg", "title": "French Cuisine", "text": "Indulge in delicious French pastries, cheese, and fine dining in the culinary capital of the world."}
            ]
        }
    }

    data = destinations.get(place, destinations["Bali"])
    
    return render_template('plan_trip.html', place=place, data=data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist
    app.run(debug=True)
