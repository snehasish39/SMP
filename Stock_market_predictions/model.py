#Model architecture, compile, and training functions

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def build_lstm_model(input_shape):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_model(model, X_train, y_train, epochs=20, batch_size=32, val_split=0.1):
    history = model.fit(X_train, y_train, epochs=epochs,
                        batch_size=batch_size, validation_split=val_split)
    return history

