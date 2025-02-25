import requests
import pandas as pd
import lightningchart as lc
import trimesh
import time
from datetime import datetime, timedelta
import pytz

# ─── Read License Key and Set Timezone ─────────────────────────────
with open(
    "D:/Computer Aplication/WorkPlacement/Projects/shared_variable.txt", "r"
) as f:
    mylicensekey = f.read().strip()
lc.set_license(mylicensekey)

local_tz = pytz.timezone("Europe/Helsinki")

# ─── API Parameters for Real-Time / Historical Data ───────────────
API_URL = "https://api.open-meteo.com/v1/forecast"
API_PARAMS = {
    "latitude": 60.1699,
    "longitude": 24.9384,
    "current": "temperature_2m,precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
    "wind_speed_10m,wind_direction_10m,relative_humidity_2m,pressure_msl,"
    "soil_temperature_0_to_7cm,soil_temperature_7_to_28cm,soil_temperature_28_to_100cm,soil_temperature_100_to_255cm,"
    "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,cloud_cover_low,cloud_cover_mid,cloud_cover_high",
    "hourly": "temperature_2m,precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
    "wind_speed_10m,wind_direction_10m,relative_humidity_2m,pressure_msl,"
    "soil_temperature_0_to_7cm,soil_temperature_7_to_28cm,soil_temperature_28_to_100cm,soil_temperature_100_to_255cm,"
    "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,cloud_cover_low,cloud_cover_mid,cloud_cover_high",
    "past_days": 1,
    "forecast_days": 0,  # only historical/current data here
    "timezone": "auto",
}


