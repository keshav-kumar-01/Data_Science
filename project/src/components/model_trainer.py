import os
import sys
from dataclasses import dataclass
from catboost import CatBoostRegressor
from sklearn.ensemble import(
    AdaBoostRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor
from src.exception import CustomException
from src.logger import logging
from src.utils import save_object
from src.utils import evaluate_models



@dataclass
class model_trainer_config_files:
    trained_model_file_path= os.path.join("artifacts","model.pkl")

class model_trainer:
    def __init__(self):
        self.model_trainer_config = model_trainer_config_files()

    def initiate_model_training(self,train_array,test_array):
        try:
            logging.info("spliting training and test input data")
            X_train , y_train , X_test , y_test=(
                train_array[:,:-1],
                train_array[:,-1],
                test_array[:,:-1],
                test_array[:,-1]
            )
            models = {
                "Random Forest": RandomForestRegressor(),
                "Decision Tree": DecisionTreeRegressor(),
                "Gradient Boosting": GradientBoostingRegressor(),
                "Linear Regressor": LinearRegression(),
                "K-Neighbors Regressor": KNeighborsRegressor(),
                "XG Boost": XGBRegressor(),
                "CatBoost Regressor": CatBoostRegressor(verbose=False),
                "Ada Boost Regressor": AdaBoostRegressor(),
            }

            param = {
                "Decision Tree": {
                    "criterion": ["squared_error", "friedman_mse", "absolute_error", "poisson"],
                    "splitter": ["best", "random"],
                    "max_depth": [None, 5, 10],
                    "min_samples_split": [2, 5, 10],
                    "min_samples_leaf": [1, 2, 4],
                    #"min_weight_fraction_leaf": [0.0],
                    "max_features": [None, "sqrt", "log2"],
                    "random_state": [42],
                    #"max_leaf_nodes": [None, 10, 20, 50],
                    #"min_impurity_decrease": [0.0],
                    #"ccp_alpha": [0.0]
                },

                "Random Forest": {
                    "n_estimators": [50, 100, 200],
                    "criterion": ["squared_error", "absolute_error", "friedman_mse", "poisson"],
                    "max_depth": [None, 10, 20],
                    "min_samples_split": [2, 5, 10],
                    #"min_samples_leaf": [1, 2, 4],
                    #"min_weight_fraction_leaf": [0.0],
                    "max_features": ["sqrt", "log2", None],
                    #"max_leaf_nodes": [None, 10, 20, 50],
                    #"bootstrap": [True, False],
                    #"oob_score": [False],
                    "random_state": [42],
                    "n_jobs": [-1],
                    #"ccp_alpha": [0.0]
                },

                "Gradient Boosting": {
                    "loss": ["squared_error", "absolute_error", "huber", "quantile"],
                    "learning_rate": [0.01, 0.05, 0.1, 0.2],
                    "n_estimators": [50, 100, 200],
                    #"subsample": [0.8, 1.0],
                    #"criterion": ["friedman_mse", "squared_error"],
                    "min_samples_split": [2, 5, 10],
                    #"min_samples_leaf": [1, 2, 4],
                    "max_depth": [3, 5, 10],
                    "max_features": ["sqrt", "log2", None],
                    "random_state": [42]
                },

                "Linear Regressor": {
                    "fit_intercept": [True, False],
                    #"copy_X": [True, False],
                    #"positive": [True, False]
                },

                "K-Neighbors Regressor": {
                    "n_neighbors": [3, 5, 7, 9],
                    "weights": ["uniform", "distance"],
                    "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
                    #"leaf_size": [20, 30, 40],
                    #"p": [1, 2],
                    #"metric": ["minkowski"]
                },

                "XG Boost": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.01, 0.05, 0.1, 0.2],
                    "max_depth": [3, 5],
                    # "min_child_weight": [1, 3, 5],
                    #"subsample": [0.8, 1.0],
                    #"colsample_bytree": [0.8, 1.0],
                    #"gamma": [0, 0.1, 0.2],
                    #"reg_alpha": [0, 0.01, 0.1],
                    #"reg_lambda": [1, 1.5, 2],
                    "random_state": [42]
                },

                "CatBoost Regressor": {
                    "iterations": [100, 200, 500],
                    "learning_rate": [0.01, 0.05, 0.1],
                    "depth": [4, 6, 8, 10],
                    "loss_function": ["RMSE"],
                    "eval_metric": ["RMSE"],
                    "random_seed": [42],
                    "verbose": [False]
                },

                "Ada Boost Regressor": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.01, 0.05, 0.1, 1.0],
                    "loss": ["linear", "square", "exponential"],
                    "random_state": [42]
                }
            }

            model_report: dict= evaluate_models(X_train=X_train,y_train=y_train,X_test = X_test , y_test = y_test ,models=models,params=param)

            best_model_score = max(sorted(model_report.values()))

            best_model_name = list(model_report.keys())[
                list(model_report.values()).index(best_model_score)
            ]
            best_model = models[best_model_name]
            if best_model_score <0.6:
                raise CustomException("No best model found")
            logging.info(f"Best found model on both training and testing dataset")
            
            save_object(
                file_path=self.model_trainer_config.trained_model_file_path,
                obj = best_model
            )
            predicted = best_model.predict(X_test)
            r2_score_output = r2_score(y_test,predicted)
            return r2_score_output

        except Exception as e:
            raise CustomException(e,sys)