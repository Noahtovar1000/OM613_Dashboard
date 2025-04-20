import streamlit as st
st.set_page_config(layout='wide')
import pandas as pd
import datetime
import random
import numpy as np
from PIL import Image
from faker import Faker
import plotly.express as px
import plotly.graph_objects as go
import os
import warnings

warnings.filterwarnings('ignore')
fake = Faker()

# === Cached Data Generation ===
@st.cache_data
def generate_data():
    warehouse_names = ['North Hub', 'East Depot', 'South Terminal', 'West Yard', 'Central Storage']
    managers = ['Alice Johnson', 'Bob Smith', 'Carlos Martinez', 'Diana Wu', 'Ethan Patel']
    warehouse_df = pd.DataFrame({
        'WarehouseID': [f"W{1000 + i}" for i in range(10)],
        'WarehouseName': [random.choice(warehouse_names) for _ in range(10)],
        'WarehouseManager': [random.choice(managers) for _ in range(10)],
    })

    warehouse_ids = warehouse_df['WarehouseID'].tolist()
    employee_df = pd.DataFrame({
        'EmployeeID': [f"E{2000 + i}" for i in range(20)],
        'EmployeeName': [fake.name() for _ in range(20)],
        'EmployeeStartDate': [fake.date_between(start_date='-5y', end_date='today') for _ in range(20)],
        'WarehouseID': [random.choice(warehouse_ids) for _ in range(20)],
    })

    product_names = ['Canned Beans', 'Toilet Paper', 'LED Bulb', 'Wrench Set', 'Notebook', 'Shampoo',
                     'Cleaning Spray', 'Box of Nails', 'Chocolate Bar', 'Energy Drink']
    product_df = pd.DataFrame({
        'ProductID': [f"P{3000 + i}" for i in range(25)],
        'ProductName': [random.choice(product_names) for _ in range(25)],
        'ProductExpiration': [fake.date_between(start_date='today', end_date='+3y') for _ in range(25)],
        'WarehouseID': [random.choice(warehouse_ids) for _ in range(25)],
    })

    employee_ids = employee_df['EmployeeID'].tolist()
    vehicle_df = pd.DataFrame({
        'VehicleID': [f"V{4000 + i}" for i in range(20)],
        'VehicleName': [f"Vehicle{i+1}" for i in range(20)],
        'VehicleMileage': [random.randint(5000, 120000) for _ in range(20)],
        'EmployeeID': employee_ids
    })

    route_names = ['Coastal Loop', 'Desert Express', 'Mountain Trail', 'Valley Run', 'Metro Circuit']
    cities = ['San Diego', 'Los Angeles', 'Phoenix', 'Las Vegas', 'Tucson', 'Santa Barbara', 'Riverside']
    route_df = pd.DataFrame({
        'RouteID': [f"R{5000 + i}" for i in range(5)],
        'RouteName': route_names,
        'RouteLength': [random.randint(50, 300) for _ in range(5)],
        'Origin': random.choices(cities, k=5),
        'Destination': random.choices(cities, k=5)
    })

    vehicle_route_df = pd.DataFrame({
        'VehicleID': vehicle_df['VehicleID'],
        'RouteID': np.random.choice(route_df['RouteID'], size=vehicle_df.shape[0])
    })

    receiving_party_df = pd.DataFrame({
        'ReceiverID': [f"RCV{6000 + i}" for i in range(15)],
        'ReceiverName': [fake.company() for _ in range(15)],
        'DatePromised': [fake.date_between(start_date='-1y', end_date='today') for _ in range(15)],
        'DateReceived': [fake.date_between(start_date='today', end_date='+15d') for _ in range(15)],
        'RouteID': [random.choice(route_df['RouteID']) for _ in range(15)]
    })

    receiving_party_df['DatePromised'] = pd.to_datetime(receiving_party_df['DatePromised'], dayfirst=True)
    receiving_party_df['DateReceived'] = pd.to_datetime(receiving_party_df['DateReceived'], dayfirst=True)
    product_df['ProductExpiration'] = pd.to_datetime(product_df['ProductExpiration'], dayfirst=True)
    employee_df['EmployeeStartDate'] = pd.to_datetime(employee_df['EmployeeStartDate'], dayfirst=True)
    receiving_party_df['DelayDays'] = (receiving_party_df['DateReceived'] - receiving_party_df['DatePromised']).dt.days

    return warehouse_df, employee_df, product_df, vehicle_df, route_df, vehicle_route_df, receiving_party_df

# Load Data
warehouse_df, employee_df, product_df, vehicle_df, route_df, vehicle_route_df, receiving_party_df = generate_data()

# Merging and Calculations
combined_df = pd.merge(vehicle_route_df, route_df, on='RouteID', how='left')
vehicle_and_route = pd.merge(combined_df, vehicle_df, how='inner', on='VehicleID')
vehicle_and_route_and_Receiving_Party = pd.merge(vehicle_and_route, receiving_party_df, on='RouteID', how='inner')
Average_Delay_Per_Route = vehicle_and_route_and_Receiving_Party.groupby('RouteID')['DelayDays'].mean().reset_index()
Average_Delay_Per_Route.columns = ['RouteID', 'AverageDelayDays']
avg_delay_per_vehicle = vehicle_and_route_and_Receiving_Party.groupby(['VehicleID', 'VehicleMileage'])['DelayDays'].mean().reset_index()
Route_Length_Avg_Delays = vehicle_and_route_and_Receiving_Party.groupby('RouteLength')['DelayDays'].mean().reset_index()
warehouse_and_products = pd.merge(warehouse_df, product_df, on='WarehouseID', how='inner')
Warehouse_Product_Counts = warehouse_and_products.groupby('WarehouseName')['ProductID'].count().reset_index(name='ProductCount')

# Streamlit Layout and Charts
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)
image = Image.open('BLC_LOGO.jpg')
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image(image, width=200)

html_title = """
    <style>
    .title-test {
    font-weight:bold;
    padding:5px;
    border-radius:6px;
    margin-top: 40px;}
    </style>
    <center><h1 class ="title-test">BLC Interactive Sales Dashboard</h1></center>"""
with col2:
    st.markdown(html_title, unsafe_allow_html=True)

col3, col4, col5 = st.columns([0.1, 0.45, 0.45])
with col3:
    box_date = str(datetime.datetime.now().strftime("%d %B %Y"))
    st.write(f"Last Updated by:\n {box_date}")

with col4:
    fig = px.box(receiving_party_df, y='DelayDays', title='Distribution of Delays', points='all')
    fig.update_layout(yaxis_title='Delay (Days)')
    st.plotly_chart(fig, use_container_width=True)

with col5:
    fig1 = px.bar(Average_Delay_Per_Route, x='RouteID', y='AverageDelayDays', title='Average Delay Per Route', color='RouteID')
    fig1.update_layout(xaxis_title='Route ID', yaxis_title='Average Delay', showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

st.divider()

fig2 = px.bar(avg_delay_per_vehicle, x='VehicleID', y='DelayDays', title='Vehicles and Average Delays', color='VehicleID')
fig2.update_layout(xaxis_title='VehicleID', yaxis_title='Delay(Days)', showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

_, col6 = st.columns([0.1, 1])
with col6:
    fig4 = px.line(Route_Length_Avg_Delays, x='RouteLength', y='DelayDays', title='Route Length vs Average Delay', markers=True)
    fig4.update_layout(xaxis_title='RouteLength', yaxis_title='Average Delay(Days)')
    st.plotly_chart(fig4, use_container_width=True)