# ─── Function to Fetch Forecast Data (for Hourly Charts) ───────
def fetch_weather_data():
    params = {
        "latitude": 60.1699,
        "longitude": 24.9384,
        # Request forecast_days = 2 so that later hours (e.g. 00:00) are available.
        "hourly": "temperature_2m,weather_code,relative_humidity_2m,pressure_msl,wind_speed_10m,precipitation,snowfall",
        "past_days": 1,
        "forecast_days": 2,
        "timezone": "auto",
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        hourly_data = data.get("hourly", {})
        df = pd.DataFrame(hourly_data)
        # IMPORTANT: Assume the API time strings are in UTC;
        # convert them to local Helsinki time:
        df["Time"] = (
            pd.to_datetime(df["time"]).dt.tz_localize("UTC").dt.tz_convert(local_tz)
        )
        df.sort_values(by="Time", inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return pd.DataFrame()


# ─── Weather Mapping ──────────────────────────────────────────────
weather_mapping = {
    0: "Clear sky.obj",
    1: "Mainly clear.obj",
    2: "Partly cloudy.obj",
    3: "Overcast.obj",
    45: "Overcast.obj",  # Fog cases
    48: "Overcast.obj",
    51: "drizzle.obj",  # Drizzle cases
    53: "drizzle.obj",
    55: "drizzle.obj",
    56: "drizzle.obj",
    57: "drizzle.obj",
    61: "rainy.obj",  # Rain cases
    63: "rainy.obj",
    65: "rainy.obj",
    66: "rainy.obj",
    67: "rainy.obj",
    80: "rainy.obj",
    81: "rainy.obj",
    82: "rainy.obj",
    71: "snow.obj",  # Snow/Snowfall cases
    73: "snow.obj",
    75: "snow.obj",
    77: "snow.obj",
    85: "snow.obj",
    86: "snow.obj",
    95: "rainy.obj",  # Thunderstorm
    96: "rainy.obj",
    99: "rainy.obj",
}

# ─── Create Dashboard ─────────────────────────────────────────────
dashboard = lc.Dashboard(rows=14, columns=12, theme=lc.Themes.CyberSpace)

# ─── Main 3D Weather Visualization (Current) ──────────────────────
chart_3d = dashboard.Chart3D(
    row_index=0, column_index=8, row_span=4, column_span=2
).set_title("Current Weather Condition")
chart_3d.get_default_x_axis().set_tick_strategy("Empty")
chart_3d.get_default_y_axis().set_tick_strategy("Empty")
chart_3d.get_default_z_axis().set_tick_strategy("Empty")
chart_3d.set_camera_location(0, 1, 5)

mesh_models = {}


def load_mesh_model(obj_filename):
    obj_path = f"Dataset/{obj_filename}"
    scene = trimesh.load(obj_path)
    if isinstance(scene, trimesh.Scene):
        mesh = scene.dump(concatenate=True)
    else:
        mesh = scene
    vertices = mesh.vertices.flatten().tolist()
    indices = mesh.faces.flatten().tolist()
    normals = mesh.vertex_normals.flatten().tolist()
    return vertices, indices, normals


unique_weather_codes = [
    0,
    1,
    2,
    3,
    45,
    48,
    51,
    53,
    55,
    56,
    57,
    61,
    63,
    65,
    66,
    67,
    71,
    73,
    75,
    77,
    80,
    81,
    82,
    85,
    86,
    95,
    96,
    99,
]
for code in unique_weather_codes:
    obj_file = weather_mapping.get(code, None)
    if obj_file and obj_file not in mesh_models:
        vertices, indices, normals = load_mesh_model(obj_file)
        model = chart_3d.add_mesh_model()
        model.set_model_geometry(vertices=vertices, indices=indices, normals=normals)
        model.set_scale(1)
        model.set_model_location(8, 0, 0)
        mesh_models[obj_file] = model


def transition_weather(prev_obj, new_obj):
    if prev_obj == new_obj:
        return
    transition_steps = 40
    delay = 0.05
    prev_model = mesh_models.get(prev_obj, None)
    new_model = mesh_models.get(new_obj, None)
    if prev_model:
        for step in range(transition_steps):
            prev_model.set_model_location(0 - (step / transition_steps), 0, 0)
            time.sleep(delay)
        prev_model.set_model_location(-8, 0, 0)
    if new_model:
        new_model.set_model_location(2, 0, 0)
        for step in range(transition_steps):
            new_model.set_model_location(2 - (step / transition_steps * 2), 0, 0)
            time.sleep(delay)


def fetch_past_weather():
    response = requests.get(API_URL, params=API_PARAMS)
    response.raise_for_status()
    data = response.json()
    hourly_data = data.get("hourly", {})
    df = pd.DataFrame(hourly_data)
    df["Time"] = pd.to_datetime(df["time"])
    today = datetime.utcnow().date()
    df = df[df["Time"].dt.date < today]
    return df


def get_weather_obj(weather_code):
    if weather_code in [0]:
        return "Clear sky.obj"
    elif weather_code in [1]:
        return "Mainly clear.obj"
    elif weather_code in [2]:
        return "Partly cloudy.obj"
    elif weather_code in [3]:
        return "Overcast.obj"
    elif weather_code in [45, 48]:
        return "Overcast.obj"
    elif weather_code in [51, 53, 55, 56, 57]:
        return "drizzle.obj"
    elif weather_code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "rainy.obj"
    elif weather_code in [71, 73, 75, 77, 85, 86]:
        return "snow.obj"
    elif weather_code in [95, 96, 99]:
        return "thunderstorm.obj"
    else:
        return None


def fetch_real_time_weather():
    response = requests.get(API_URL, params=API_PARAMS)
    response.raise_for_status()
    return response.json()["current"]


# ─── Other Dashboard Charts (Polar, Gauge, Bar, Multi-Line) ───────
polar_chart = dashboard.PolarChart(
    column_index=0, row_index=0, row_span=4, column_span=4
)
polar_chart.set_title("Current Wind Direction & Speed")
legend = polar_chart.add_legend(title="Wind Speed (km/h)")
sectors = 12
annuli = 5
heatmap_series = polar_chart.add_heatmap_series(sectors=sectors, annuli=annuli)
heatmap_series.set_palette_coloring(
    steps=[
        {"value": 0, "color": lc.Color("blue")},
        {"value": 5, "color": lc.Color("green")},
        {"value": 10, "color": lc.Color("yellow")},
        {"value": 15, "color": lc.Color("red")},
    ],
    look_up_property="value",
    interpolate=True,
)
legend.add(heatmap_series)

gauge_chart = dashboard.GaugeChart(
    column_index=10, row_index=0, row_span=4, column_span=2
)
gauge_chart.set_angle_interval(start=180, end=0).set_rounded_edges(False)
gauge_chart.set_title("Current Temperature (°C)").set_unit_label(
    "(°C)"
).set_unit_label_font(20, weight="bold").set_value_label_font(30, weight="bold")
gauge_chart.set_interval(start=-30, end=50).set_needle_length(30)
gauge_chart.set_value(0).set_bar_thickness(15).set_needle_thickness(7)

bar_chart_temp = dashboard.BarChart(
    column_index=0, row_index=4, row_span=5, column_span=4
)
bar_chart_temp.set_title("Current Soil Temperature (°C)")
soil_categories = ["0 to 7", "7 to 28", "28 to 100", "100 to 255"]
bar_chart_temp.set_data(
    [{"category": d, "value": 0} for d in soil_categories]
).set_sorting("disabled")
bar_chart_temp.set_palette_colors(
    steps=[
        {"value": -10, "color": lc.Color("red")},
        {"value": 0, "color": lc.Color("orange")},
        {"value": 10, "color": lc.Color("yellow")},
        {"value": 20, "color": lc.Color("green")},
    ]
)

bar_chart_moisture = dashboard.BarChart(
    column_index=0, row_index=9, row_span=5, column_span=4
)
bar_chart_moisture.set_title("Current Soil Moisture m³/m³")
moisture_categories = ["0 to 7", "7 to 28", "28 to 100", "100 to 255"]
bar_chart_moisture.set_data(
    [{"category": d, "value": 0} for d in moisture_categories]
).set_sorting("disabled")
bar_chart_moisture.set_palette_colors(
    steps=[
        {"value": 0, "color": lc.Color("red")},
        {"value": 0.5, "color": lc.Color("orange")},
        {"value": 0.75, "color": lc.Color("yellow")},
        {"value": 1, "color": lc.Color("green")},
    ]
)

# NEW: Cloud Coverage Bar Chart
bar_chart_cloud = dashboard.BarChart(
    row_index=0, column_index=4, row_span=4, column_span=4, vertical=False
)
bar_chart_cloud.set_title("Current Cloud Coverage (%)")
cloud_categories = ["Total", "Low", "Mid", "High"]
bar_chart_cloud.set_data(
    [{"category": cat, "value": 0} for cat in cloud_categories]
).set_sorting("disabled")
bar_chart_cloud.set_palette_colors(
    steps=[
        {"value": 0, "color": lc.Color("blue")},
        {"value": 0.25, "color": lc.Color("cyan")},
        {"value": 0.50, "color": lc.Color("green")},
        {"value": 0.75, "color": lc.Color("yellow")},
        {"value": 0.100, "color": lc.Color("red")},
    ],
    look_up_property="x",
)

line_chart = dashboard.ChartXY(column_index=4, row_index=4, row_span=4, column_span=8)
line_chart.set_title("Environmental Data Trends")
line_chart.get_default_y_axis().dispose()
line_chart.get_default_x_axis().set_tick_strategy("DateTime")
legend_line = line_chart.add_legend()
weather_features = [
    "Wind Speed (km/h)",
    "Humidity (%)",
    "Pressure (hPa)",
    "Precipitation (mm)",
]
series_dict = {}
for i, feature in enumerate(weather_features):
    axis_y = line_chart.add_y_axis(stack_index=i)
    series = line_chart.add_line_series(y_axis=axis_y, data_pattern="ProgressiveX")
    series.set_name(feature)
    series_dict[feature] = series
    legend_line.add(series)

# ─── Additional Forecast / Alert / Hourly Forecast Charts ─────────
# (Forecast title and cloud model remain as in your original code.)
forcasting_text = dashboard.ChartXY(
    row_index=8, column_index=4, row_span=1, column_span=2
).set_title("")
forcasting_text.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    0, 1, stop_axis_after=True
)
forcasting_text.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    0, 1, stop_axis_after=True
)
forcasting_text.add_textbox("Hourly Weather Forecast", 0.5, 0.5).set_text_font(
    "20", weight="bold"
).set_stroke(thickness=0, color=lc.Color("black"))

