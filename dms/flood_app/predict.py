import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from flood_app.models import WeatherData, FloodPrediction
import datetime

def train_predict_model():
    data = WeatherData.objects.all().values()
    df = pd.DataFrame(list(data))
    if df.empty:
        return

    X = df[['precipitation', 'temperature', 'humidity']]
    df['flood_risk'] = np.where(df['precipitation'] > 50, 1, 0)
    y = df['flood_risk']

    model = LinearRegression()
    model.fit(X, y)

    current_data = df.tail(1)[['precipitation', 'temperature', 'humidity']].values
    for days_ahead in range(1, 8):
        future_date = datetime.datetime.now() + datetime.timedelta(days=days_ahead)
        prediction = model.predict(current_data)
        probability = min(max(prediction[0], 0), 1)
        severity = int(probability * 5) or 1
        FloodPrediction.objects.update_or_create(
            location=df['location'].iloc[-1],
            predicted_date=future_date,
            defaults={'probability': probability, 'severity_level': severity}
        )