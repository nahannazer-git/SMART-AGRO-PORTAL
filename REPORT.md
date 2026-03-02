# Smart Agriculture Support System - Project Report

**Project Status**: Active / Deployed  
**Deployment URL**: [https://farmers-portal.onrender.com](https://farmers-portal.onrender.com)  
**Last Updated**: 2026-02-09

---

## 1. Executive Summary

The **Smart Agriculture Support System** is a comprehensive digital platform designed to modernize agricultural practices by bridging the communication gap between key stakeholders: Farmers, Agricultural Experts, and Government Officers (Krishi Bhavan). The system leverages modern web technologies and Artificial Intelligence (AI) to provide real-time solutions for crop health monitoring, yield prediction, and market access.

### Core Objectives
*   **Empower Farmers**: Access to AI-driven tools for instant disease detection and yield estimation.
*   **Expert Connection**: Direct communication channels with certified agricultural scientists.
*   **Government Integration**: Streamlined process for subsidy distribution and resource requests.
*   **Economic Growth**: A dedicated e-marketplace for farmers to sell produce directly to consumers.

---

## 2. System Architecture

### 2.1 Technology Stack

**Frontend**
*   **HTML5 / CSS3**: Semantic structure and custom styling ensuring accessibility.
*   **Bootstrap 5**: Responsive UI framework for consistent cross-device experience.
*   **JavaScript (Vanilla)**: Handles AJAX polling, dynamic DOM manipulation, and chart visualizations.
*   **Jinja2**: Server-side templating engine for dynamic content rendering.

**Backend**
*   **Python 3.11+**: The core programming language powering the application logic.
*   **Flask 3.0**: A lightweight, extensible web framework.
*   **Flask-SQLAlchemy**: ORM for efficient database abstraction and management.
*   **Flask-Login**: Robust session management and role-based authentication.
*   **Werkzeug**: Security helpers for password hashing and data safety.

**Database**
*   **SQLite**: Used for local development and testing environment.
*   **PostgreSQL**: High-performance production database hosted on Render.

**AI & Machine Learning**
*   **TensorFlow / Keras**: Convolutional Neural Networks (CNN) for high-accuracy leaf disease detection.
*   **Scikit-Learn**: Regression models for precise crop yield prediction.
*   **NumPy / Pandas**: Efficient data preprocessing and manipulation pipelines.
*   **Pillow (PIL)**: Image processing for upload handling and analysis.

**Deployment & Infrastructure**
*   **Render**: PaaS cloud hosting platform for Web Services and PostgreSQL.
*   **Gunicorn**: WSGI HTTP server ensuring production-grade performance.
*   **Git / GitHub**: Version control system with CI/CD integration.

**External APIs**
*   **OpenWeatherMap API**: Fetches real-time weather data crucial for yield prediction algorithms.

---

## 3. Module Description & User Roles

The system supports four distinct authenticated roles plus a public access view.

### A. Farmer Module
*   **Dashboard**: Real-time weather updates, active alerts, and a summary of crop issues.
*   **Crop Health Analysis**: AI-powered tool where farmers upload leaf images for instant disease prediction.
*   **Expert Consultation**: Integrated chat system to discuss diagnosis and treatment with assigned experts.
*   **Yield Prediction**: Estimates harvest volume based on soil parametres and inputs.
*   **Krishi Bhavan Market**: View and request government-subsidized seeds, fertilizers, and tools.
*   **Agro Marketplace**: Listings management to sell farm produce directly to the public.
*   **Reports**: Access diagnosis reports and rate expert performance.

### B. Expert Module (Agricultural Scientist)
*   **Dashboard**: Analytics on assigned cases, diagnosis statistics, and performance ratings.
*   **Diagnosis Workflow**: Review farmer issues (images/symptoms), provide diagnoses, and prescribe treatments.
*   **Communication**: Real-time chat interface to clarify symptoms with farmers.
*   **Performance Tracking**: Visualization of personal ratings and monthly resolution metrics.

### C. Krishi Bhavan Officer Module (Government)
*   **Dashboard**: Monitor regional inventory levels and request statistics.
*   **Inventory Management**: CRUD operations for subsidized products visible to farmers.
*   **Request Approval**: Workflow to review and approve/reject farmer resource requests.
*   **Notices**: Publishing system for official schemes and government alerts.

### D. Admin Module
*   **Dashboard**: Global system statistics (Users, Issues, Predictions, Yields).
*   **User Management**: Administration of all user roles (Farmer, Expert, Officer).
*   **Reports**: Generation of system-wide reports (Regional stats, Disease frequency).
*   **AI Monitoring**: Tracking model accuracy and managing training datasets.

---

## 4. AI & Machine Learning Implementation

### 4.1 Disease Prediction Model
*   **Type**: Multi-label Classification Model (Random Forest / Decision Tree).
*   **Framework**: Scikit-Learn.
*   **Inputs**: Crop Type, Selected Symptoms, Location, Season.
*   **Workflow**: User inputs symptoms -> Preprocessing -> Inference -> Prediction.
*   **Note**: Image uploads are stored for expert review and future model training (CNN), while immediate diagnosis uses symptom-based classification.

### 4.2 Yield Prediction Model
*   **Type**: Random Forest Regressor.
*   **Framework**: Scikit-learn.
*   **Input Features**: Rainfall, Temperature, Soil pH, Soil Type, Crop Type.
*   **Output**: Estimated yield in tons per hectare/acre.

---

## 5. Database Schema

The system uses a relational database with the following key entities:

1.  **Users**: Stores authentication and profile data for all roles.
2.  **Crop Issues**: Tracks reported issues, including images, symptoms, and status.
3.  **Diagnosis Reports**: Links issues to expert findings and treatment plans.
4.  **Chat Messages**: Stores communication history between farmers and experts.
5.  **Farmer Products**: Manages the public marketplace inventory.
6.  **Krishi Bhavan Products**: Manages government-subsidized inventory.
7.  **Yield Predictions**: Logs prediction requests and results.
8.  **Product Requests**: Tracks farmer requests for subsidized goods.
9.  **Notices**: Stores government announcements.

---

## 6. Future Enhancements

*   **Mobile App**: developing a native mobile application for offline access.
*   **IoT Integration**: Direct connection with soil sensors for automated data collection.
*   **Multi-language Support**: Expanding interface support for regional languages.
*   **Blockchain**: Implementing supply chain transparency for the marketplace.
