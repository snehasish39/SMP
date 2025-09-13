#Functions for prediction and plotting results


import matplotlib.pyplot as plt

def predict(model, X):
    return model.predict(X)

def plot_predictions(real, predicted, title='Stock Price Prediction'):
    plt.figure(figsize=(10, 5))
    plt.plot(real, color='black', label='Real Price')
    plt.plot(predicted, color='green', label='Predicted Price')
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()