chart_3d_weather = dashboard.Chart3D(
    row_index=9, column_index=4, row_span=1, column_span=1
).set_title("")
object_weather = trimesh.load(
    "D:/Computer Aplication/WorkPlacement/Projects/Project19/Weekly dash/cloud.obj"
)
chart_3d_weather.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_weather.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_weather.get_default_z_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_weather.set_camera_location(0, 1, 5)
vertices_weather = object_weather.vertices.flatten().tolist()
indices_weather = object_weather.faces.flatten().tolist()
normals_weather = object_weather.vertex_normals.flatten().tolist()
model_weather = chart_3d_weather.add_mesh_model().set_color(lc.Color("white"))
model_weather.set_model_geometry(
    vertices=vertices_weather, indices=indices_weather, normals=normals_weather
)
model_weather.set_scale(0.006).set_model_location(1, 0.3, 0).set_model_rotation(0, 0, 0)

chart_text_weather = dashboard.ChartXY(
    row_index=9, column_index=5, row_span=1, column_span=1
).set_title("")
chart_text_weather.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_text_weather.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_text_weather.add_textbox("Weather", 0.5, 0.5).set_text_font(
    "20", weight="bold"
).set_stroke(thickness=0, color=lc.Color("black"))

# Alert Chart (3D icon for visual alert)
chart_3d_alert = dashboard.Chart3D(
    row_index=10, column_index=4, row_span=1, column_span=1
).set_title("")
object_alert = trimesh.load(
    "D:/Computer Aplication/WorkPlacement/Projects/Project19/Weekly dash/alert.obj"
)
chart_3d_alert.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_alert.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_alert.get_default_z_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_alert.set_camera_location(0, 1, 5)
vertices_alert = object_alert.vertices.flatten().tolist()
indices_alert = object_alert.faces.flatten().tolist()
normals_alert = object_alert.vertex_normals.flatten().tolist()
model_alert = chart_3d_alert.add_mesh_model().set_color(lc.Color("red"))
model_alert.set_model_geometry(
    vertices=vertices_alert, indices=indices_alert, normals=normals_alert
)
model_alert.set_scale(1.5).set_model_location(1, 0.3, 0).set_model_rotation(90, 0, 0)
chart_alert_alert = dashboard.ChartXY(
    row_index=10, column_index=5, row_span=1, column_span=1
).set_title("")
chart_alert_alert.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_alert.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_alert.add_textbox("Alert", 0.5, 0.5).set_text_font(
    "20", weight="bold"
).set_stroke(thickness=0, color=lc.Color("black"))

