import os
import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import google.generativeai as genai

# --- ⚙️ 설정: 이 부분에 실제 정보를 입력하세요. ---

# 1. Gemini API 키 설정
# https://aistudio.google.com/app/apikey 에서 API 키를 발급받아 아래에 붙여넣으세요.
GEMINI_API_KEY = "-"

# 2. RDS MySQL 데이터베이스 정보 설정
DB_CONFIG = {
    'host': "premo-instance.czwmu86ms4yl.us-east-1.rds.amazonaws.com",
    'user': "admin",
    'password': "tteam891",
    'database': "premo"
}
# ----------------------------------------------------


# Gemini API 설정
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    print("✅ Gemini API configured successfully.")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")
    exit()

def create_db_connection():
    """RDS MySQL 데이터베이스에 연결"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ MySQL Database connection successful")
        return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL Database: {e}")
        return None

def fetch_unprocessed_matches(connection):
    """
    아직 처리되지 않은 경기 목록을 가져옵니다.
    home_insights가 NULL인 것을 기준으로 처리 대상을 판단합니다.
    """
    cursor = connection.cursor(dictionary=True)
    # start_time을 datetime 객체로 변환하여 비교할 수 있도록 CAST 사용
    query = """
    SELECT 
        m.match_id, 
        CAST(m.start_time AS DATETIME) AS match_date,
        ht.team_common_name AS home_team_name,
        ht.team_id AS home_team_id,
        at.team_common_name AS away_team_name,
        at.team_id AS away_team_id
    FROM `match` m
    JOIN team ht ON m.home_team_id = ht.team_id
    JOIN team at ON m.away_team_id = at.team_id
    WHERE m.home_insights IS NULL
    ORDER BY m.start_time ASC;
    """
    try:
        cursor.execute(query)
        matches = cursor.fetchall()
        return matches
    except Error as e:
        print(f"❌ Error fetching matches: {e}")
        return []
    finally:
        cursor.close()


def search_team_news(team_name, end_date):
    """
    Google 검색을 통해 특정 팀의 최신 뉴스를 검색합니다.
    실제 구현에서는 Google Search API 등을 사용하여 뉴스 기사 제목과 URL을 가져와야 합니다.
    이 코드에서는 예시를 위해 더미 데이터를 반환합니다.
    """
    print(f"🔍 Searching news for '{team_name}' until {end_date.strftime('%Y-%m-%d')}...")
    # 예시 뉴스 데이터
    dummy_news = {
        "Manchester United": [
            "Interested in signing Barcelona forward and Athletic Club winger Nico Williams - 90min",
            "A new stadium will be built at a cost of around £2 billion - BBC",
            "Pushing to sign Trent Alexander-Arnold on a free transfer this summer - 90min"
        ],
        "Real Madrid": [
            "Attempting to hijack Arsenal's deal for Real Sociedad midfielder Martin Zubimendi - 90min",
            "Lost 2 of their last 5 games.",
            "They have recorded 4 wins and 1 draw in their last 5 matches against PL teams."
        ]
    }
    return dummy_news.get(team_name, [f"No recent news found for {team_name}."])


def get_summary_from_gemini(home_team_name, away_team_name, home_news, away_news):
    """Gemini API를 사용하여 뉴스 요약 및 인사이트 생성"""
    print("🤖 Calling Gemini API for summarization...")
    
    prompt = f"""
    You are a professional football analyst. For the upcoming match between {home_team_name} (home) and {away_team_name} (away), analyze the provided news articles.
    Generate a single, valid JSON object that contains four main keys: "home_insights", "away_insights", "home_news", and "away_news".

    - The "insights" keys should point to an object with a single key "data" which contains an array of strings. Each string should be a key analysis point, such as team form, major injuries, or tactical considerations.
    - The "news" keys should point to an object with a single key "data" which contains an array of strings. Each string should be a summary of a significant news item, like transfer rumors or off-field events.

    Here is the recent news:
    - {home_team_name} News: {' | '.join(home_news)}
    - {away_team_name} News: {' | '.join(away_news)}

    Provide your response ONLY in the following valid JSON format. Do not include any text before or after the JSON object.

    {{
      "home_insights": {{ "data": ["No losses in the last 5 games.", "Key players are unavailable due to injury."] }},
      "away_insights": {{ "data": ["Recorded 4 wins and 1 draw in their last 5 matches.", "Lost 2 of their last 5 games."] }},
      "home_news": {{ "data": ["Interested in signing a new forward.", "Plans for a new stadium are progressing."] }},
      "away_news": {{ "data": ["Linked with a move for a star midfielder.", "Manager confirmed the team is at full strength."] }}
    }}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        # Gemini 응답에서 ```json ... ``` 블록을 정리하고 순수 JSON 텍스트만 추출
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")].strip()
        
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"❌ Error calling Gemini API or parsing JSON: {e}")
        print(f"   Gemini Response Text: {response.text if 'response' in locals() else 'N/A'}")
        return None

def update_database(connection, match_id, analysis_result):
    """생성된 데이터로 DB의 match 테이블을 업데이트"""
    cursor = connection.cursor()
    try:
        # match 테이블 업데이트
        update_match_query = """
        UPDATE `match`
        SET home_insights = %s, away_insights = %s, home_news = %s, away_news = %s, updated_at = NOW()
        WHERE match_id = %s;
        """
        # Gemini 결과에서 각 부분을 JSON 문자열로 변환
        home_insights_json = json.dumps(analysis_result.get('home_insights'))
        away_insights_json = json.dumps(analysis_result.get('away_insights'))
        home_news_json = json.dumps(analysis_result.get('home_news'))
        away_news_json = json.dumps(analysis_result.get('away_news'))

        cursor.execute(update_match_query, (
            home_insights_json, away_insights_json,
            home_news_json, away_news_json,
            match_id
        ))
        print(f"💾 Updated `match` table for match_id: {match_id}")
        
        connection.commit()
    except Error as e:
        print(f"❌ Database update failed for match_id {match_id}: {e}")
        connection.rollback()
    finally:
        cursor.close()


def main():
    """메인 실행 함수"""
    db_conn = create_db_connection()
    if not db_conn:
        return

    matches_to_process = fetch_unprocessed_matches(db_conn)
    print(f"\nFound {len(matches_to_process)} matches to process.")

    for match in matches_to_process:
        print(f"\n▶ Processing Match ID: {match['match_id']} ({match['home_team_name']} vs {match['away_team_name']})")
        
        # 1. 뉴스 검색
        match_date = match['match_date']
        home_news = search_team_news(match['home_team_name'], match_date)
        away_news = search_team_news(match['away_team_name'], match_date)

        # 2. Gemini로 요약 및 분석
        analysis_result = get_summary_from_gemini(match['home_team_name'], match['away_team_name'], home_news, away_news)
        
        if not analysis_result:
            print(f"⏩ Skipping match {match['match_id']} due to Gemini API error.")
            continue

        # 3. DB 업데이트 (키플레이어 로직 제거됨)
        update_database(db_conn, match['match_id'], analysis_result)

    db_conn.close()
    print("\n✅ All matches processed. Connection closed.")

if __name__ == "__main__":
    main()
