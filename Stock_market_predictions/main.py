from data_preprocessing import load_csv_data, preprocess_data, create_sequences
from model import build_lstm_model, train_model
from evaluates import predict, plot_predictions  # change 'evaluates' to the actual filename

if __name__ == '__main__':
    # Parameters
    SEQ_LEN = 60
    csv_file = "/Users/snehasish/Documents/archive/stocks/AAME.csv"  # path to your CSV file

    # Data Loading & Preprocessing
    df = load_csv_data(csv_file)  # pass only the filepath

    data_scaled, scaler = preprocess_data(df)
    X, y = create_sequences(data_scaled, SEQ_LEN)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    # Train/Test Split
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Model
    model = build_lstm_model((SEQ_LEN, 1))
    train_model(model, X_train, y_train)

    # Predict and Evaluate
    predicted = predict(model, X_test)
    import numpy as np
    real_prices = scaler.inverse_transform(y_test.reshape(-1, 1))
    predicted_prices = scaler.inverse_transform(predicted)
    plot_predictions(real_prices, predicted_prices, title="Stock Price Prediction")
