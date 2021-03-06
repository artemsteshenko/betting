# -*- coding: utf-8 -*-
"""feature_selector.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/160254jZGu5KgsDKHH2HYxDBDDllVku7T
"""

import pandas as pd
import numpy as np
import csv  
from sklearn.linear_model import RidgeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score
from sklearn.linear_model import Lasso
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn import preprocessing
import itertools
from sklearn.model_selection import ShuffleSplit

matches = pd.read_csv('matches.csv', header=None, names=['match_id','fid','home_team_id','away_team_id','date','league_id','season',
                                                         'home_team_goals','away_team_goals','home_team_name','away_team_name','home_team_xg','away_team_xg',
                                                         'home_team_win_chance','drow_chance','away_team_win_chance','league_name','home_team_shots','away_team_shots',
                                                         'home_team_shots_on_target','away_team_shots_on_target','home_team_deep','away_team_deep','away_team_ppda','home_team_ppda'])
matches = matches.sort_values(by='date' ,ignore_index=True)
data_feature_en = pd.read_csv('data_feature_en.csv')
data_feature_en = data_feature_en[matches['league_id'] != 6]
def get_result(scored, conceded):
  if scored > conceded:
    return 'H'
  elif scored <= conceded:
    return 'noH'

data_feature_en['result'] = data_feature_en.apply(lambda x: get_result(x[3], x[4]), axis=1)

data_feature_en['coeff_noH'] = (data_feature_en['coeffA']*data_feature_en['coeffD'])/(data_feature_en['coeffA']+data_feature_en['coeffD'])
data_without_nones = data_feature_en.replace(to_replace='None', value=np.nan).dropna()
#data_without_nones.iloc[:,22:70]



def quality(data, X_test, y_test, prediction):
  exact_data = X_test[prediction == y_test]
  sum = 0
  count_D= 0
  for item in exact_data.index:
    if y_test[item] == 'H':
      sum += data_feature_en.loc[item,:]['coeffH']
    elif y_test[item] == 'noH':
      count_D += 1
      sum += data_feature_en.loc[item,:]['coeff_noH']  
  return sum/len(X_test) - 1

def normalize(X):
  normalized_X = pd.DataFrame(preprocessing.normalize(X), index=X.index, columns=X.columns)
  return normalized_X

# def get_best_subset(data, model):
#   y = data['result']
#   X = data.iloc[:, :48]
#   remaining_features = X.columns
#   best_models = {}
#   for number in range(3, len(remaining_features)):
#     best_quality_for_number = -100

#     for combination in itertools.combinations(remaining_features,number):

#       value = fit_predict(data, y, combination, model)
#       if value > best_quality_for_number:
#         best_quality_for_number = value
#     print(number, best_quality_for_number)
#     best_models[str(number)] = (number, combination, best_quality_for_number)
#   return best_models

def add_model_to_file(file, number, best_quality_for_number, features):
    fields=[number, best_quality_for_number, features]
    with open(file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(fields)

def get_forward_subset(data, model):
  y = data['result']
  X = data.iloc[:, :48]
  remaining_features = set(X.columns)
  best_models = {}
  number_of_features = len(remaining_features) - 1
  features = ['mean_away_goals_scored_last_6']
  for number in range(number_of_features):

    best_quality_for_number = -100
    for new_feature in remaining_features:
      
      value = fit_predict(data, y, features + [new_feature], model)
      if value > best_quality_for_number:
        best_quality_for_number = value
        best_feature = new_feature
    features.append(best_feature)
    remaining_features -= set(best_feature)
    print(number, best_quality_for_number, str(model)[:20], features)
    add_model_to_file('best_models'+str(model)[:20]+'.csv', number, best_quality_for_number, features)
    best_models[str(number)] = (number, best_quality_for_number, features)
  return best_models

def fit_predict(data, y, combination, model):
  X = data[list(combination)]

  normalized_X = normalize(X)
  cv = ShuffleSplit(n_splits=5, test_size=0.25, random_state=0)
  values = []
  for train_index, test_index in cv.split(normalized_X):
    X_train, X_test, y_train, y_test = normalized_X.iloc[list(train_index)], normalized_X.iloc[list(test_index)], y.iloc[list(train_index)], y.iloc[list(test_index)]
    model.fit(X_train, y_train)

    prediction = model.predict(X_test)
    values.append(quality(data, X_test, y_test, prediction))
  return np.array(values).mean()

models = [GradientBoostingClassifier(),RandomForestClassifier(), SVC(), LogisticRegression(solver='lbfgs')]

for model in models:
  best_models = get_forward_subset(data_without_nones.iloc[:,22:], model)

