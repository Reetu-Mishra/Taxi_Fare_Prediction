
import streamlit as st
import pandas as pd
import pickle
from datetime import datetime
import mysql.connector
import webbrowser

# Load model
model = pickle.load(open("LinearRegression_taxi_model.pkl", "rb"))

# Load CSV with known column names
distance_df = pd.read_csv("mode_distances.csv")
distance_df['pickup_location'] = distance_df['pickup_location'].str.lower()
distance_df['drop_location'] = distance_df['drop_location'].str.lower()

# Location dictionary
location_dict = {i: name for i, name in enumerate(distance_df['pickup_location'].unique(), 1)}
location_list = list(location_dict.values())

# MySQL insertion function
def insert_prediction(datetime_val, pickup, drop, distance,fare):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",  # Replace with your MySQL password
            database="taxi_fare_db"
        )
        cursor = conn.cursor()
        query = """
            INSERT INTO fare_predictions (datetime, pickup, dropoff, distance,fare)
            VALUES (%s, %s, %s, %s,%s)
        """
        values = (datetime_val, pickup, drop, distance,fare)
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
st.title("🚖 Taxi Fare Prediction")

# Input widgets
selected_date = st.date_input("Select Date", value=datetime.now().date())
selected_time = st.time_input("Select Time", value=datetime.now().time())
datetime_input = datetime.combine(selected_date, selected_time)

pickup = st.selectbox("Select Pickup Location", location_list)
drop = st.selectbox("Select Drop Location", location_list)

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

# Prediction
if st.button("Predict Fare"):
    if pickup != drop and distance is not None:
        hour = datetime_input.hour
        day = datetime_input.weekday()
        pickup_index = location_list.index(pickup)
        drop_index = location_list.index(drop)
        features = [[hour, day, distance, pickup_index, drop_index]]
        prediction = model.predict(features)[0]
        fare = round(prediction, 2)

        # Store to MySQL
        if insert_prediction(datetime_input, pickup, drop,distance, fare):
            st.success(f"Estimated Fare: ${fare} (saved to database)")
        else:
            st.warning("Prediction failed to save to database.")
    else:
        st.error("Invalid input: pickup and drop can't be the same.")

# Tableau Dashboard button
if st.button("📊 Open Tableau Dashboard"):
    tableau_url = "https://public.tableau.com/views/TaxifarePred/Dashboard1?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link"
    webbrowser.open_new_tab(tableau_url)
