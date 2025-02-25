import requests
import lightningchart as lc
import trimesh
import collections
from datetime import datetime
import os
import threading
import time

with open(
    "D:/Computer Aplication/WorkPlacement/Projects/shared_variable.txt", "r"
) as f:
    mylicensekey = f.read().strip()
lc.set_license(mylicensekey)

# ====== Step 1: Fetch and Process Weather Data ======
API_URL = "https://api.open-meteo.com/v1/forecast"
LAT, LON = 60.1699, 24.9384

# Define API parameters to fetch **current and future days**
API_PARAMS = {
    "latitude": LAT,
    "longitude": LON,
    "hourly": "temperature_2m,weather_code,relative_humidity_2m,precipitation,rain,snowfall,pressure_msl,wind_direction_10m",
    "forecast_days": 7,
    "timezone": "auto",
}

# Fetch data
response = requests.get(API_URL, params=API_PARAMS)
response.raise_for_status()
data = response.json()

# Process hourly weather data
hourly_data = data.get("hourly", {})
timestamps = [datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in hourly_data["time"]]
weather_codes = hourly_data["weather_code"]
temperatures = hourly_data["temperature_2m"]
wind_directions = hourly_data["wind_direction_10m"]

# Group by day
weather_by_day = collections.defaultdict(list)
temp_by_day = collections.defaultdict(list)
wind_by_day = collections.defaultdict(list)

for i, timestamp in enumerate(timestamps):
    day_str = timestamp.strftime("%Y-%m-%d")
    weather_by_day[day_str].append(weather_codes[i])
    temp_by_day[day_str].append(temperatures[i])
    wind_by_day[day_str].append(wind_directions[i])

# Compute the daily average wind direction
wind_avg = {
    day: sum(directions) / len(directions) for day, directions in wind_by_day.items()
}


# Compute the most frequent weather code and average temperature per day
processed_data = []
for day, codes in weather_by_day.items():
    most_frequent_weather = max(set(codes), key=codes.count)  # Most repeated weather
    avg_temp = sum(temp_by_day[day]) / len(temp_by_day[day])  # Average temperature
    processed_data.append((day, most_frequent_weather, avg_temp))

# Sort data chronologically
processed_data.sort(key=lambda x: x[0])

# Extract **today's data** and **future data separately**
today = datetime.utcnow().date()
processed_today = [
    entry
    for entry in processed_data
    if datetime.strptime(entry[0], "%Y-%m-%d").date() == today
]
processed_future = [
    entry
    for entry in processed_data
    if datetime.strptime(entry[0], "%Y-%m-%d").date() > today
]

# Merge today + future
if processed_today:
    processed_data_final = (
        processed_today + processed_future[:6]
    )  # Ensuring only 6 future days are included
else:
    processed_data_final = processed_future[
        :7
    ]  # If today’s data is missing, show all future days

# Extract wind direction for only the selected days in processed_data_final
wind_directions_final = [wind_avg.get(day, 0) for day, _, _ in processed_data_final]
print("Wind Directions Per Day:", wind_directions_final)

# Extract structured data
dates, weather_conditions, avg_temperatures = zip(*processed_data_final)
days_of_week = [datetime.strptime(date, "%Y-%m-%d").strftime("%A") for date in dates]

# ====== Step 2: Map Weather Codes to 3D Models ======
weather_mapping = {
    0: "Clear sky.obj",
    1: "Mainly clear.obj",
    2: "Partly cloudy.obj",
    3: "Overcast.obj",
    45: "Overcast.obj",  # Fog cases
    48: "Overcast.obj",
    51: "drizzle.obj",
    53: "drizzle.obj",
    55: "drizzle.obj",
    56: "drizzle.obj",
    57: "drizzle.obj",
    61: "rainy.obj",
    63: "rainy.obj",
    65: "rainy.obj",
    66: "rainy.obj",
    67: "rainy.obj",
    80: "rainy.obj",
    81: "rainy.obj",
    82: "rainy.obj",
    71: "snow.obj",
    73: "snow.obj",
    75: "snow.obj",
    77: "snow.obj",
    85: "snow.obj",
    86: "snow.obj",
    95: "thunderstorm.obj",
    96: "thunderstorm.obj",
    99: "thunderstorm.obj",
}

# ====== Step 3: Initialize Dashboard with 8 Columns (Today's Data + Future Days) ======
dashboard = lc.Dashboard(rows=9, columns=8, theme=lc.Themes.CyberSpace)

