Fitbit Metrics Dashboard
A simple Streamlit application to visualize your personal Fitbit activity data. This dashboard connects to the Fitbit API to fetch and display key metrics such as steps, calories, heart rate, and active zone minutes in a clean and easy-to-read format.

Features
Activity Summary: View daily steps, calories burned, and distance.

Active Minutes Breakdown: See a breakdown of time spent in sedentary, lightly active, fairly active, and very active states.

Real-time Heart Rate: Check your current and resting heart rate.

Heart Rate Zones: Understand how much time you've spent in different heart rate zones (e.g., Fat Burn, Cardio).

Heart Rate Trend: Visualize your heart rate trend over the day with a line chart.

Activities Log: See a list of your logged activities for the day.

Prerequisites
To run this application, you will need:

Python 3.7+

A Fitbit Developer Account to create your own application and get API credentials.

Setup and Configuration

1. Clone the Repository
   First, clone this repository to your local machine:

git clone <repository-url>
cd <repository-name>

2. Install Dependencies
   Install the required Python packages using pip. It's recommended to use a virtual environment.

pip install -r requirements.txt

requirements.txt:

streamlit
requests
pandas

3. Create and Configure a Fitbit App
   Go to the Fitbit Developer Dashboard and click "Register an App".

Fill out the required information. For the OAuth 2.0 Application Type, select Personal.

Set the Callback URL to http://localhost:8501. This is for local development. For deployment, you will need to add the app's public URL later.

Copy your OAuth 2.0 Client ID and Client Secret.

4. Configure Your Secrets
   For security, your API credentials should not be hardcoded in the application code. This app uses Streamlit's built-in secrets management.

Create a new folder named .streamlit in the root of your project directory, and inside it, create a file named secrets.toml.

Your file structure should look like this:

your-repo/
├── .streamlit/
│ └── secrets.toml
└── fitbit_streamlit_app.py

Add your Fitbit credentials to the secrets.toml file:

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

Important: Make sure to add .streamlit/secrets.toml to your .gitignore file to prevent it from being committed to your public repository.

Running the Application
Once your credentials are set up, run the application from your terminal:

streamlit run fitbit_streamlit_app.py

This will start the app and open it in your web browser. Follow the on-screen instructions to authorize the app with your Fitbit account.

Deployment
This application is ready for deployment on Streamlit Cloud, which provides a free tier for hosting.

Push your code (excluding the secrets.toml file) to a public GitHub repository.

Go to the Streamlit Cloud dashboard.

Click "New app" and connect to your repository.

In the "Advanced settings" section, add your CLIENT_ID and CLIENT_SECRET directly as secrets. Streamlit will handle the rest!

After deployment, you must update your Fitbit app's Callback URL to the new public URL of your Streamlit app (e.g., https://<your-username>-<your-app-name>.streamlit.app).
