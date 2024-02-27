import numpy as np
import random
import joblib
import json

def get_cleaned_data(pos: str = 'Centers'):
    with open(f'collected_data/player_cleaned_data/cleaned_contract_data_{pos}.json', 'r') as f:
        return json.load(f)

def split_cleaned_data(data, test_set_size: float = 0.2):
    num_train_elements = int(len(data) * (1 - test_set_size))
    random.shuffle(data)

    X_train, y_train, X_test, y_test = [], [], [], []
    for i in range(len(data)):
        element = data[i]

        x_attrs = []
        y_attrs = [element.get("CapPct")]
        if element.get("position") == "C":
            x_attrs = [
                    element.get("G82"), element.get("A82"), element.get("PM82"), 
                    element.get("S%"), element.get("Age"), element.get("StartIsUFA"), 
                    element.get("EndIsUFA"), element.get("Length")
                ]
        elif element.get("position") == "L" or element.get("position") == "R":
            x_attrs = [
                    element.get("G82"), element.get("A82"), element.get("PM82"), 
                    element.get("S%"), element.get("Age"), element.get("StartIsUFA"), 
                    element.get("EndIsUFA"), element.get("Length")
                ]
        elif element.get("position") == "D":
            x_attrs = [
                element.get("G82"), element.get("A82"), element.get("PM82"), 
                ((element.get("PIM") / element.get("gamesPlayed")) * 82), 
                element.get("S%"), element.get("Age"), element.get("StartIsUFA"), 
                element.get("EndIsUFA"), element.get("Length")
            ]
        else:
            x_attrs = [
                (element.get("W") / element.get("gamesPlayed")), (element.get("SO") / element.get("W")), 
                element.get("SV%"), element.get("GAA"), element.get("Age"), 
                element.get("StartIsUFA"), element.get("EndIsUFA"), element.get("Length")
            ]
        
        if i < num_train_elements:
            X_train.append(x_attrs)
            y_train.append(y_attrs)
        else:
            X_test.append(x_attrs)
            y_test.append(y_attrs)
    return np.array(X_train), np.array(y_train), np.array(X_test), np.array(y_test)

def sklearn_model_rf():
    player_types = ['Centers', 'Wings', 'Defencemen', 'Goalies']
    for model in player_types:
        X_train, y_train, X_test, y_test = split_cleaned_data(get_cleaned_data(model), 0.2)

        from sklearn.ensemble import RandomForestRegressor

        reg = RandomForestRegressor(
            n_jobs=-1,
            n_estimators=100
        ).fit(X_train, y_train)

        get_model_scores(reg, X_train, y_train, X_test, y_test)

        joblib.dump(reg, f"models/model_{model.lower()}.joblib")

def sklearn_model_lin_reg():
    player_types = ['Centers', 'Wings', 'Defencemen', 'Goalies']
    for model in player_types:
        X_train, y_train, X_test, y_test = split_cleaned_data(get_cleaned_data(model), 0.2)

        from sklearn.linear_model import LinearRegression

        reg = LinearRegression(
            n_jobs=-1,
        ).fit(X_train, y_train)

        get_model_scores(reg, X_train, y_train, X_test, y_test)

        joblib.dump(reg, f"models/model_linreg_{model.lower()}.joblib")

def get_model_scores(regressor, X_train, y_train, X_test, y_test):
    print(regressor.score(X_train, y_train))
    print(regressor.score(X_test, y_test))

if __name__ == "__main__":
    sklearn_model_rf()
    sklearn_model_lin_reg()