# Temperature Chart (3D icon)
chart_3d_temp = dashboard.Chart3D(
    row_index=11, column_index=4, row_span=1, column_span=1
).set_title("")
object_temp = trimesh.load(
    "D:/Computer Aplication/WorkPlacement/Projects/Project19/Weekly dash/Snowflake.obj"
)
chart_3d_temp.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_temp.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_temp.get_default_z_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_temp.set_camera_location(0, 1, 5)
vertices_temp = object_temp.vertices.flatten().tolist()
indices_temp = object_temp.faces.flatten().tolist()
normals_temp = object_temp.vertex_normals.flatten().tolist()
model_temp = chart_3d_temp.add_mesh_model().set_color(lc.Color("white"))
model_temp.set_model_geometry(
    vertices=vertices_temp, indices=indices_temp, normals=normals_temp
)
model_temp.set_scale(0.4).set_model_location(1, 0.3, 0).set_model_rotation(90, 0, 0)
chart_alert_temp = dashboard.ChartXY(
    row_index=11, column_index=5, row_span=1, column_span=1
).set_title("")
chart_alert_temp.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_temp.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_temp.add_textbox("Temperature", 0.5, 0.5).set_text_font(
    "20", weight="bold"
).set_stroke(thickness=0, color=lc.Color("black"))

# Humidity Chart (3D icon)
chart_3d_humidity = dashboard.Chart3D(
    row_index=12, column_index=4, row_span=1, column_span=1
).set_title("")
object_humidity = trimesh.load(
    "D:/Computer Aplication/WorkPlacement/Projects/Project19/Weekly dash/humidity.obj"
)
chart_3d_humidity.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_humidity.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_humidity.get_default_z_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_humidity.set_camera_location(0, 1, 5)
vertices_humidity = object_humidity.vertices.flatten().tolist()
indices_humidity = object_humidity.faces.flatten().tolist()
normals_humidity = object_humidity.vertex_normals.flatten().tolist()
model_humidity = chart_3d_humidity.add_mesh_model().set_color(lc.Color(102, 178, 255))
model_humidity.set_model_geometry(
    vertices=vertices_humidity, indices=indices_humidity, normals=normals_humidity
)
model_humidity.set_scale(0.4).set_model_location(1, 0.3, 0).set_model_rotation(0, 0, 0)
chart_alert_humidity = dashboard.ChartXY(
    row_index=12, column_index=5, row_span=1, column_span=1
).set_title("")
chart_alert_humidity.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_humidity.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_humidity.add_textbox("Humidity", 0.5, 0.5).set_text_font(
    "20", weight="bold"
).set_stroke(thickness=0, color=lc.Color("black"))

