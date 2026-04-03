import pandas as pd
import numpy as np
import pickle

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# ================= LOAD DATA =================
delivery_df = pd.read_csv('deliveries.csv')
matches_df = pd.read_csv('matches.csv')

# ================= FILTER 2ND INNINGS =================
delivery_df = delivery_df[delivery_df['inning'] == 2]
delivery_df = delivery_df.sort_values(['match_id','over','ball'])

# ================= WICKETS =================
delivery_df['wicket'] = delivery_df['player_dismissed'].notna().astype(int)
delivery_df['wickets'] = delivery_df.groupby('match_id')['wicket'].cumsum()
delivery_df['wickets_left'] = 10 - delivery_df['wickets']

# ================= RUNS =================
delivery_df['current_runs'] = delivery_df.groupby('match_id')['total_runs'].cumsum()
delivery_df['target'] = delivery_df.groupby('match_id')['total_runs'].transform('sum')
delivery_df['runs_left'] = delivery_df['target'] - delivery_df['current_runs']

# ================= BALLS =================
delivery_df['balls_left'] = 120 - (delivery_df['over']*6 + delivery_df['ball'])
delivery_df['balls_left'] = delivery_df['balls_left'].clip(lower=1)

# ================= RATES =================
delivery_df['crr'] = delivery_df['current_runs'] / ((delivery_df['over']*6 + delivery_df['ball'])/6)
delivery_df['rrr'] = (delivery_df['runs_left']*6) / delivery_df['balls_left']

# ================= MERGE CITY + WINNER =================
matches_df = matches_df[['id','city','winner']]
delivery_df = delivery_df.merge(matches_df, left_on='match_id', right_on='id')
delivery_df.drop(columns=['id'], inplace=True)

# ================= RESULT =================
delivery_df['result'] = (delivery_df['batting_team'] == delivery_df['winner']).astype(int)

# ================= FINAL DATA =================
final_df = delivery_df[['batting_team','bowling_team','city',
                        'runs_left','balls_left','wickets_left','crr','rrr','result']]

final_df = final_df.replace([np.inf, -np.inf], np.nan)
final_df.dropna(inplace=True)

# ================= MODEL =================
X = final_df.drop('result', axis=1)
y = final_df['result']

trf = ColumnTransformer([
    ('cat', OneHotEncoder(drop='first'), ['batting_team','bowling_team','city']),
    ('num', StandardScaler(), ['runs_left','balls_left','wickets_left','crr','rrr'])
], remainder='passthrough', force_int_remainder_cols=False)

pipe = Pipeline([
    ('step1', trf),
    ('step2', LogisticRegression(max_iter=2000))
])

# ================= TRAIN =================
pipe.fit(X, y)

# ================= SAVE =================
pickle.dump(pipe, open('pipe.pkl','wb'))

print("✅ Model trained and saved as pipe.pkl")