# ====== Step 4: Row 1 - Show Day Names & Dates ======
text_charts = []

# **Today's Section (Spanning Two Columns)**
chart = dashboard.ChartXY(row_index=0, column_index=0, column_span=2, row_span=2)
chart.set_title("").set_chart_background_image("Images/Stormclouds.jpg")
# chart.set_background_color(lc.Color(255, 255, 255, 128))
town_textbox = (
    chart.add_textbox("Helsinki, Finland", 0.5, 0.8)
    .set_text_font(42, weight="bold")
    .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
)
day_textbox = (
    chart.add_textbox(days_of_week[0], 0.5, 0.5)
    .set_text_font(46, weight="bold")
    .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
)
date_textbox = (
    chart.add_textbox(dates[0], 0.5, 0.2)
    .set_text_font(28, weight="bold")
    .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
)
text_charts.append((day_textbox, date_textbox))
chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    0, 1, stop_axis_after=True
)
chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    0, 1, stop_axis_after=True
)

# **Future Days (Shifted Right)**
for col in range(1, 7):
    chart = dashboard.ChartXY(row_index=0, column_index=col + 1)
    chart.set_title("")
    day_textbox = (
        chart.add_textbox(days_of_week[col], 0.5, 0.7)
        .set_text_font(25, weight="bold")
        .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
    )
    date_textbox = (
        chart.add_textbox(dates[col], 0.5, 0.4)
        .set_text_font(15, weight="bold")
        .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
    )
    text_charts.append((day_textbox, date_textbox))
    chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )

# ====== Step 5: Row 2 - Show 3D Weather Models ======
chart_3d_list = []
mesh_models = {}


# Function to Load a Mesh Model# ====== Fix: Correctly Map Weather Code to File Name ======
def load_mesh_model(file_name, is_arrow=False):
    """Load weather or arrow model from the Dataset folder."""

    # If loading the arrow, always use "arrow.obj"
    if is_arrow:
        obj_file = "arrow.obj"
    else:
        obj_file = weather_mapping.get(file_name, "Overcast.obj")  # Default to Overcast

    obj_path = f"Dataset/{obj_file}"

    if not os.path.exists(obj_path):
        print(f"Missing model file: {obj_path}")
        return None, None, None

    try:
        scene = trimesh.load(obj_path)
        mesh = (
            scene.dump(concatenate=True) if isinstance(scene, trimesh.Scene) else scene
        )
        vertices, indices, normals = (
            mesh.vertices.flatten().tolist(),
            mesh.faces.flatten().tolist(),
            mesh.vertex_normals.flatten().tolist(),
        )
        return vertices, indices, normals
    except Exception as e:
        print(f"Error loading {obj_file}: {e}")
        return None, None, None


# **Today's Section (Spanning Two Columns)**
chart_3d = dashboard.Chart3D(
    row_index=2, column_index=0, column_span=2, row_span=2
).set_title("")
chart_3d.get_default_x_axis().set_tick_strategy("Empty")
chart_3d.get_default_y_axis().set_tick_strategy("Empty")
chart_3d.get_default_z_axis().set_tick_strategy("Empty")
chart_3d.set_camera_location(0, 1, 5)
chart_3d_list.append(chart_3d)

# Load Model for Today's Weather
vertices, indices, normals = load_mesh_model(weather_conditions[0])
if vertices and indices and normals:
    model = chart_3d.add_mesh_model()
    model.set_model_geometry(vertices=vertices, indices=indices, normals=normals)
    model.set_scale(1).set_model_location(0, 0.45, 0)
    mesh_models[weather_conditions[0]] = model
else:
    print(f"Failed to load model for today's weather: {weather_conditions[0]}")

arrow_vertices, arrow_indices, arrow_normals = load_mesh_model("arrow", is_arrow=True)

if arrow_vertices and arrow_indices and arrow_normals:
    arrow_model = chart_3d.add_mesh_model().set_color(lc.Color("yellow"))
    arrow_model.set_model_geometry(
        vertices=arrow_vertices, indices=arrow_indices, normals=arrow_normals
    )
    arrow_model.set_scale(0.07)  # Slightly Smaller
    arrow_model.set_model_location(0, -0.65, 0)  # **Positioned Below Center**

    wind_direction = wind_directions_final[
        0
    ]  # Get the correct wind direction for today
    arrow_model.set_model_rotation(90, 300 - wind_direction, 0)  # Rotate Around Y-Axis


