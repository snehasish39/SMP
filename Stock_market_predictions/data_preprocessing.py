#Data collection and sequence creation functions
import numpy as np
import yfinance as yf
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

csv_file = "/Users/snehasish/Documents/archive/stocks/AAME.csv"
def load_csv_data(csv_path):
    df = pd.read_csv(csv_path)
    return df

def preprocess_data(df):
    close_prices = df['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(close_prices)
    return data_scaled, scaler

def create_sequences(data_scaled, seq_length=60):
    X, y = [], []
    for i in range(seq_length, len(data_scaled)):
        X.append(data_scaled[i-seq_length:i, 0])
        y.append(data_scaled[i, 0])
    return np.array(X), np.array(y)
