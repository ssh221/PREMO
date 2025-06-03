import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

class PLKeyPlayerSelector:
    def __init__(self, season_id=719):
        self.base_url = "https://footballapi.pulselive.com/football"
        self.season_id = season_id
        self.team_names = {
            1: 'Arsenal', 2: 'Aston Villa', 131: 'Brighton', 20: 'Southampton',
            4: 'Chelsea', 6: 'Crystal Palace', 7: 'Everton', 34: 'Fulham',
            26: 'Leicester', 10: 'Liverpool', 11: 'Man City', 12: 'Man Utd',
            23: 'Newcastle', 130: 'Brentford', 15: 'Southampton', 21: 'Tottenham',
            127: 'Bournemouth', 25: 'West Ham', 38: 'Wolves', 8: 'Ipswich'
        }

        # 재시도 전략 설정
        self.retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True
        )

        # HTTP 세션 설정
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=self.retry_strategy))
        self.session.headers.update({
            'Origin': 'https://www.premierleague.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        })

    def parse_match_date(self, date_str):
        """날짜 파싱 함수 (BST/GMT 처리)"""
        try:
            # 타임존 정보 제거 및 파싱
            date_clean = re.sub(r'\s+([A-Z]{3})$', '', date_str)
            return datetime.strptime(date_clean, '%a %d %b %Y, %H:%M')
        except Exception as e:
            logger.error(f"날짜 파싱 실패: {date_str} - {str(e)}")
            return datetime.now()

    def get_all_matches(self):
        """전체 경기 정보 수집 (정수형 ID 강제 변환)"""
        matches = []
        page = 0
        
        while True:
            try:
                response = self.session.get(
                    f"{self.base_url}/fixtures",
                    params={
                        'compSeasons': self.season_id,
                        'pageSize': 100,
                        'page': page,
                        'sort': 'asc'
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                for fixture in data.get('content', []):
                    home_team = fixture.get('teams', [{}])[0].get('team', {})
                    away_team = fixture.get('teams', [{}])[1].get('team', {})
                    
                    matches.append({
                        'match_id': int(fixture['id']),
                        'home_team_id': int(home_team.get('id', 0)),
                        'away_team_id': int(away_team.get('id', 0)),
                        'match_date': self.parse_match_date(fixture.get('kickoff', {}).get('label', '')),
                        'home_team_name': self.team_names.get(int(home_team.get('id', 0)), 'Unknown'),
                        'away_team_name': self.team_names.get(int(away_team.get('id', 0)), 'Unknown')
                    })
                
                if page >= data.get('pageInfo', {}).get('numPages', 0) - 1:
                    break
                page += 1
                time.sleep(1)  # 페이지 간 지연

            except Exception as e:
                logger.error(f"경기 정보 수집 실패: {str(e)}")
                break
        
        return matches

    def get_team_players(self, team_id):
        """팀 선수 목록 조회 (정수형 처리)"""
        try:
            response = self.session.get(
                f"{self.base_url}/players",
                params={
                    'compSeasons': self.season_id,
                    'teams': int(team_id),
                    'pageSize': 50
                },
                timeout=10
            )
            response.raise_for_status()
            return [{
                'player_id': int(p['id']),
                'name': p['name']['display'],
                'position': p.get('info', {}).get('position', ''),
                'team_id': int(team_id)
            } for p in response.json().get('content', [])]
            
        except Exception as e:
            logger.error(f"선수 목록 조회 실패 (팀 {team_id}): {str(e)}")
            return []

    def get_player_stats(self, player_id):
        """선수 통계 조회 (재시도 적용)"""
        try:
            response = self.session.get(
                f"{self.base_url}/stats/player/{int(player_id)}",
                params={'compSeasons': self.season_id, 'comps': 1},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            stats = {'player_id': int(player_id)}
            for stat in data.get('stats', []):
                stats[stat['name'].lower()] = stat.get('value', 0)
            
            # 점수 계산
            stats['score'] = (
                stats.get('goals', 0) * 3 +
                stats.get('assists', 0) * 2 +
                stats.get('appearances', 0) * 0.5 +
                stats.get('rating', 0) * 0.1
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"선수 통계 조회 실패 ({player_id}): {str(e)}")
            return {'player_id': int(player_id), 'score': 0}

    def select_key_player(self, team_id, team_name):
        """키 플레이어 선정 알고리즘"""
        players = self.get_team_players(team_id)
        if not players:
            return None
        
        player_scores = []
        for player in players:
            stats = self.get_player_stats(player['player_id'])
            player_scores.append({
                **player,
                **stats
            })
            time.sleep(0.5)  # API 요청 간 지연
        
        if player_scores:
            best_player = max(player_scores, key=lambda x: x['score'])
            return {
                'player_id': best_player['player_id'],
                'player_name': best_player['name'],
                'position': best_player['position'],
                'score': best_player['score']
            }
        return None

    def process_match(self, match):
        """단일 경기 처리"""
        try:
            logger.info(f"처리 중: {match['home_team_name']} vs {match['away_team_name']}")
            
            home_player = self.select_key_player(match['home_team_id'], match['home_team_name'])
            away_player = self.select_key_player(match['away_team_id'], match['away_team_name'])
            
            return {
                'match_id': match['match_id'],
                'match_date': match['match_date'].strftime('%Y-%m-%d'),
                'home_team': match['home_team_name'],
                'away_team': match['away_team_name'],
                'home_key_player_id': home_player['player_id'] if home_player else None,
                'home_key_player_name': home_player['player_name'] if home_player else None,
                'away_key_player_id': away_player['player_id'] if away_player else None,
                'away_key_player_name': away_player['player_name'] if away_player else None
            }
        except Exception as e:
            logger.error(f"경기 처리 실패 ({match['match_id']}): {str(e)}")
            return None

    def run(self):
        """메인 실행 함수"""
        logger.info("2024/25 프리미어리그 키 플레이어 선정 시작")
        
        # 1. 모든 경기 정보 수집
        matches = self.get_all_matches()
        logger.info(f"총 {len(matches)}경기 발견")
        
        # 2. 병렬 처리 (5개 워커로 제한)
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.process_match, match): match for match in matches}
            
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        logger.info(f"진행률: {len(results)}/{len(matches)}")
                except Exception as e:
                    logger.error(f"경기 처리 실패: {str(e)}")
        
        # 3. 결과 저장
        df = pd.DataFrame(results)
        df.to_csv('pl_2024_25_key_players.csv', index=False, encoding='utf-8-sig')
        logger.info(f"CSV 저장 완료: {len(results)}경기 처리됨")

if __name__ == "__main__":
    selector = PLKeyPlayerSelector()
    selector.run()
