import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

#예시 데이터 불러오기
df = pd.read_csv('../data/1819/england-premier-league-matches-2018-to-2019-stats.csv')

#간단한 예측 모델
df['match_result'] = df.apply(lambda row : 1 if row['home_team_goal_count'] > row['away_team_goal_count']
else 0 if row['home_team_goal_count']  < row['away_team_goal_count']
else 2, axis=1)

X = df[['odds_ft_home_team_win', 'odds_ft_draw', 'odds_ft_away_team_win']]
y = df['match_result']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

