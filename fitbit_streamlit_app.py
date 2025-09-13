import streamlit as st
import requests
import base64
from urllib.parse import urlparse, parse_qs
import time
import pandas as pd
import datetime

# --- REQUIRED: Use Streamlit Secrets to manage credentials ---
# For deployment, add a .streamlit/secrets.toml file to your repo
# with the following content:
# CLIENT_ID = "your_client_id"
# CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = 'https://fitbit-ace.streamlit.app'
# -----------------------------------------------------------

# Fitbit API endpoints
AUTH_URL = 'https://www.fitbit.com/oauth2/authorize'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
AZM_URL = 'https://api.fitbit.com/1/user/-/activities/active-zone-minutes/date/today/1d.json'
TODAY_HEART_RATE_URL = 'https://api.fitbit.com/1/user/-/activities/heart/date/today/today/1min.json'

def get_auth_url(client_id, redirect_uri):
    """Generates the authorization URL for the user to grant access."""
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'heartrate activity profile',
        'expires_in': 87000,
        'prompt': 'consent'
    }
    req = requests.Request('GET', AUTH_URL, params=params)
    prepared = req.prepare()
    return prepared.url

def get_tokens(client_id, client_secret, auth_code, redirect_uri):
    """Exchanges the authorization code for access and refresh tokens."""
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': auth_code
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def get_active_zone_minutes_data(access_token):
    """Fetches Active Zone Minutes for today."""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(AZM_URL, headers=headers)
    response.raise_for_status()
    return response.json()
    