for col in range(1, 7):
    chart_3d = dashboard.Chart3D(
        row_index=1, column_index=col + 1, row_span=2
    ).set_title("")
    chart_3d.get_default_x_axis().set_tick_strategy("Empty")
    chart_3d.get_default_y_axis().set_tick_strategy("Empty")
    chart_3d.get_default_z_axis().set_tick_strategy("Empty")
    chart_3d.set_camera_location(0, 1, 5)
    chart_3d_list.append(chart_3d)

    # Load Model for Future Weather
    vertices, indices, normals = load_mesh_model(weather_conditions[col])
    if vertices and indices and normals:
        model = chart_3d.add_mesh_model()
        model.set_model_geometry(vertices=vertices, indices=indices, normals=normals)
        model.set_scale(1).set_model_location(0, 0.45, 0)
        mesh_models[weather_conditions[col]] = model
    else:
        print(f"Failed to load model for day {col + 1}: {weather_conditions[col]}")

    arrow_vertices, arrow_indices, arrow_normals = load_mesh_model(
        "arrow", is_arrow=True
    )
    if arrow_vertices and arrow_indices and arrow_normals:
        arrow_model = chart_3d.add_mesh_model().set_color(lc.Color("yellow"))
        arrow_model.set_model_geometry(
            vertices=arrow_vertices, indices=arrow_indices, normals=arrow_normals
        )
        arrow_model.set_scale(0.07)  # Slightly Smaller
        arrow_model.set_model_location(0, -0.65, 0)  # **Positioned Below Center**

        wind_direction = wind_directions_final[
            col
        ]  # Get the correct wind direction for today
        arrow_model.set_model_rotation(
            90, 300 - wind_direction, 0
        )  # Rotate Around Y-Axis


# ====== Step 6: Row 3 - Show Temperature Gauges ======
gauge_charts = []

chart_temp_today = dashboard.ChartXY(
    row_index=4, column_index=0, column_span=2, row_span=1
).set_title("Temperature Overview")

# **Extract Min and Max Temperatures from Today's Forecast**
today_temps = temp_by_day[dates[0]]
min_temp, max_temp = min(today_temps), max(today_temps)

# **Create Static High and Low Temperature Text Boxes**
high_temp_text = (
    chart_temp_today.add_textbox(f"High: {max_temp:.1f}°C", 0.5, 0.8)
    .set_text_font(14, weight="bold")
    .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
)
low_temp_text = (
    chart_temp_today.add_textbox(f"Low: {min_temp:.1f}°C", 0.5, 0.2)
    .set_text_font(14, weight="bold")
    .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
)

# **Create Dynamic Current Temperature Text Box**
current_temp_text = (
    chart_temp_today.add_textbox("Current: --°C", 0.5, 0.5)
    .set_text_font(18, weight="bold")
    .set_stroke(thickness=0, color=lc.Color(0, 0, 0, 0))
)

# **Remove Axis Lines and Labels**
chart_temp_today.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    0, 1, stop_axis_after=True
)
chart_temp_today.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    0, 1, stop_axis_after=True
)

# **Future Days**
for col in range(1, 7):
    gauge_chart = dashboard.GaugeChart(row_index=3, column_index=col + 1, row_span=2)
    gauge_chart.set_angle_interval(start=180, end=0).set_rounded_edges(
        False
    ).set_value_label_font(28).set_tick_font(25).set_needle_thickness(
        5
    ).set_needle_length(20)
    gauge_chart.set_title("Avg Temp (°C)").set_unit_label("(°C)").set_unit_label_font(
        14
    )
    gauge_chart.set_interval(start=-30, end=50).set_bar_thickness(3)
    gauge_chart.set_value(avg_temperatures[col]).set_value_decimals(0)
    gauge_charts.append(gauge_chart)

# ====== Step 8: Add Humidity Line Chart at the Bottom ======

# Create a new row for the humidity chart (Row 6)
chart_humidity = dashboard.ChartXY(
    row_index=5, column_index=0, column_span=3, row_span=4
)
chart_humidity.set_title("Humidity Changes Over the Week")

humidity_values = hourly_data["relative_humidity_2m"]

# Group humidity by day (to take average per day)
humidity_by_day = collections.defaultdict(list)

for i, timestamp in enumerate(timestamps):
    day_str = timestamp.strftime("%Y-%m-%d")
    humidity_by_day[day_str].append(humidity_values[i])

# Compute the daily average humidity
humidity_daily_avg = [
    sum(humidities) / len(humidities) for humidities in humidity_by_day.values()
]

