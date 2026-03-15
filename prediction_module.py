import numpy as np
from sklearn.linear_model import LinearRegression


def predict_next_value(before_values, after_values):
    """
    Прогноз следующего значения показателя
    """

    X = np.array(before_values).reshape(-1, 1)
    y = np.array(after_values)

    model = LinearRegression()
    model.fit(X, y)

    predictions = model.predict(X)

    return predictions