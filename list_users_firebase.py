import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK (Ensure the JSON file path is correct)
cred = credentials.Certificate("we-trail-tales-firebase-adminsdk-fbsvc-270e521c2e.json")
firebase_admin.initialize_app(cred)

# Function to retrieve and print all users
def list_all_users():
    users = auth.list_users().iterate_all()  # Fetch all users
    for user in users:
        print(f"UID: {user.uid}, Email: {user.email}, Display Name: {user.display_name}")

def create_user():
    try:
        user = auth.create_user(
            email="testuser@example.com",
            email_verified=False,
            password="Test@1234",
            display_name="Test User",
            disabled=False
        )
        print(f"Successfully created user: {user.uid}")
    except Exception as e:
        print(f"Error creating user: {e}")

# Run the function
create_user()
# Call the function
list_all_users()
