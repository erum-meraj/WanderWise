import datetime
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import firebase_admin
from firebase_admin import credentials, auth
from api_param_ext import extract_travel_info
import markdown
from flight_func import get_flight_offers
from hotel_func import get_hotel_offers


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session security

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Azure OpenAI Configuration
api_url = "https://ai-aihackthonhub282549186415.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2023-05-15"
api_key = "Fj1KPt7grC6bAkNja7daZUstpP8wZTXsV6Zjr2FOxkO7wsBQ5SzQJQQJ99BCACHYHv6XJ3w3AAAAACOGL3Xg"

# Image Upload Configuration
UPLOAD_FOLDER = 'static/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload folder exists

db = SQLAlchemy(app)

# Configuration
FLIGHT_API_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
HOTEL_API_URL = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"

# API credentials (in a real app, these should be in environment variables)
FLIGHT_API_KEY = "P0H5Nt1hmixtoHkwUD6w8T8PG45J"
HOTEL_API_KEY = "jH4yZd6iyZEy8XF3NrreWC9FgcSP"


# Firebase Admin SDK Initialization
cred = credentials.Certificate("we-trail-tales-firebase-adminsdk-fbsvc-59fdb71862.json")  
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
    video_url = db.Column(db.String(255), nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)
    date_published = db.Column(db.Date, nullable=False, default=datetime.date.today)


final_plan = ""