# Extract days of the week for the x-axis
humidity_days_of_week = [
    datetime.strptime(day, "%Y-%m-%d").strftime("%A") for day in humidity_by_day.keys()
]

# Add Point Line Series for humidity
humidity_series = chart_humidity.add_point_line_series()
humidity_series.set_point_shape("circle").set_point_size(6).set_point_color(
    lc.Color("blue")
)
humidity_series.set_line_thickness(2).set_line_color(lc.Color("blue"))

# Add humidity data to the series
humidity_series.add(x=list(range(len(humidity_daily_avg))), y=humidity_daily_avg)

# Format X and Y Axes
x_axis = chart_humidity.get_default_x_axis()
y_axis = chart_humidity.get_default_y_axis()

x_axis.set_tick_strategy("Empty")
y_axis.set_title("Humidity (%)")

# Customize X-Axis to show day names
for i, label in enumerate(humidity_days_of_week):
    custom_tick_x = x_axis.add_custom_tick().set_tick_label_rotation(45)
    custom_tick_x.set_value(i)
    custom_tick_x.set_text(label)

# ====== Step 9: Add Precipitation Bar Chart ======
chart_precip = dashboard.BarChart(
    row_index=5, column_index=3, column_span=2, row_span=4
).set_value_label_display_mode("hidden")
chart_precip.set_title("Precipitation Forecast (mm)")

precip_by_day = collections.defaultdict(list)

for i, timestamp in enumerate(timestamps):
    day_str = timestamp.strftime("%Y-%m-%d")
    precip_by_day[day_str].append(hourly_data["precipitation"][i])

# Compute daily total precipitation
precip_daily_total = [sum(precip) for precip in precip_by_day.values()]

# Add data to Bar Chart
chart_precip.set_data(
    [
        {"category": day, "value": precip}
        for day, precip in zip(humidity_days_of_week, precip_daily_total)
    ]
)

# ====== Step 11: Add Air Pressure Line Chart ======
chart_pressure = dashboard.ChartXY(
    row_index=5, column_index=5, column_span=3, row_span=4
)
chart_pressure.set_title("Air Pressure Forecast Trends (hPa)")

# Process air pressure data
pressure_values = hourly_data["pressure_msl"]

pressure_by_day = collections.defaultdict(list)

for i, timestamp in enumerate(timestamps):
    day_str = timestamp.strftime("%Y-%m-%d")
    pressure_by_day[day_str].append(pressure_values[i])

# Compute the daily average air pressure
pressure_daily_avg = [
    sum(pressures) / len(pressures) for pressures in pressure_by_day.values()
]

# Extract days of the week for the x-axis
pressure_days_of_week = [
    datetime.strptime(day, "%Y-%m-%d").strftime("%A") for day in humidity_by_day.keys()
]

# Add Point Line Series for air pressure
pressure_series = chart_pressure.add_point_line_series()
pressure_series.set_point_shape("circle").set_point_size(6).set_point_color(
    lc.Color("blue")
)
pressure_series.set_line_thickness(2).set_line_color(lc.Color("blue"))

# Add air pressure data to the series
pressure_series.add(x=list(range(len(pressure_daily_avg))), y=pressure_daily_avg)

# Format X and Y Axes
x_axis = chart_pressure.get_default_x_axis()
y_axis = chart_pressure.get_default_y_axis()

x_axis.set_tick_strategy("Empty")
y_axis.set_title("Air Pressure (hPa)")

# Customize X-Axis to show day names
for i, label in enumerate(pressure_days_of_week):
    custom_tick_x = x_axis.add_custom_tick().set_tick_label_rotation(45)
    custom_tick_x.set_value(i)
    custom_tick_x.set_text(label)


######**Function to Fetch Real-Time Temperature**
def update_real_time_temperature():
    while True:
        try:
            real_time_response = requests.get(
                API_URL,
                params={
                    "latitude": LAT,
                    "longitude": LON,
                    "current": "temperature_2m",
                    "timezone": "auto",
                },
            )
            real_time_response.raise_for_status()
            real_time_data = real_time_response.json()

            if "current" in real_time_data:
                real_temp = real_time_data["current"]["temperature_2m"]
                current_temp_text.set_text(f"Current: {real_temp:.1f}°C")
                print(f"Real-time temperature: {real_temp:.1f}°C, date: {dates[0]}")

        except Exception as e:
            print(f"Real-time temperature update failed: {e}")

        time.sleep(0.1)


dashboard.open(live=True)
threading.Thread(target=update_real_time_temperature, daemon=True).start()