# Pressure Chart (3D icon)
chart_3d_pressure = dashboard.Chart3D(
    row_index=13, column_index=4, row_span=1, column_span=1
).set_title("")
object_pressure = trimesh.load(
    "D:/Computer Aplication/WorkPlacement/Projects/Project19/Weekly dash/pressure.obj"
)
chart_3d_pressure.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_pressure.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_pressure.get_default_z_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_3d_pressure.set_camera_location(0, 1, 5)
vertices_pressure = object_pressure.vertices.flatten().tolist()
indices_pressure = object_pressure.faces.flatten().tolist()
normals_pressure = object_pressure.vertex_normals.flatten().tolist()
model_pressure = chart_3d_pressure.add_mesh_model().set_color(lc.Color("yellow"))
model_pressure.set_model_geometry(
    vertices=vertices_pressure, indices=indices_pressure, normals=normals_pressure
)
model_pressure.set_scale(0.7).set_model_location(1, 0.3, 0).set_model_rotation(
    90, 0, 30
)
chart_alert_pressure = dashboard.ChartXY(
    row_index=13, column_index=5, row_span=1, column_span=1
).set_title("")
chart_alert_pressure.get_default_x_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_pressure.get_default_y_axis().set_tick_strategy("Empty").set_interval(
    start=0, end=1, stop_axis_after=True
)
chart_alert_pressure.add_textbox("Pressure", 0.5, 0.5).set_text_font(
    "20", weight="bold"
).set_stroke(thickness=0, color=lc.Color("black"))

# ─── Hourly Forecast Charts (6 charts) ───────────────────────────
hourly_charts = []
hourly_textboxes = []
hourly_3d_charts = []
hourly_3d_models = []
for i in range(6):
    chart = dashboard.ChartXY(
        row_index=8, column_index=6 + i, row_span=1, column_span=1
    ).set_title("")
    chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    textbox = (
        chart.add_textbox("Loading...", 0.5, 0.5)
        .set_text_font(18, weight="bold")
        .set_stroke(thickness=0, color=lc.Color("black"))
    )
    hourly_charts.append(chart)
    hourly_textboxes.append(textbox)
for i in range(6):
    chart = dashboard.Chart3D(
        row_index=9, column_index=6 + i, row_span=1, column_span=1
    ).set_title("")
    chart.get_default_x_axis().set_tick_strategy("Empty")
    chart.get_default_y_axis().set_tick_strategy("Empty")
    chart.get_default_z_axis().set_tick_strategy("Empty")
    chart.set_camera_location(0, 1, 5)
    model = chart.add_mesh_model()
    model.set_model_geometry(vertices=[], indices=[], normals=[])  # start empty
    model.set_scale(10).set_model_location(8, 0, 0)  # offscreen initially
    hourly_3d_charts.append(chart)
    hourly_3d_models.append(model)

# ─── Hourly Alert Charts (6 text boxes) ───────────────────────────
hourly_alert_charts = []
hourly_alert_textboxes = []
for i in range(6):
    chart = dashboard.ChartXY(
        row_index=10, column_index=6 + i, row_span=1, column_span=1
    ).set_title("")
    chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    textbox = (
        chart.add_textbox("-", 0.5, 0.5)
        .set_text_font(18, weight="bold")
        .set_stroke(thickness=0, color=lc.Color("black"))
    )
    hourly_alert_charts.append(chart)
    hourly_alert_textboxes.append(textbox)

# ─── Hourly Temperature Charts (6 text boxes) ─────────────────────
hourly_temperature_charts = []
hourly_temperature_textboxes = []
for i in range(6):
    chart = dashboard.ChartXY(
        row_index=11, column_index=6 + i, row_span=1, column_span=1
    ).set_title("")
    chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    textbox = (
        chart.add_textbox("0°C", 0.5, 0.5)
        .set_text_font(18, weight="bold")
        .set_stroke(thickness=0, color=lc.Color("black"))
    )
    hourly_temperature_charts.append(chart)
    hourly_temperature_textboxes.append(textbox)

# ─── Hourly Humidity Charts (6 text boxes) ─────────────────────────
hourly_humidity_charts = []
hourly_humidity_textboxes = []
for i in range(6):
    chart = dashboard.ChartXY(
        row_index=12, column_index=6 + i, row_span=1, column_span=1
    ).set_title("")
    chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    textbox = (
        chart.add_textbox("0%", 0.5, 0.5)
        .set_text_font(18, weight="bold")
        .set_stroke(thickness=0, color=lc.Color("black"))
    )
    hourly_humidity_charts.append(chart)
    hourly_humidity_textboxes.append(textbox)

