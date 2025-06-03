from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import pickle
import warnings
import pymysql
from scipy.stats import poisson
import os

warnings.filterwarnings("ignore")
app = Flask(__name__)

# ✅ 모델 로드
with open('xgb_model_home.pkl', 'rb') as f:
    model_home = pickle.load(f)
with open('xgb_model_away.pkl', 'rb') as f:
    model_away = pickle.load(f)

# 학습 시 사용된 feature 컬럼 불러오기
with open('trained_feature_columns.pkl', 'rb') as f:
    trained_feature_columns = pickle.load(f)

# 전체 데이터 로드
df_full = pd.read_csv('../../data/datas/2/final/merged_final.csv')
df_full['date'] = pd.to_datetime(df_full['date'], errors='coerce')

# DB 연결 함수
def get_db_connection():
    return pymysql.connect(
        host="premo-instance.czwmu86ms4yl.us-east-1.rds.amazonaws.com",
        user="admin",
        password="tteam891",
        db="premo",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# 팀 매핑 정보 초기화
def load_team_mapping(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT team_id, team_common_name, short_name FROM team")
        team_rows = cursor.fetchall()
    mapping = {}
    for row in team_rows:
        mapping[row['team_common_name'].lower()] = row['team_id']
        mapping[row['short_name'].lower()] = row['team_id']
    return mapping

team_folder_map = {"AFC Bournemouth": "Bournemouth"}

def build_input_vector(home_team_name, away_team_name, current_date, df, trained_feature_columns, N=3):
    print("✅ [ENTRY] build_input_vector 함수 진입")

    try:
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        current_date = pd.to_datetime(current_date)
        print(f"📅 [STEP 1] 날짜 처리 완료: {current_date}")
    except Exception as e:
        print(f"❌ [ERROR] 날짜 처리 실패: {e}")
        raise

    try:
        home_past = df[(df['home_team_name'] == home_team_name) & (df['date'] < current_date)] \
                        .sort_values('date', ascending=False).head(N)
        away_past = df[(df['away_team_name'] == away_team_name) & (df['date'] < current_date)] \
                        .sort_values('date', ascending=False).head(N)
        print(f"📊 [STEP 2] 최근 경기 필터링 완료 - 홈: {len(home_past)}, 어웨이: {len(away_past)}")

        if home_past.empty or away_past.empty:
            raise ValueError("최근 경기 부족: 홈팀 또는 어웨이팀")
    except Exception as e:
        print(f"❌ [ERROR] 최근 경기 필터링 실패: {e}")
        raise

    try:
        exclude_cols = [
            'date_GMT', 'date', 'season',
            'home_result', 'away_result',
            'home_gk_save_pct', 'away_gk_save_pct',
            'home_team_goal_count', 'away_team_goal_count'
        ]
        #feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [
        col for col in df.columns
        if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]
        home_feature_cols = [col for col in feature_cols if col.startswith('home_')]
        away_feature_cols = [col for col in feature_cols if col.startswith('away_')]

        home_mean = home_past[home_feature_cols].mean()
        away_mean = away_past[away_feature_cols].mean()
        base_vector = pd.concat([home_mean, away_mean]).to_frame().T
        print(f"🧮 [STEP 3] 평균 벡터 계산 완료 - shape: {base_vector.shape}")
    except Exception as e:
        print(f"❌ [ERROR] 평균 벡터 계산 실패: {e}")
        raise

    try:
        dummy_df = pd.DataFrame({
            'home_team_name': [home_team_name],
            'away_team_name': [away_team_name]
        })
        team_dummies = pd.get_dummies(dummy_df, prefix=['home_team_name', 'away_team_name'])
        print(f"🏷️ [STEP 4] 팀 원-핫 인코딩 완료 - 컬럼: {team_dummies.columns.tolist()}")
    except Exception as e:
        print(f"❌ [ERROR] 팀 원-핫 인코딩 실패: {e}")
        raise

    try:
        full_vector = pd.concat([base_vector, team_dummies], axis=1)

        for col in trained_feature_columns:
            if col not in full_vector.columns:
                full_vector[col] = 0.0

        full_vector = full_vector[trained_feature_columns]
        full_vector = full_vector.select_dtypes(include='number')
        full_vector.reset_index(drop=True, inplace=True)
        print(f"📦 [STEP 5] 최종 입력 벡터 정렬 및 반환 - shape: {full_vector.shape}")
    except Exception as e:
        print(f"❌ [ERROR] 최종 벡터 구성 실패: {e}")
        raise

    return full_vector

""" def build_input_vector(home_team_name, away_team_name, current_date, df, trained_feature_columns, N=5):
    print("✅ [ENTRY] build_input_vector_weighted_avg 진입")

    try:
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        current_date = pd.to_datetime(current_date)
        print(f"📅 날짜 처리 완료: {current_date}")
    except Exception as e:
        print(f"❌ 날짜 처리 실패: {e}")
        raise

    try:
        home_past = df[(df['home_team_name'] == home_team_name) & (df['date'] < current_date)] \
                        .sort_values('date', ascending=False).head(N)
        away_past = df[(df['away_team_name'] == away_team_name) & (df['date'] < current_date)] \
                        .sort_values('date', ascending=False).head(N)
        print(f"📊 최근 경기 필터링 - 홈: {len(home_past)}, 어웨이: {len(away_past)}")
        if home_past.empty or away_past.empty:
            raise ValueError("최근 경기 부족")
    except Exception as e:
        print(f"❌ 경기 필터링 실패: {e}")
        raise

    try:
        exclude_cols = [
            'date_GMT', 'date', 'season',
            'home_result', 'away_result',
            'home_gk_save_pct', 'away_gk_save_pct',
            'home_team_goal_count', 'away_team_goal_count'
        ]
        feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        home_feature_cols = [col for col in feature_cols if col.startswith('home_')]
        away_feature_cols = [col for col in feature_cols if col.startswith('away_')]

        weights = np.linspace(1, 0.6, len(home_past))
        home_weighted = (home_past[home_feature_cols].T * weights).T.sum() / weights.sum()

        weights = np.linspace(1, 0.6, len(away_past))
        away_weighted = (away_past[away_feature_cols].T * weights).T.sum() / weights.sum()

        base_vector = pd.concat([home_weighted, away_weighted]).to_frame().T
        print(f"🧮 가중 평균 완료 - shape: {base_vector.shape}")
    except Exception as e:
        print(f"❌ 가중 평균 실패: {e}")
        raise

    try:
        dummy_df = pd.DataFrame({'home_team_name': [home_team_name], 'away_team_name': [away_team_name]})
        team_dummies = pd.get_dummies(dummy_df, prefix=['home_team_name', 'away_team_name'])
        print(f"🏷️ 원-핫 인코딩 완료 - 컬럼: {team_dummies.columns.tolist()}")
    except Exception as e:
        print(f"❌ 원-핫 인코딩 실패: {e}")
        raise

    try:
        full_vector = pd.concat([base_vector, team_dummies], axis=1)
        for col in trained_feature_columns:
            if col not in full_vector.columns:
                full_vector[col] = 0.0
        full_vector = full_vector[trained_feature_columns].select_dtypes(include='number')
        full_vector.reset_index(drop=True, inplace=True)
        print(f"📦 최종 벡터 완성 - shape: {full_vector.shape}")
    except Exception as e:
        print(f"❌ 최종 벡터 구성 실패: {e}")
        raise

    return full_vector """

""" def build_input_vector(home_team_name, away_team_name, current_date, df, trained_feature_columns, N=5):
    print("✅ [ENTRY] build_input_vector_team_blind 진입")

    try:
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        current_date = pd.to_datetime(current_date)
        print(f"📅 날짜 처리 완료: {current_date}")
    except Exception as e:
        print(f"❌ 날짜 처리 실패: {e}")
        raise

    try:
        home_past = df[
            ((df['home_team_name'] == home_team_name) | (df['away_team_name'] == home_team_name)) &
            (df['date'] < current_date)
        ].sort_values('date', ascending=False).head(N)

        away_past = df[
            ((df['home_team_name'] == away_team_name) | (df['away_team_name'] == away_team_name)) &
            (df['date'] < current_date)
        ].sort_values('date', ascending=False).head(N)

        print(f"📊 최근 경기 필터링 (혼합) - 홈팀: {len(home_past)}, 어웨이팀: {len(away_past)}")
        if home_past.empty or away_past.empty:
            raise ValueError("최근 경기 부족")
    except Exception as e:
        print(f"❌ 혼합 필터링 실패: {e}")
        raise

    try:
        exclude_cols = [
            'date_GMT', 'date', 'season',
            'home_result', 'away_result',
            'home_gk_save_pct', 'away_gk_save_pct',
            'home_team_goal_count', 'away_team_goal_count'
        ]
        feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
        home_feature_cols = [col for col in feature_cols if col.startswith('home_')]
        away_feature_cols = [col for col in feature_cols if col.startswith('away_')]

        home_mean = home_past[home_feature_cols].mean()
        away_mean = away_past[away_feature_cols].mean()
        base_vector = pd.concat([home_mean, away_mean]).to_frame().T
        print(f"🧮 혼합 평균 완료 - shape: {base_vector.shape}")
    except Exception as e:
        print(f"❌ 혼합 평균 실패: {e}")
        raise

    try:
        dummy_df = pd.DataFrame({'home_team_name': [home_team_name], 'away_team_name': [away_team_name]})
        team_dummies = pd.get_dummies(dummy_df, prefix=['home_team_name', 'away_team_name'])
        print(f"🏷️ 원-핫 인코딩 완료 - 컬럼: {team_dummies.columns.tolist()}")
    except Exception as e:
        print(f"❌ 원-핫 인코딩 실패: {e}")
        raise

    try:
        full_vector = pd.concat([base_vector, team_dummies], axis=1)
        for col in trained_feature_columns:
            if col not in full_vector.columns:
                full_vector[col] = 0.0
        full_vector = full_vector[trained_feature_columns].select_dtypes(include='number')
        full_vector.reset_index(drop=True, inplace=True)
        print(f"📦 최종 벡터 완성 - shape: {full_vector.shape}")
    except Exception as e:
        print(f"❌ 최종 벡터 구성 실패: {e}")
        raise

    return full_vector """


# Poisson 예측 함수
def predict_scores_with_prob(input_vector, max_goal=5, top_k=3):
    mu_home = model_home.predict(input_vector)[0]
    mu_away = model_away.predict(input_vector)[0]

    result = []
    home_win_prob, draw_prob, away_win_prob, rest_prob = 0, 0, 0, 0

    for h in range(max_goal + 1):
        for a in range(max_goal + 1):
            p = poisson.pmf(h, mu_home) * poisson.pmf(a, mu_away)
            result.append(((h, a), p))
            if h > a:
                home_win_prob += p
            elif h == a:
                draw_prob += p
            else:
                away_win_prob += p

    for h in range(max_goal + 1):
        rest_prob += poisson.pmf(h, mu_home) * (1 - poisson.cdf(max_goal, mu_away))
        rest_prob += (1 - poisson.cdf(max_goal, mu_home)) * poisson.pmf(h, mu_away)
    rest_prob -= (1 - poisson.cdf(max_goal, mu_home)) * (1 - poisson.cdf(max_goal, mu_away))

    result.append((("5+", "5+"), rest_prob))

    total = home_win_prob + draw_prob + away_win_prob
    home_win_prob /= total
    draw_prob /= total
    away_win_prob /= total

    return {
        "home_expected_goals": round(mu_home, 3),
        "away_expected_goals": round(mu_away, 3),
        "top_predictions": sorted(result, key=lambda x: x[1], reverse=True)[:top_k],
        "home_win_prob": round(home_win_prob, 4),
        "draw_prob": round(draw_prob, 4),
        "away_win_prob": round(away_win_prob, 4)
    }

def insert_prediction_to_db(
    conn, match_date, home_team_name, away_team_name, prediction_result, team_name_to_id, team_folder_map={}
):
    home_name = team_folder_map.get(home_team_name, home_team_name).lower()
    away_name = team_folder_map.get(away_team_name, away_team_name).lower()

    home_id = team_name_to_id.get(home_name)
    away_id = team_name_to_id.get(away_name)
    row_date = pd.to_datetime(match_date).strftime("%Y-%m-%d")

    if home_id is None or away_id is None:
        print(f"❌ 팀 ID 매핑 실패: {home_team_name} / {away_team_name}")
        return

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT match_id FROM `match`
            WHERE home_team_id = %s AND away_team_id = %s AND start_time = %s
        """, (home_id, away_id, row_date))
        result = cursor.fetchone()

        if not result:
            print(f"❌ Match not found: {home_team_name} vs {away_team_name} on {match_date}")
            return

        match_id = result["match_id"]

        insert_sql = """
        INSERT INTO model_output (
            match_id,
            home_winrate, drawrate, away_winrate,
            home_score_1, away_score_1, score_1_prob,
            home_score_2, away_score_2, score_2_prob,
            home_score_3, away_score_3, score_3_prob,
            prediction_date, created_at, updated_at
        ) VALUES (
            %(match_id)s,
            %(home_winrate)s, %(drawrate)s, %(away_winrate)s,
            %(home_score_1)s, %(away_score_1)s, %(score_1_prob)s,
            %(home_score_2)s, %(away_score_2)s, %(score_2_prob)s,
            %(home_score_3)s, %(away_score_3)s, %(score_3_prob)s,
            NOW(), NOW(), NOW()
        );
        """

        insert_data = {
            "match_id": match_id,
            "home_winrate": prediction_result['home_win_prob'] * 100,
            "drawrate": prediction_result['draw_prob'] * 100,
            "away_winrate": prediction_result['away_win_prob'] * 100,
        }

        for i, ((h, a), p) in enumerate(prediction_result["top_predictions"], 1):
            insert_data[f"home_score_{i}"] = h
            insert_data[f"away_score_{i}"] = a
            insert_data[f"score_{i}_prob"] = round(p * 100, 2)

        cursor.execute(insert_sql, insert_data)
        conn.commit()

        print(f"✅ DB 저장 완료: {home_team_name} vs {away_team_name} on {match_date}")

# API 엔드포인트
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    home_team = data.get("home_team")
    away_team = data.get("away_team")
    match_date = data.get("match_date")

    if not home_team or not away_team or not match_date:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        input_vector = build_input_vector(home_team, away_team, match_date, df_full, trained_feature_columns)
        prediction_result = predict_scores_with_prob(input_vector)

        # 🔁 numpy 타입을 Python 기본 타입으로 변환
        def convert(obj):
            if isinstance(obj, np.generic):
                return obj.item()
            if isinstance(obj, tuple):
                return tuple(convert(i) for i in obj)
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj

        clean_result = convert(prediction_result)

        return jsonify({
            "success": True,
            "home_team": home_team,
            "away_team": away_team,
            "match_date": match_date,
            **clean_result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 서버 실행
if __name__ == '__main__':
    print("\u26a1\ufe0f 서버 실행 중...")
    app.run(host='0.0.0.0', port=5000)