from app import app, db, Blog

with app.app_context():  # Set up the application context
    blogs = Blog.query.all()

    if blogs:
        for blog in blogs:
            print(f"ID: {blog.id}, Title: {blog.title}, Content: {blog.date_published}")
    else:
        print("No blogs found in the database.")