# ─── Hourly Pressure Charts (6 text boxes) ─────────────────────────
hourly_pressure_charts = []
hourly_pressure_textboxes = []
for i in range(6):
    chart = dashboard.ChartXY(
        row_index=13, column_index=6 + i, row_span=1, column_span=1
    ).set_title("")
    chart.get_default_x_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    chart.get_default_y_axis().set_tick_strategy("Empty").set_interval(
        0, 1, stop_axis_after=True
    )
    textbox = (
        chart.add_textbox("0 hPa", 0.5, 0.5)
        .set_text_font(18, weight="bold")
        .set_stroke(thickness=0, color=lc.Color("black"))
    )
    hourly_pressure_charts.append(chart)
    hourly_pressure_textboxes.append(textbox)


# ─── Update Function for Next 6 Hours Forecast (and alerts) ───────
def update_next_6_hours(weather_df, current_time):
    print("🔍 Debugging: Current Time:", current_time.strftime("%Y-%m-%d %H:%M"))
    # Use current_time (without adding an extra hour) as the lower bound.
    next_hours = weather_df.loc[weather_df["Time"] >= current_time].head(6)
    if next_hours.empty:
        print("⚠️ Warning: No future data available in weather_df!")
        return
    next_times = list(next_hours["Time"])
    while len(next_times) < 6:
        next_times.append(next_times[-1] + timedelta(hours=1))
    print("✅ Next 6 Hours:", [t.strftime("%H:%M") for t in next_times])
    # Update forecast time text boxes
    for i, text_box in enumerate(hourly_textboxes):
        text_box.set_text(next_times[i].strftime("%H:%M"))
    # Update Alert, Temperature, Humidity, and Pressure text boxes
    for i, forecast in enumerate(next_hours.to_dict("records")):
        # Check for missing data; if missing, set to "-"
        if forecast.get("temperature_2m") is None:
            hourly_alert_textboxes[i].set_text("-")
            hourly_temperature_textboxes[i].set_text("-")
            hourly_humidity_textboxes[i].set_text("-")
            hourly_pressure_textboxes[i].set_text("-")
        else:
            # Alerts:
            wind_speed = forecast.get("wind_speed_10m", 0)
            precipitation = forecast.get("precipitation", 0)
            snowfall = forecast.get("snowfall", 0)
            temperature = forecast.get("temperature_2m", 0)
            alert_messages = []
            if wind_speed > 50:
                alert_messages.append("High Wind Alert")
            if precipitation > 10:
                alert_messages.append("Heavy Rain Alert")
            if snowfall > 5:
                alert_messages.append("Snowfall Alert")
            if temperature > 35 or temperature < -10:
                alert_messages.append("Extreme Temp Alert")
            alert_text = ", ".join(alert_messages) if alert_messages else "-"
            hourly_alert_textboxes[i].set_text(alert_text)
            # Temperature:
            temp_text = f"{temperature:.1f}°C"
            hourly_temperature_textboxes[i].set_text(temp_text)
            # Humidity:
            humidity = forecast.get("relative_humidity_2m", 0)
            humidity_text = f"{humidity:.1f}%"
            hourly_humidity_textboxes[i].set_text(humidity_text)
            # Pressure:
            pressure = forecast.get("pressure_msl", 0)
            pressure_text = f"{pressure:.1f} hPa"
            hourly_pressure_textboxes[i].set_text(pressure_text)
    # Update 3D Weather Models
    for i, forecast in enumerate(next_hours.to_dict("records")):
        weather_code = forecast.get("weather_code", None)
        obj_file = weather_mapping.get(weather_code, None)
        if obj_file:
            vertices, indices, normals = load_mesh_model(obj_file)
            if vertices:
                hourly_3d_models[i].set_model_geometry(
                    vertices=vertices, indices=indices, normals=normals
                )
                hourly_3d_models[i].set_model_location(0, 0, 0)
            else:
                hourly_3d_models[i].set_model_location(8, 0, 0)
        else:
            hourly_3d_models[i].set_model_location(8, 0, 0)


