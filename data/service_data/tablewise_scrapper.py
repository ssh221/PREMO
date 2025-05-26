import requests
import pandas as pd
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("epl_multiseason_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class EPLHistoricalScraper:
    def __init__(self, output_folder="epl_historical_data"):
        self.output_folder = output_folder
        self.base_url = "https://footballapi.pulselive.com/football"
        self.headers = {
            'Origin': 'https://www.premierleague.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        
        # 세션 설정
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        os.makedirs(output_folder, exist_ok=True)

    def get_all_seasons(self):
        """2010/11~2024/25 시즌 목록 조회"""
        url = f"{self.base_url}/competitions/1/compseasons"
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            seasons = response.json().get('content', [])
            
            # 수동으로 누락된 시즌 추가
            missing_seasons = [
                {'label': '2010/11', 'id': 19},
                {'label': '2011/12', 'id': 20},
                {'label': '2012/13', 'id': 21},
                {'label': '2013/14', 'id': 22},
                {'label': '2014/15', 'id': 27}
            ]
            
            all_seasons = seasons + missing_seasons
            
            # 중복 제거 및 필터링
            seen = set()
            filtered_seasons = []
            for s in all_seasons:
                key = (s['id'], s['label'])
                if key not in seen:
                    seen.add(key)
                    if '/' in s['label']:
                        start_year = int(s['label'].split('/')[0])
                        if 2010 <= start_year <= 2024:
                            s['id'] = int(s['id'])  # ID 정수 변환
                            filtered_seasons.append(s)
            
            # 최신 시즌부터 처리하기 위해 역순 정렬
            return sorted(filtered_seasons, key=lambda x: x['id'], reverse=True)
        except Exception as e:
            logger.error(f"시즌 목록 조회 실패: {str(e)}")
            return []

    def process_season(self, season):
        """단일 시즌 처리 파이프라인"""
        season_id = season['id']
        season_label = season['label'].replace('/', '_')
        season_folder = os.path.join(self.output_folder, season_label)
        
        # 시즌 폴더 생성
        os.makedirs(season_folder, exist_ok=True)
        logger.info(f"시즌 처리 시작: {season_label} ({season_id})")

        # 팀 정보 수집
        teams = self.scrape_teams(season_id, season_folder)
        if teams:
            self.scrape_team_stats(season_id, season_folder)
        
        # 선수 정보 수집
        players = self.scrape_players(season_id, season_folder)
        if players:
            self.scrape_player_info(season_id, players, season_folder)
        
        # 경기 정보 수집
        self.scrape_matches(season_id, season_folder)

    def scrape_teams(self, season_id, folder):
        """팀 기본 정보 수집"""
        url = f"{self.base_url}/teams"
        params = {
            'compSeasons': season_id,
            'comps': 1,
            'pageSize': 30,
            'altIds': 'true'
        }
        
        try:
            response = self.session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            teams = response.json().get('content', [])
            
            team_data = []
            for team in teams:
                team_data.append({
                    'team_id': int(team['id']),
                    'name': team['name'],
                    'short_name': team.get('shortName', ''),
                    'founded': int(team.get('founded', 0)) if team.get('founded') else None,
                    'stadium': team.get('grounds', [{}])[0].get('name'),
                    'capacity': int(team.get('grounds', [{}])[0].get('capacity', 0)) if team.get('grounds', [{}])[0].get('capacity') else None
                })
            
            df = pd.DataFrame(team_data)
            
            # 정수형 컬럼 변환
            int_columns = ['team_id']
            df[int_columns] = df[int_columns].astype('int32')
            
            # founded와 capacity는 None 값이 있을 수 있으므로 별도 처리
            if 'founded' in df.columns:
                df['founded'] = df['founded'].astype('Int32')  # nullable integer
            if 'capacity' in df.columns:
                df['capacity'] = df['capacity'].astype('Int32')  # nullable integer
            
            df.to_csv(os.path.join(folder, 'teams.csv'), index=False)
            logger.info(f"{folder} 팀 정보 저장 완료")
            return team_data
        except Exception as e:
            logger.error(f"팀 정보 수집 실패: {str(e)}")
            return []

    def scrape_team_stats(self, season_id, folder):
        """팀 시즌 통계 수집 (정수형 변환 추가)"""
        url = f"{self.base_url}/standings"
        params = {
            'compSeasons': season_id,
            'altIds': 'true'
        }
        
        try:
            response = self.session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            standings = response.json().get('tables', [{}])[0].get('entries', [])
            
            stats_data = []
            for entry in standings:
                stats_data.append({
                    'team_id': int(entry['team']['id']),
                    'season_id': int(season_id),
                    'position': int(entry.get('position', 0)),
                    'played': int(entry.get('played', 0)),
                    'wins': int(entry.get('won', 0)),
                    'draws': int(entry.get('drawn', 0)),
                    'losses': int(entry.get('lost', 0)),
                    'goals_for': int(entry.get('goalsFor', 0)),
                    'goals_against': int(entry.get('goalsAgainst', 0)),
                    'points': int(entry.get('points', 0)),
                    'clean_sheets': int(entry.get('cleanSheets', 0)),
                    'goal_difference': int(entry.get('goalDifference', 0))
                })
            
            df = pd.DataFrame(stats_data)
            
            # 정수형으로 명시적 변환
            int_columns = ['team_id', 'season_id', 'position', 'played', 'wins', 
                          'draws', 'losses', 'goals_for', 'goals_against', 
                          'points', 'clean_sheets', 'goal_difference']
            df[int_columns] = df[int_columns].astype('int32')
            
            df.to_csv(os.path.join(folder, 'team_stats.csv'), index=False)
            logger.info(f"{folder} 팀 통계 저장 완료")
        except Exception as e:
            logger.error(f"팀 통계 수집 실패: {str(e)}")

    def scrape_players(self, season_id, folder):
        """선수 기본 정보 수집"""
        url = f"{self.base_url}/players"
        params = {
            'compSeasons': season_id,
            'pageSize': 100,
            'page': 0,
            'altIds': 'true'
        }
        
        all_players = []
        while True:
            try:
                response = self.session.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                players = data.get('content', [])
                
                if not players:
                    break
                
                for player in players:
                    all_players.append({
                        'player_id': int(player['id']),
                        'name': player['name']['display'],
                        'position': player.get('info', {}).get('position'),
                        'nationality': player.get('nationalTeam', {}).get('country')
                    })
                
                if params['page'] >= data.get('pageInfo', {}).get('numPages', 0) - 1:
                    break
                    
                params['page'] += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"선수 페이지 {params['page']} 수집 실패: {str(e)}")
                break
        
        if all_players:
            df = pd.DataFrame(all_players)
            
            # 정수형 컬럼 변환
            int_columns = ['player_id']
            df[int_columns] = df[int_columns].astype('int32')
            
            df.to_csv(os.path.join(folder, 'players.csv'), index=False)
            logger.info(f"{folder} 선수 정보 저장 완료")
        return all_players

    def scrape_player_info(self, season_id, players, folder):
        """선수 상세 정보 수집 (정수형 변환 추가)"""
        def process_player(player):
            try:
                url = f"{self.base_url}/stats/player/{player['player_id']}"
                params = {'compSeasons': season_id, 'comps': 1}
                
                response = self.session.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                stats = response.json().get('stats', [])
                
                player_info = {
                    'player_id': int(player['player_id']),
                    'season_id': int(season_id),
                    'appearances': 0,
                    'goals': 0,
                    'assists': 0,
                    'minutes_played': 0,
                    'yellow_cards': 0,
                    'red_cards': 0
                }
                
                for stat in stats:
                    name = stat['name'].lower()
                    value = int(stat['value']) if stat['value'] is not None else 0
                    
                    if 'appearances' in name:
                        player_info['appearances'] = value
                    elif 'goals' in name and 'own' not in name:
                        player_info['goals'] = value
                    elif 'assist' in name:
                        player_info['assists'] = value
                    elif 'mins_played' in name:
                        player_info['minutes_played'] = value
                    elif 'yellow_cards' in name:
                        player_info['yellow_cards'] = value
                    elif 'red_cards' in name:
                        player_info['red_cards'] = value
                
                return player_info
            except Exception as e:
                logger.error(f"선수 {player['player_id']} 정보 오류: {str(e)}")
                return None
        
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(process_player, players))
        
        valid_results = [r for r in results if r]
        if valid_results:
            df = pd.DataFrame(valid_results)
            
            # 결측치 처리 및 타입 변환
            df = df.fillna(0)
            int_columns = ['player_id', 'season_id', 'appearances', 'goals', 'assists', 
                          'minutes_played', 'yellow_cards', 'red_cards']
            df[int_columns] = df[int_columns].astype('int32')
            
            df.to_csv(os.path.join(folder, 'player_stats.csv'), index=False)
            logger.info(f"{folder} 선수 통계 저장 완료")

    def scrape_matches(self, season_id, folder):
        """경기 정보 수집 (정수형 변환 추가)"""
        url = f"{self.base_url}/fixtures"
        params = {
            'compSeasons': season_id,
            'pageSize': 100,
            'page': 0,
            'sort': 'asc',
            'statuses': 'C'
        }
        
        all_matches = []
        while True:
            try:
                response = self.session.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                fixtures = data.get('content', [])
                
                if not fixtures:
                    break
                
                for fixture in fixtures:
                    teams = fixture.get('teams', [])
                    home_team_id = teams[0].get('team', {}).get('id', 0) if len(teams) > 0 else 0
                    away_team_id = teams[1].get('team', {}).get('id', 0) if len(teams) > 1 else 0
                    home_score = teams[0].get('score', 0) if len(teams) > 0 else 0
                    away_score = teams[1].get('score', 0) if len(teams) > 1 else 0
                    
                    all_matches.append({
                        'match_id': int(fixture['id']),
                        'season_id': int(season_id),
                        'date': fixture.get('kickoff', {}).get('label'),
                        'home_team': int(home_team_id),
                        'away_team': int(away_team_id),
                        'home_score': int(home_score) if home_score is not None else 0,
                        'away_score': int(away_score) if away_score is not None else 0,
                        'status': fixture.get('status'),
                        'stadium': fixture.get('ground', {}).get('name'),
                        'attendance': int(fixture.get('attendance', 0)) if fixture.get('attendance') else None
                    })
                
                if params['page'] >= data.get('pageInfo', {}).get('numPages', 0) - 1:
                    break
                    
                params['page'] += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"경기 페이지 {params['page']} 수집 실패: {str(e)}")
                break
        
        if all_matches:
            df = pd.DataFrame(all_matches)
            
            # 정수형 변환
            int_columns = ['match_id', 'season_id', 'home_team', 'away_team', 'home_score', 'away_score']
            df[int_columns] = df[int_columns].astype('int32')
            
            # attendance는 null 값이 있을 수 있으므로 별도 처리
            if 'attendance' in df.columns:
                df['attendance'] = df['attendance'].astype('Int32')  # nullable integer
            
            df.to_csv(os.path.join(folder, 'matches.csv'), index=False)
            logger.info(f"{folder} 경기 정보 저장 완료")

    def run(self):
        """메인 실행 함수"""
        seasons = self.get_all_seasons()
        if not seasons:
            logger.error("시즌 정보를 찾을 수 없습니다.")
            return
        
        logger.info(f"총 {len(seasons)}개 시즌 처리 시작")
        
        for season in seasons:
            start_time = time.time()
            self.process_season(season)
            elapsed = time.time() - start_time
            logger.info(f"{season['label']} 시즌 처리 완료 (소요시간: {elapsed:.2f}초)")
            time.sleep(5)  # API 부하 방지

if __name__ == "__main__":
    scraper = EPLHistoricalScraper()
    scraper.run()
