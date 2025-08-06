import streamlit as st
import pandas as pd
import pickle
from datetime import datetime
import mysql.connector
import webbrowser

# Load model
model = pickle.load(open("LinearRegression_taxi_model3.pkl", "rb"))

# Load CSV with known column names
distance_df = pd.read_csv("mode_distances.csv")
distance_df['pickup_location'] = distance_df['pickup_location'].str.lower()
distance_df['drop_location'] = distance_df['drop_location'].str.lower()

# --- Force refresh once on first browser load using new API ---
if "refresh" not in st.query_params:
    st.query_params["refresh"] = "true"
    st.rerun()

# Time encoding function
def get_time_encoded(hour):
    if 0 <= hour < 6:
        return 1  # Early Morning
    elif 6 <= hour < 12:
        return 2  # Morning
    elif 12 <= hour < 16:
        return 3  # Afternoon
    elif 16 <= hour < 20:
        return 4  # Evening
    elif 20 <= hour:
        return 5  # Night

# Creating Location Dictionary & List
location_dict = {i: name for i, name in enumerate(distance_df['pickup_location'].unique(), 1)}
location_list = list(location_dict.values())

# MySQL insertion function
def insert_prediction(time_encoded, datetime_val, pickup, drop, distance, fare):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",  # Replace with your MySQL password
            database="taxi_fare_db"
        )
        cursor = conn.cursor()
        query = """
            INSERT INTO fare_prediction (time_encoded, datetime, pickup, dropoff, distance, fare)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (time_encoded, datetime_val, pickup, drop, distance, fare)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        st.error(f"MySQL Error: {err}")
        return False

# UI
st.set_page_config(page_title="Taxi Fare Predictor", layout="centered")
st.markdown(
    """
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <h1 style='margin: 0;'>🚖 Taxi Fare Prediction</h1>
        <a href='https://public.tableau.com/views/Taxi_Fare_Prediction_Data_2019/MonthlyTrendsbyusingTotalamount?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link' target='_blank' style='text-decoration: none; font-size: 16px; color: #4A90E2;'>📊 View Tableau Dashboard</a>
    </div>
    """,
    unsafe_allow_html=True
)

# Input widgets
selected_date = st.date_input(" Date", value=datetime.now().date())
selected_time = st.time_input(" Time", value=datetime.now().time())
datetime_input = datetime.combine(selected_date, selected_time)

pickup = st.selectbox("Select Pickup Location", location_list)

# Filter drop locations
filtered_df = distance_df[
    (distance_df['pickup_location'] == pickup.lower()) |
    (distance_df['drop_location'] == pickup.lower())
]

drop_options = set()
for _, row in filtered_df.iterrows():
    if row['pickup_location'] == pickup.lower():
        drop_options.add(row['drop_location'])
    elif row['drop_location'] == pickup.lower():
        drop_options.add(row['pickup_location'])

drop_options = sorted(drop_options)
drop = st.selectbox("Select Drop Location", drop_options)

# Distance lookup
def get_distance(pickup, drop):
    if pickup == drop:
        return 0.0
    row = distance_df[
        (distance_df['pickup_location'] == pickup.lower()) & (distance_df['drop_location'] == drop.lower())
    ]
    if row.empty:
        row = distance_df[
            (distance_df['pickup_location'] == drop.lower()) & (distance_df['drop_location'] == pickup.lower())
        ]
    if not row.empty:
        return round(float(row.iloc[0]['AverageDistance']), 2)
    return None

distance = get_distance(pickup, drop)
if distance is None:
    st.error("Distance between selected locations not found!")
else:
    st.info(f"Trip Distance: {distance} miles")

st.markdown(
    """
    <style>
    div.stButton {
        text-align: center;
    }
    .st-key-predictfare .stButton button {
        background-color: #E6E6FA;
        color: #FFFFFF;
        font-size: 18px;
        font-weight: bold;
        padding: 15px 60px;
        border-radius: 20px;
        transition: background-color 0.3s ease, transform 0.2s ease;
    }
    .st-key-predictfare .stButton button:hover {
        background-color: #47d7ac;
        transform: scale(1.05);
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Prediction
if st.button("Predict Fare"):
    if pickup != drop and distance is not None:
        hour = datetime_input.hour
        day = datetime_input.weekday()
        pickup_index = location_list.index(pickup)
        drop_index = location_list.index(drop)

        time_encoded = get_time_encoded(hour)

        features = [[time_encoded,hour, day, distance, pickup_index, drop_index]]
        prediction = model.predict(features)[0]
        fare = round(prediction, 2)

        if insert_prediction(time_encoded, datetime_input, pickup, drop, distance, fare):
            st.success(f"Estimated Fare: ${fare} (saved to database)")
        else:
            st.warning("Prediction failed to save to database.")
    else:
        st.error("Invalid input: pickup and drop can't be the same.")