# ─── Synchronized Forecast Generator ─────────────────────────────
def forecast_generator():
    weather_df = fetch_weather_data()
    if weather_df.empty:
        return
    # Compute forecast_start as the current hour (rounded down)
    forecast_start = datetime.now(local_tz).replace(minute=0, second=0, microsecond=0)
    current_time = forecast_start
    # Loop until the current rounded hour is reached (this generator is used during historical playback)
    while current_time < datetime.now(local_tz).replace(
        minute=0, second=0, microsecond=0
    ):
        update_next_6_hours(weather_df, current_time)
        yield current_time
        current_time += timedelta(hours=1)
        time.sleep(1)  # sync delay (adjust as needed)
    update_next_6_hours(weather_df, current_time)
    yield current_time


# ─── Open the Dashboard and Create the Forecast Generator ─────
dashboard.open(live=True)
forecast_gen = forecast_generator()

# ─── Process Historical Weather Data, Stepping Forecast Updates Synchronously ─
past_weather_df = fetch_past_weather()
past_weather_df["Time"] = (
    pd.to_datetime(past_weather_df["time"])
    .dt.tz_localize("UTC")
    .dt.tz_convert("Europe/Helsinki")
)
past_weather_df["Timestamp"] = past_weather_df["Time"].astype("int64") // 10**6
print("Filtered past weather data:", past_weather_df)

previous_obj = None
previous_weather_code = None

# Fetch forecast data once for historical playback
historical_forecast_df = fetch_weather_data()

