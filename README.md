# Smart Agriculture Support System

> **Bridging the gap between Technology and Agriculture**

**Farmers Portal** is a comprehensive platform connecting Farmers, Agricultural Experts, and Government Officers. It leverages AI for disease detection, facilitates expert consultation, streamlines subsidy distribution, and opens new market avenues for farmers.

## 🚀 Quick Links
- [**Project Report**](REPORT.md) - Formal documentation of the system.
- [**User Manual**](USER_MANUAL.md) - Guide for Farmers, Experts, and Officers.
- [**Deployment Guide**](docs/DEPLOY_INSTRUCTIONS.md) - How to deploy to Render.
- [**Scrum Log**](docs/SCRUM_BOOK.txt) - Development timeline and task tracking.

## ✨ Key Features

### 🌾 For Farmers
- **AI Disease Detection**: Snap a photo of a sick plant and get instant analysis.
- **Expert Access**: Chat directly with agricultural scientists.
- **Yield Prediction**: Plan your season with ML-based yield estimates.
- **E-Marketplace**: Sell your harvest directly to consumers.

### 🔬 For Experts
- **Digital Consulting**: Review cases remotely and prescribe treatments.
- **Patient Management**: Track cases and follow up with farmers.

### 🏛️ For Government (Krishi Bhavan)
- **Subsidy Management**: Distribute seeds and fertilizers efficiently.
- **Digital Notices**: Broadcast schemes and alerts instantly.

## 🛠️ Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML5, Bootstrap 5, Vanilla JS
- **AI/ML**: TensorFlow, Scikit-Learn, NumPy
- **Database**: PostgreSQL (Production), SQLite (Dev)

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/farmers-portal.git
   cd farmers-portal
   ```

2. **Setup Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```bash
   python run.py
   ```
   Visit `http://localhost:5000` in your browser.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
