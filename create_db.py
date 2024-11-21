from app import db, create_app  # Import db and create_app from your main application file

# Create an instance of the app using the factory function
app = create_app()

# Use the application context to initialize the database
with app.app_context():
    db.create_all()  # This will create the database and all tables as defined in your models
    print("Database initialized and tables created successfully.")