for _, row in past_weather_df.iterrows():
    timestamp = row["Timestamp"]
    weather_code = row["weather_code"]
    wind_speed = row["wind_speed_10m"]
    wind_direction = row["wind_direction_10m"]
    percipitation = row["precipitation"]
    temperature = row["temperature_2m"]
    humidity = row["relative_humidity_2m"]
    pressure = row["pressure_msl"]
    soil_temp = [
        row["soil_temperature_0_to_7cm"],
        row["soil_temperature_7_to_28cm"],
        row["soil_temperature_28_to_100cm"],
        row["soil_temperature_100_to_255cm"],
    ]
    soil_moisture = [
        row["soil_moisture_0_to_7cm"],
        row["soil_moisture_7_to_28cm"],
        row["soil_moisture_28_to_100cm"],
        row["soil_moisture_100_to_255cm"],
    ]
    cloud_cover_dict = [
        row["cloud_cover"],
        row["cloud_cover_low"],
        row["cloud_cover_mid"],
        row["cloud_cover_high"],
    ]

    print(f"Historical Time: {row['Time']}")
    print(f"Cloud Cover: {cloud_cover_dict}")
    if weather_code != previous_weather_code:
        new_obj = weather_mapping.get(weather_code, None)
        transition_weather(previous_obj, new_obj)
        previous_obj = new_obj
        previous_weather_code = weather_code
        print(f"Updated weather object to: {new_obj}")
    gauge_chart.set_value(temperature)
    intensity_values = [[0] * sectors for _ in range(annuli)]
    sector_index = int((wind_direction / 360) * sectors) % sectors
    annulus_index = min(int(wind_speed // 3), annuli - 1)
    intensity_values[annulus_index][sector_index] += wind_speed
    heatmap_series.invalidate_intensity_values(intensity_values)
    bar_chart_temp.set_data(
        [{"category": soil_categories[i], "value": soil_temp[i]} for i in range(4)]
    )
    bar_chart_moisture.set_data(
        [
            {"category": moisture_categories[i], "value": soil_moisture[i]}
            for i in range(4)
        ]
    )
    bar_chart_cloud.set_data(
        [
            {"category": cloud_categories[i], "value": cloud_cover_dict[i]}
            for i in range(4)
        ]
    )
    for feature, series in series_dict.items():
        if feature == "Wind Speed (km/h)":
            series.add([timestamp], [wind_speed])
        elif feature == "Humidity (%)":
            series.add([timestamp], [humidity])
        elif feature == "Pressure (hPa)":
            series.add([timestamp], [pressure])
        elif feature == "Precipitation (mm)":
            series.add([timestamp], [percipitation])

    # For historical playback, update the forecast row based on the current historical row's time.
    # Compute the forecast start as the historical row's time rounded down to the hour.
    historical_time = row["Time"]
    historical_forecast_start = historical_time.replace(
        minute=0, second=0, microsecond=0
    )
    update_next_6_hours(historical_forecast_df, historical_forecast_start)
    print(
        f"Forecast updated for historical time: {historical_forecast_start.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    time.sleep(1)  # main loop delay


print("Switching to real-time weather updates...")

# ─── Real-Time Weather Updates ───────────────────────────────
# ─── Real-Time Weather Updates ───────────────────────────────
while True:
    # Fetch current weather data from the "current" part
    real_time_data = fetch_real_time_weather()
    # Get the actual current time (with minutes and seconds)
    current = datetime.now(local_tz)
    real_time_timestamp = int(current.timestamp() * 1000)

    # Also fetch hourly forecast data (which contains cloud_cover fields)
    rt_weather_df = fetch_weather_data()
    # Find the forecast row corresponding to the current hour
    current_hour = current.replace(minute=0, second=0, microsecond=0)
    current_row = rt_weather_df[rt_weather_df["Time"] == current_hour]
    if current_row.empty:
        # If no exact match is found, choose the closest (for example, the first row)
        current_row = rt_weather_df.iloc[[0]]
    try:
        cloud_cover = float(current_row.iloc[0]["cloud_cover"])
        cloud_cover_low = float(current_row.iloc[0]["cloud_cover_low"])
        cloud_cover_mid = float(current_row.iloc[0]["cloud_cover_mid"])
        cloud_cover_high = float(current_row.iloc[0]["cloud_cover_high"])
    except Exception:
        cloud_cover = cloud_cover_low = cloud_cover_mid = cloud_cover_high = 0

    # Update the cloud coverage bar chart using these values
    bar_chart_cloud.set_data(
        [
            {"category": "Total", "value": cloud_cover},
            {"category": "Low", "value": cloud_cover_low},
            {"category": "Mid", "value": cloud_cover_mid},
            {"category": "High", "value": cloud_cover_high},
        ]
    )

    # Also update the forecast row continuously using interpolation
    real_time_weather_df = fetch_weather_data()
    update_next_6_hours(real_time_weather_df, current)

    # Check for a change in weather code and update 3D model accordingly
    if real_time_data["weather_code"] != previous_weather_code:
        new_obj = get_weather_obj(real_time_data["weather_code"])
        transition_weather(previous_obj, new_obj)
        previous_obj = new_obj
        previous_weather_code = real_time_data["weather_code"]

    # Update soil temperature and moisture
    soil_temp_real = [
        real_time_data["soil_temperature_0_to_7cm"],
        real_time_data["soil_temperature_7_to_28cm"],
        real_time_data["soil_temperature_28_to_100cm"],
        real_time_data["soil_temperature_100_to_255cm"],
    ]
    soil_moisture_real = [
        real_time_data["soil_moisture_0_to_7cm"],
        real_time_data["soil_moisture_7_to_28cm"],
        real_time_data["soil_moisture_28_to_100cm"],
        real_time_data["soil_moisture_100_to_255cm"],
    ]

    # Update the temperature gauge
    new_temperature = real_time_data["temperature_2m"]
    gauge_chart.set_value(new_temperature)

    # Update wind speed and direction (polar heatmap)
    wind_speed = real_time_data["wind_speed_10m"]
    wind_direction = real_time_data["wind_direction_10m"]
    sector_index = int((wind_direction / 360) * sectors) % sectors
    annulus_index = min(int(wind_speed // 3), annuli - 1)
    intensity_values = [[0] * sectors for _ in range(annuli)]
    intensity_values[annulus_index][sector_index] = wind_speed
    heatmap_series.invalidate_intensity_values(intensity_values)

    # Update the multi-line charts with current data
    series_dict["Wind Speed (km/h)"].add([real_time_timestamp], [wind_speed])
    series_dict["Humidity (%)"].add(
        [real_time_timestamp], [real_time_data["relative_humidity_2m"]]
    )
    series_dict["Pressure (hPa)"].add(
        [real_time_timestamp], [real_time_data["pressure_msl"]]
    )
    series_dict["Precipitation (mm)"].add(
        [real_time_timestamp], [real_time_data["precipitation"]]
    )
    line_chart.get_default_x_axis().fit()

    # Update soil data bar charts
    bar_chart_temp.set_data(
        [{"category": soil_categories[i], "value": soil_temp_real[i]} for i in range(4)]
    )
    bar_chart_moisture.set_data(
        [
            {"category": moisture_categories[i], "value": soil_moisture_real[i]}
            for i in range(4)
        ]
    )

    print(
        f"Real-Time Update at {current.strftime('%Y-%m-%d %H:%M:%S')} | Temp: {new_temperature}°C, Wind: {wind_speed} km/h"
    )
    time.sleep(30)  # Wait 30 seconds before the next update