def get_current_heart_rate_data(access_token):
    """Fetches intraday heart rate data for today."""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(TODAY_HEART_RATE_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def get_daily_summary_data(access_token, date_str):
    """Fetches daily summary data for a given date."""
    DAILY_SUMMARY_URL = f'https://api.fitbit.com/1/user/-/activities/date/{date_str}.json'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(DAILY_SUMMARY_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    """Main function for the Streamlit app."""
    st.title("Fitbit Metrics")

    # State management for authentication
    if 'auth_code' not in st.session_state:
        st.session_state.auth_code = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    
    # Check for secrets
    if "CLIENT_ID" not in st.secrets or "CLIENT_SECRET" not in st.secrets:
        st.error("Missing Fitbit API credentials. Please add them to your `secrets.toml` file.")
        st.stop()
        
    CLIENT_ID = st.secrets["CLIENT_ID"]
    CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
    REDIRECT_URI = 'http://localhost:8501' # Must match what you set on the Fitbit dev site
    
    # Sidebar for authentication
    with st.sidebar:
        st.header("Authentication")
        if not st.session_state.access_token:
            auth_url = get_auth_url(CLIENT_ID, REDIRECT_URI)
            st.markdown(
                f"1. [Authorize Fitbit]({auth_url})"
            )
            redirect_url_input = st.text_input("2. Paste redirected URL here:")
            if st.button("Submit URL"):
                if redirect_url_input:
                    try:
                        parsed_url = urlparse(redirect_url_input)
                        query_params = parse_qs(parsed_url.query)
                        if 'code' in query_params:
                            st.session_state.auth_code = query_params['code'][0]
                            tokens = get_tokens(CLIENT_ID, CLIENT_SECRET, st.session_state.auth_code, REDIRECT_URI)
                            st.session_state.access_token = tokens['access_token']
                            st.session_state.refresh_token = tokens['refresh_token']
                            st.success("Authenticated!")
                            st.rerun()
                        else:
                            st.error("No code found in URL.")
                    except Exception as e:
                        st.error(f"Invalid URL format. Error: {e}")
                else:
                    st.warning("Please paste the URL.")
        else:
            st.success("Authenticated!")
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()
    
    # Main app content after authentication
    if st.session_state.access_token:
        try:
            with st.spinner('Fetching data...'):
                today_date = datetime.date.today().strftime('%Y-%m-%d')
                azm_data = get_active_zone_minutes_data(st.session_state.access_token)
                heart_rate_data = get_current_heart_rate_data(st.session_state.access_token)
                daily_summary_data = get_daily_summary_data(st.session_state.access_token, today_date)
            
            st.header("Today's Activity Summary")
            col1, col2, col3 = st.columns(3)
            
            # Steps
            if 'summary' in daily_summary_data and 'steps' in daily_summary_data['summary']:
                total_steps = daily_summary_data['summary']['steps']
                col1.metric("🚶‍♂️ Steps", f"{total_steps}")
                col1.progress(min(total_steps / 10000, 1.0))
            else:
                col1.metric("🚶‍♂️ Steps", "N/A")
            
            # Calories
            if 'summary' in daily_summary_data and 'caloriesOut' in daily_summary_data['summary']:
                total_calories = daily_summary_data['summary']['caloriesOut']
                col2.metric("🔥 Calories Burned", f"{total_calories}")
            else:
                col2.metric("🔥 Calories Burned", "N/A")
            
            if 'summary' in daily_summary_data:
                activity_calories = daily_summary_data['summary'].get('activityCalories')
                calories_bmr = daily_summary_data['summary'].get('caloriesBMR')
                col2.metric("🏃‍♀️ Activity Calories", f"{activity_calories}")
                col2.metric("😴 BMR Calories", f"{calories_bmr}")

            # Distance
            if 'summary' in daily_summary_data and 'distances' in daily_summary_data['summary']:
                total_distance_obj = next((d for d in daily_summary_data['summary']['distances'] if d['activity'] == 'total'), None)
                if total_distance_obj:
                    total_distance = total_distance_obj['distance']
                    col3.metric("🏃‍♀️ Distance", f"{total_distance:.2f} km")
                else:
                    col3.metric("🏃‍♀️ Distance", "N/A")
            else:
                col3.metric("🏃‍♀️ Distance", "N/A")
            
            st.subheader("Active Minutes Breakdown")
            col_min1, col_min2, col_min3, col_min4 = st.columns(4)
            if 'summary' in daily_summary_data:
                col_min1.metric("🛌 Sedentary", f"{daily_summary_data['summary'].get('sedentaryMinutes', 'N/A')} min")
                col_min2.metric("🚶 Lightly Active", f"{daily_summary_data['summary'].get('lightlyActiveMinutes', 'N/A')} min")
                col_min3.metric("🏃 Fairly Active", f"{daily_summary_data['summary'].get('fairlyActiveMinutes', 'N/A')} min")
                col_min4.metric("⚡️ Very Active", f"{daily_summary_data['summary'].get('veryActiveMinutes', 'N/A')} min")

            # Separator before the next section
            st.markdown("---")

            # Heart Rate Metrics & Active Zones (grouped together)
            st.header("Heart Rate & Active Zones")
            
            # Resting Heart Rate from daily_summary
            col_hr1, col_hr2 = st.columns(2)
            resting_heart_rate = daily_summary_data['summary'].get('restingHeartRate')
            col_hr1.metric("❤️ Resting HR", f"{resting_heart_rate} BPM" if resting_heart_rate else "N/A")

            # Current Heart Rate
            if 'activities-heart-intraday' in heart_rate_data and heart_rate_data['activities-heart-intraday']['dataset']:
                latest_hr_data = heart_rate_data['activities-heart-intraday']['dataset'][-1]
                current_heart_rate = latest_hr_data['value']
                col_hr2.metric("❤️ Current HR", f"{current_heart_rate} BPM")
            else:
                col_hr2.metric("❤️ Current HR", "N/A")
            
            st.subheader("Active Zone Minutes")
            col_azm1, col_azm2, col_azm3 = st.columns(3)
            
            if 'activities-active-zone-minutes' in azm_data and azm_data['activities-active-zone-minutes']:
                azm_metrics = azm_data['activities-active-zone-minutes'][0]['value']
                azm_value = azm_metrics.get('activeZoneMinutes')
                fat_burn_azm = azm_metrics.get('fatBurnActiveZoneMinutes')
                cardio_azm = azm_metrics.get('cardioActiveZoneMinutes')

                col_azm1.metric("⚡️ Total AZM", f"{azm_value}")
                col_azm2.metric("🔥 Fat Burn", f"{fat_burn_azm} min")
                col_azm3.metric("❤️ Cardio", f"{cardio_azm} min")
            else:
                st.info("No active zone data available.")
                
            st.subheader("Heart Rate Zones")
            if 'activities-heart' in heart_rate_data and heart_rate_data['activities-heart']:
                zones = heart_rate_data['activities-heart'][0].get('value', {}).get('heartRateZones', [])
                for zone in zones:
                    st.metric(f"❤️ {zone['name']}", f"{zone['minutes']} minutes")
            else:
                st.info("No heart rate zone data available.")

            # Heart Rate Trend Chart is now placed with other heart metrics
            st.subheader("Heart Rate Trend")
            if 'activities-heart-intraday' in heart_rate_data and heart_rate_data['activities-heart-intraday']['dataset']:
                hr_df = pd.DataFrame(heart_rate_data['activities-heart-intraday']['dataset'])
                hr_df['time'] = pd.to_datetime(hr_df['time'])
                hr_df.set_index('time', inplace=True)
                st.line_chart(hr_df['value'])
            else:
                st.info("No heart rate data available to display trend.")
            
            # Separator before the next section
            st.markdown("---")

            # Activities Log
            st.header("Activities Log")
            if 'activities' in daily_summary_data and daily_summary_data['activities']:
                for activity in daily_summary_data['activities']:
                    with st.expander(f"**{activity.get('name', 'N/A')}**"):
                        st.write(f"**Duration:** {activity.get('duration', 0) // 60000} minutes")
                        st.write(f"**Calories:** {activity.get('calories', 'N/A')}")
            else:
                st.info("No activities logged for today.")


        except requests.exceptions.HTTPError as e:
            st.error(f"Error fetching data: {e}. Please check permissions.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

        st.info("Refreshing in 2 minutes...")
        time.sleep(120)
        st.rerun()
    else:
        st.info("Please authenticate using the sidebar to continue.")

if __name__ == "__main__":
    main()
