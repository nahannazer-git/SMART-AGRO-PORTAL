from app import create_app

# Vercel requires the app instance to be available for the serverless function
app = create_app()

# This allows running locally if needed
if __name__ == "__main__":
    app.run()
