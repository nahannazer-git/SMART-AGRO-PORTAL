from app import create_app

# Create the Flask application instance
# Vercel looks for the 'app' or 'application' variable in this file
app = create_app()

if __name__ == "__main__":
    app.run()