@app.before_request
def initialize_session_variables():
    if 'messages' not in session:
        session['messages'] = [
            {"role": "system", "content": "You are a helpful travel assistant who creates and updates detailed and personalized travel itineraries. Take feedback and adjust the plan accordingly."}
        ]

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

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Get messages from session and add new user message
        messages = session.get('messages', [])
        
        # Check for "Thanks" message
        if user_message.lower() == 'thanks':
            # Store the final plan in session before redirecting
            if messages and messages[-1]['role'] == 'assistant':
                session['final_plan'] = messages[-1]['content']
            # Return a response that tells the client to redirect
            return jsonify({"redirect": "/final_trip_plan"})
        
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

        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            ai_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I couldn't process that request.")
            messages.append({"role": "assistant", "content": ai_response})
            session['messages'] = messages
            session.modified = True
            return jsonify({"response": ai_response})
        else:
            error_msg = f"API error: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text[:200]}"
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    try:
        # Reset the chat history with updated system message
        session['messages'] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful travel assistant. Before providing any travel itinerary, "
                    "collect the following required details: number of days for the trip, origin-destination details, "
                    "and traveler count. If any information is missing, ask the user for it. "
                    "Once all details are gathered, generate a personalized and detailed travel itinerary. "
                    "Take feedback and adjust the plan accordingly."
                )
            }
        ]
        session.modified = True
        return jsonify({"status": "Chat history cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_chat_history')
def get_chat_history():
    return jsonify({"messages": session.get('messages', [])})

@app.route('/start_chat', methods=['GET'])
def start_chat():
    try:
        messages = session.get('messages', [])
        if len(messages) <= 1:
            greeting = "Hello! I'm your travel assistant. Let's start planning your trip. Can you provide the trip duration, origin, destination, and the number of travelers?"
            messages.append({"role": "assistant", "content": greeting})
            session['messages'] = messages
            session.modified = True
            return jsonify({"greeting": greeting})
        return jsonify({"greeting": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        try:
            category = request.form.get('category')
            title = request.form.get('title')
            content = request.form.get('content')
            image = request.files.get('image')
            video = request.files.get('video')
            audio = request.files.get('audio')

            if not all([category, title]):
                flash("Category and title are required!", "danger")
                return redirect(request.url)

            image_filename = None
            video_filename = None
            audio_filename = None

            if image and image.filename:
                image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_filename)

            if video and video.filename:
                video_filename = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
                video.save(video_filename)

            if audio and audio.filename:
                audio_filename = os.path.join(app.config['UPLOAD_FOLDER'], audio.filename)
                audio.save(audio_filename)

            new_blog = Blog(
                category=category,
                title=title,
                content=content if category == 'blog' else '',
                image_url=f"/{image_filename}" if image_filename else None,
                video_url=f"/{video_filename}" if video_filename else None,
                audio_url=f"/{audio_filename}" if audio_filename else None
            )

            db.session.add(new_blog)
            db.session.commit()
            flash("Blog created successfully!", "success")
            return redirect(url_for('travel_stories'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating blog: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('create_blog.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for('login'))

        try:
            response = requests.post(FIREBASE_AUTH_URL, json={
                "email": email, 
                "password": password, 
                "returnSecureToken": True
            }, timeout=10)
            
            data = response.json()

            if "idToken" in data:
                user = auth.get_user_by_email(email)
                session["user_id"] = user.uid
                session["id_token"] = data["idToken"]
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                error_message = data.get("error", {}).get("message", "Invalid email or password!")
                flash(f"Login failed: {error_message}", "danger")
        except requests.Timeout:
            flash("Login timeout. Please try again.", "danger")
        except Exception as e:
            flash(f"Login error: {str(e)}", "danger")
    
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        print(f"Signup Attempt - Email: {email}, Password: {password}")  # Debugging

        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for('signup'))

        try:
            print("Trying to create user in Firebase...")  # Debugging
            user = auth.create_user(email=email, password=password)
            print(f"User Created Successfully - UID: {user.uid}")  # Debugging
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            print(f"Signup Error: {str(e)}")  # Print the actual error in terminal
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

CLIENT_ID = "Xwjs1dXdMvJYJhoOuZWON44ImGCwpZZI"
CLIENT_SECRET = "6ugKGuGqpHORjpCd"
ACCESS_TOKEN = None
TOKEN_EXPIRATION = None

def get_access_token():
    """Get access token from Amadeus API"""
    global ACCESS_TOKEN, TOKEN_EXPIRATION
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        ACCESS_TOKEN = token_data["access_token"]
        expires_in = token_data.get("expires_in", 1800)
        TOKEN_EXPIRATION = datetime.now().timestamp() + expires_in
        return True
    except Exception as e:
        print(f"Error obtaining access token: {e}")
        return False
# def get_flight_offers():
#     """Fetch flight offers from Amadeus API"""
#     url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
#     headers = {
#         "Authorization": f"Bearer {ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "originDestinations": [
#             {
#                 "id": "1",
#                 "originLocationCode": "BOM",
#                 "destinationLocationCode": "PAR",
#                 "departureDateTimeRange": {
#                     "date": "2025-03-29"
#                 }
#             }
#         ],
#         "travelers": [
#             {
#                 "id": "1",
#                 "travelerType": "ADULT",
#                 "fareOptions": ["STANDARD"]
#             },
#             {
#                 "id": "2",
#                 "travelerType": "ADULT",
#                 "fareOptions": ["STANDARD"]
#             }
#         ],
#         "sources": ["GDS"],
#         "searchCriteria": {
#             "maxFlightOffers": 2
#         }
#     }
    
#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         response.raise_for_status()
#         return response.json().get('data', [])
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching flight offers: {e}")
#         return []
# def get_hotel_offers():
#     """Fetch hotel offers from Amadeus API"""
#     url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
#     headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
#     params = {
#         'hotelIds': 'MCLONGHM',
#         'adults': 2,
#         'checkInDate': '2025-03-29',
#         'checkOutDate': '2025-03-31',
#         'roomQuantity': 1,
#         'currency': 'USD'
#     }
    
#     try:
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()
#         return response.json().get('data', [])
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching hotel offers: {e}")
#         return []


@app.route('/check_final_plan')
def check_final_plan():
    final_plan = session.get('final_plan')
    return jsonify({'has_plan': final_plan is not None})

@app.route('/final_trip_plan')
def final_trip_plan():
    # Get the final plan from session
    final_plan = session.get('final_plan', 'No trip plan generated yet.')
    
    flight_offers = get_flight_offers()
    hotel_offers = get_hotel_offers()
    
    # Prepare search parameters for the template
    search_params = {
        'originLocationCode': 'BOM',
        'destinationLocationCode': 'PAR',
        'checkInDate': '2025-03-29',
        'checkOutDate': '2025-03-31',
        'adults': 2,
        'roomQuantity': 1
    }
    
    # Convert markdown to HTML
    plan_description_html = markdown.markdown(final_plan)
    
    # Render the combined template
    return render_template(
        'combined_results.html',
        offers=flight_offers,
        hotels=hotel_offers,
        search_params=search_params,
        plan_description=plan_description_html
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist
    app.run(debug=True)