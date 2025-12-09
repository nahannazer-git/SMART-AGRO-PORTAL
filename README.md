# Smart Agriculture Support System

> **🚀 Want to deploy?** See [`deployment/DEPLOYMENT.md`](deployment/DEPLOYMENT.md) for complete Render deployment guide.

A Flask-based web application for agricultural support with multi-role functionality.

## Project Structure

```
/app
  /static
    /css          - CSS stylesheets
    /js           - JavaScript files
    /uploads/crops - Crop image uploads
  /templates      - HTML templates
  /models         - Database models
  /routes         - Application routes/blueprints
  /utils          - Utility functions
  /ml             - Machine Learning models
  config.py       - Application configuration
  __init__.py     - Flask app factory
/run.py           - Application entry point
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python run.py
```

## Technologies

- Flask 3.0.0
- SQLite
- Bootstrap 5
- OpenWeatherMap API (for weather data)

## Environment Variables

Create a `.env` file in the project root (optional):

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/farmers_portal.db
WEATHER_API_KEY=your-openweathermap-api-key
```

### Getting OpenWeatherMap API Key

1. Sign up at https://openweathermap.org/api
2. Get your free API key
3. Add it to `.env` file as `WEATHER_API_KEY=your-key-here`
4. Without API key, the system will use mock weather data

