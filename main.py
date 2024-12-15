import streamlit as st
import pandas as pd
import requests
import datetime
import plotly.graph_objects as go

def get_current_temp(city, api_key):
  base_url = "http://api.openweathermap.org/data/2.5/weather?"
  complete_url = f"{base_url}appid={api_key}&q={city}&units=metric"
  response = requests.get(complete_url)
  data = response.json()

  if data["cod"] != 200:
    st.error(f"Ошибка: {data['message']}")
    return None

  return data["main"]["temp"], data["main"]["feels_like"], data["weather"][0]["icon"], data["weather"][0]["description"]

def validate_api_key(api_key):
    test_url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
    response = requests.get(test_url)
    if response.status_code == 200:
        return True
    else:
        return response.json().get("message", "Invalid API key Please see https://openweathermap.org/faq#error401 for more info.")

# API ключ OpenWeatherMap
api_key = "5d17cfddc212ca44869ba673d30088f4"

st.header("Step 0: Enter Your OpenWeatherMap API Key")
api_key_1 = st.text_input("API Key:", type="password")
if api_key_1:
    validation_result = validate_api_key(api_key_1)
    if validation_result == True:
        st.success("API key is valid! You can proceed.")
    else:
        st.error(f"Message: {validation_result}")
st.title("Weather Prediction")
st.header("Step 1: Upload CSV file")

# Загрузка файла
uploaded_file = st.file_uploader("Choose a file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of Uploaded Data:")
    st.write(df.head())

    # Проверка наличия колонки 'city'
    if 'city' not in df.columns:
        st.error("The uploaded file does not contain a 'city' column.")
    else:
        df['rolling_mean'] = df.groupby('city')['temperature'].transform(
            lambda x: x.rolling(window=30, center=True).mean())
        df['rolling_std'] = df.groupby('city')['temperature'].transform(
            lambda x: x.rolling(window=30, center=True).std())
        df['anomaly'] = (
            abs(df['temperature'] - df['rolling_mean']) > (2 * df['rolling_std']))

        st.header("Step 2: Choose a city")
        # Выбор города из уникальных значений
        selected_city = st.selectbox("Choose a city:", df['city'].unique())

        # Получение температуры
        if st.button("Get Temperature"):
            current_temperature, feels_like,  icon_code, weather_description = get_current_temp(selected_city, api_key)
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

            if current_temperature is not None:
                #st.success(f"Current temperature in {selected_city}: {current_temperature}°C")
                time = datetime.datetime.now()
                current_time = time.strftime("%H:%M:%S")
                st.header(f"{selected_city}: {current_temperature}°C")
                col1, col2 = st.columns([4, 2])

                with col1:
                    st.subheader(f"Feels like {feels_like}°C")
                    st.subheader(f"{weather_description}")

                with col2:  # Правая колонка для иконки
                    #st.subheader(f"{current_time}")
                    st.image(icon_url, width=150)
            city_data = df[df['city'] == selected_city]

            fig = go.Figure()

            # Добавляем график температуры
            fig.add_trace(go.Scatter(
                x=city_data['timestamp'],
                y=city_data['temperature'],
                mode='lines',
                name='Temperature',
                line=dict(color='royalblue')
            ))

            # Добавляем аномалии
            anomalies = city_data[city_data['anomaly']]
            fig.add_trace(go.Scatter(
                x=anomalies['timestamp'],
                y=anomalies['temperature'],
                mode='markers',
                name='Anomalies',
                marker=dict(color='orange', size=8)
            ))

            # Настройка графика
            fig.update_layout(
                title=f"Temperature in {selected_city} with Anomalies",
                xaxis_title="Date",
                yaxis_title="Temperature (°C)",
                template="plotly_white",
                legend=dict(
                    x=0.01, y=0.99,
                    bgcolor="rgba(255,255,255,0.5)",
                    bordercolor="Black",
                    borderwidth=1
                )
            )

            # Отображение графика в Streamlit
            st.plotly_chart(fig)
            st.header(f"Descriptive Statistics for {selected_city}")
            stats = city_data.groupby('season')['temperature'].agg(['mean', 'std', 'min', 'max']).reset_index()
            st.dataframe(stats)