import os
import time
import requests
import pandas as pd
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("epl_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('epl_crawler')

class EPLDataCrawler:
    def __init__(self, base_folder="epl_data"):
        self.base_url = "https://footballapi.pulselive.com/football"
        self.headers = {
            'Origin': 'https://www.premierleague.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        self.base_folder = base_folder
        
        # 세션 설정
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        os.makedirs(base_folder, exist_ok=True)


    def get_seasons(self):
        """시즌 정보 수집 (2017/18~2024/25)"""
        try:
            logger.debug("시즌 정보 요청 시작")
            response = self.session.get(
                f"{self.base_url}/competitions/1/compseasons",
                headers=self.headers
            )
            response.raise_for_status()
            seasons = response.json().get('content', [])
            
            filtered = []
            for s in seasons:
                if '/' in s['label']:
                    start_year = int(s['label'].split('/')[0])
                    if 2017 <= start_year <= 2024:
                        filtered.append({
                            'season_id': int(s['id']),
                            'season_name': s['label'].replace('/', ''),
                            'start_date': s.get('startDate', ''),
                            'end_date': s.get('endDate', '')
                        })
            logger.info(f"수집된 시즌 개수: {len(filtered)}")
            return sorted(filtered, key=lambda x: x['season_id'])
            
        except Exception as e:
            logger.error(f"시즌 정보 조회 실패: {str(e)}", exc_info=True)
            return []

    def process_season(self, season):
        """시즌별 데이터 처리 파이프라인"""
        logger.debug(f"=== {season['season_name']} 시즌 처리 시작 ===")
        season_folder = os.path.join(self.base_folder, season['season_name'])
        os.makedirs(season_folder, exist_ok=True)

        try:
            # 1. 팀 기본 정보
            self.process_teams(season, season_folder)
            
            # 2. 팀 통계
            self.process_team_stats(season, season_folder)
            
            # 3. 경기 정보
            self.process_matches(season, season_folder)
            
            # 4. 선수 정보 (반드시 player_stats 이전에 실행)
            self.process_players(season, season_folder)
            
            # 5. 선수 통계
            self.process_player_stats(season, season_folder)

        except Exception as e:
            logger.error(f"시즌 처리 중 치명적 오류: {str(e)}", exc_info=True)
            raise

        logger.info(f"=== {season['season_name']} 시즌 처리 완료 ===")


    def process_teams(self, season, season_folder):
        """팀 기본 정보 처리"""
        try:
            logger.debug(f"[{season['season_name']}] 팀 정보 수집 시작")
            url = f"{self.base_url}/teams"
            params = {
                'compSeasons': season['season_id'],
                'comps': 1,
                'pageSize': 30,
                'altIds': 'true'
            }
            
            response = self.session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            teams = response.json().get('content', [])
            
            team_data = []
            for team in teams:
                team_data.append({
                    'team_id': int(team['id']),
                    'team_common_name': team['name'],
                    'short_name': team.get('shortName', ''),
                    'stadium_name': team.get('grounds', [{}])[0].get('name', '')
                })
            
            # 글로벌 팀 정보 저장
            all_teams_path = os.path.join(self.base_folder, 'teams.csv')
            if os.path.exists(all_teams_path):
                existing = pd.read_csv(all_teams_path)
                updated = pd.concat([existing, pd.DataFrame(team_data)]).drop_duplicates('team_id')
            else:
                updated = pd.DataFrame(team_data)
            updated.to_csv(all_teams_path, index=False)
            
            logger.info(f"[{season['season_name']}] 팀 정보 저장 완료: {len(team_data)}개 팀")

        except Exception as e:
            logger.error(f"팀 정보 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_team_stats(self, season, season_folder):
        """팀 시즌 통계 처리 (완전한 데이터 수집)"""
        try:
            logger.debug(f"[{season['season_name']}] 팀 통계 수집 시작")
            url = f"{self.base_url}/standings"
            params = {
                'compSeasons': season['season_id'],
                'altIds': 'true'
            }
            
            response = self.session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            standings = data.get('tables', [{}])[0].get('entries', [])
            stats_data = []
            
            for entry in standings:
                stats_data.append({
                    'team_id': int(entry['team']['id']),
                    'season_id': season['season_id'],
                    'wins': entry.get('won', 0),
                    'draws': entry.get('drawn', 0),
                    'losses': entry.get('lost', 0),
                    'goals_scored': entry.get('goalsFor', 0),
                    'goals_conceded': entry.get('goalsAgainst', 0),
                    'points': entry.get('points', 0),
                    'position_in_table': entry.get('position', 0),
                    'matches_played': entry.get('played', 0)
                })
            
            # 데이터 형식 강제 변환 및 기본값 처리
            df = pd.DataFrame(stats_data)
            int_columns = ['wins', 'draws', 'losses', 'goals_scored', 
                        'goals_conceded', 'points', 'matches_played']
            df[int_columns] = df[int_columns].astype(int)
            df.fillna(0, inplace=True)
            
            df.to_csv(
                os.path.join(season_folder, 'team_info.csv'), 
                index=False,
                columns=[
                    'team_id', 'season_id', 'wins', 'draws', 'losses',
                    'goals_scored', 'goals_conceded', 'points', 
                    'position_in_table', 'matches_played'
                ]
            )
            logger.info(f"[{season['season_name']}] 팀 통계 저장 완료: {len(stats_data)}개 팀")

        except Exception as e:
            logger.error(f"팀 통계 처리 실패: {str(e)}", exc_info=True)
            raise


    def process_matches(self, season, season_folder):
        """경기 정보 처리"""
        try:
            logger.debug(f"[{season['season_name']}] 경기 정보 수집 시작")
            url = f"{self.base_url}/fixtures"
            params = {
                'compSeasons': season['season_id'],
                'pageSize': 100,
                'page': 0,
                'sort': 'asc'
            }
            
            all_matches = []
            total_pages = 0
            
            while True:
                response = self.session.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                # 페이지 정보 추출
                total_pages = data.get('pageInfo', {}).get('numPages', 0)
                logger.debug(f"페이지 {params['page']+1}/{total_pages} 처리 중")
                
                for fixture in data.get('content', []):
                    all_matches.append({
                        'match_id': int(fixture['id']),
                        'season_id': season['season_id'],
                        'home_team_id': int(fixture.get('teams', [{}])[0].get('team', {}).get('id', 0)),
                        'away_team_id': int(fixture.get('teams', [{}])[1].get('team', {}).get('id', 0)),
                        'start_time': fixture.get('kickoff', {}).get('label', ''),
                        'home_goals': fixture.get('teams', [{}])[0].get('score', 0),
                        'away_goals': fixture.get('teams', [{}])[1].get('score', 0),
                        'status': fixture.get('status', '')
                    })
                
                if params['page'] >= total_pages - 1:
                    break
                params['page'] += 1
                time.sleep(1.5)
            
            pd.DataFrame(all_matches).to_csv(
                os.path.join(season_folder, 'match_info.csv'), 
                index=False
            )
            logger.info(f"[{season['season_name']}] 경기 정보 저장 완료: {len(all_matches)}경기")

        except Exception as e:
            logger.error(f"경기 정보 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_players(self, season, season_folder):
        """선수 기본 정보 처리 (시즌별 선수 누적 저장)"""
        try:
            logger.debug(f"[{season['season_name']}] 선수 정보 수집 시작")
            url = f"{self.base_url}/players"
            params = {
                'compSeasons': season['season_id'],
                'pageSize': 100,
                'page': 0,
                'altIds': 'true'
            }
            
            current_season_players = []
            while True:
                response = self.session.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                for player in data.get('content', []):
                    player_data = {
                        'player_id': int(player['id']),
                        'full_name': player['name']['display'],
                        'birth_date': player.get('birth', {}).get('date', {}).get('label', ''),
                        'nationality': player.get('nationalTeam', {}).get('country', ''),
                        'position': player.get('info', {}).get('position', '')
                    }
                    current_season_players.append(player_data)
                
                if params['page'] >= data.get('pageInfo', {}).get('numPages', 0) - 1:
                    break
                params['page'] += 1
                time.sleep(1.5)
            
            # 글로벌 선수 정보 업데이트
            all_players_path = os.path.join(self.base_folder, 'players.csv')
            if os.path.exists(all_players_path):
                existing_players = pd.read_csv(all_players_path)
                new_players = pd.DataFrame(current_season_players)
                combined = pd.concat([existing_players, new_players]).drop_duplicates('player_id', keep='first')
            else:
                combined = pd.DataFrame(current_season_players)
            
            combined.to_csv(all_players_path, index=False)
            logger.info(f"[{season['season_name']}] 선수 정보 저장 완료: {len(current_season_players)}명")

            # 현재 시즌 선수 ID 저장
            current_season_player_ids = [p['player_id'] for p in current_season_players]
            pd.Series(current_season_player_ids, name='player_id').to_csv(
                os.path.join(season_folder, 'current_players.csv'), 
                index=False
            )

        except Exception as e:
            logger.error(f"선수 정보 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_player_stats(self, season, season_folder):
        """시즌별 선수 통계 처리 (현재 시즌 선수만 대상)"""
        try:
            logger.debug(f"[{season['season_name']}] 선수 통계 수집 시작")
            
            # 현재 시즌 선수 목록 로드
            current_players_path = os.path.join(season_folder, 'current_players.csv')
            if not os.path.exists(current_players_path):
                logger.warning(f"{current_players_path} 파일 없음")
                return
                
            current_players = pd.read_csv(current_players_path)['player_id'].tolist()
            stats_data = []
            
            # 병렬 처리
            MAX_WORKERS = 10
            CHUNK_SIZE = 50

            def process_player(player_id):
                try:
                    url = f"{self.base_url}/stats/player/{player_id}"
                    params = {
                        'compSeasons': season['season_id'],
                        'comps': 1
                    }
                    response = self.session.get(url, params=params, headers=self.headers)
                    response.raise_for_status()
                    
                    stats = response.json().get('stats', [])
                    stat_entry = {
                        'player_id': player_id,
                        'season_id': season['season_id'],
                        'appearances': 0,
                        'goals': 0,
                        'assists': 0,
                        'clean_sheets': 0,
                        'minutes_played': 0,
                        'yellow_cards': 0,
                        'red_cards': 0
                    }
                    
                    for stat in stats:
                        name = stat['name'].lower()
                        value = stat.get('value', 0)
                        
                        if name == 'appearances':
                            stat_entry['appearances'] = int(value)
                        elif name == 'goals':
                            stat_entry['goals'] = int(value)
                        elif name == 'goal_assist':
                            stat_entry['assists'] = int(value)
                        elif name == 'clean_sheet':
                            stat_entry['clean_sheets'] = int(value)
                        elif name == 'mins_played':
                            stat_entry['minutes_played'] = int(value)
                        elif name == 'yellow_cards':
                            stat_entry['yellow_cards'] = int(value)
                        elif name == 'red_cards':
                            stat_entry['red_cards'] = int(value)
                    
                    return stat_entry
                    
                except Exception as e:
                    logger.error(f"선수 {player_id} 통계 조회 실패: {str(e)}")
                    return None

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(process_player, pid): pid for pid in current_players}
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        stats_data.append(result)
                    if len(stats_data) % 100 == 0:
                        logger.info(f"처리 진행: {len(stats_data)}/{len(current_players)}")

            if stats_data:
                df = pd.DataFrame(stats_data)
                # 데이터 형식 변환
                int_columns = ['player_id', 'season_id', 'appearances', 'goals', 'assists', 
                              'clean_sheets', 'minutes_played', 'yellow_cards', 'red_cards']
                df[int_columns] = df[int_columns].astype(int)
                
                df.to_csv(
                    os.path.join(season_folder, 'player_stat.csv'), 
                    index=False,
                    columns=int_columns  # DB 스키마 순서 준수
                )
                logger.info(f"[{season['season_name']}] 선수 통계 저장 완료: {len(stats_data)}건")
                
        except Exception as e:
            logger.error(f"선수 통계 처리 실패: {str(e)}", exc_info=True)
            raise

    def run(self):
        seasons = self.get_seasons()
        logger.info(f"처리할 총 시즌 수: {len(seasons)}")
        
        for idx, season in enumerate(seasons, 1):
            logger.info(f"[{idx}/{len(seasons)}] {season['season_name']} 시즌 처리 시작")
            start_time = time.time()
            
            try:
                self.process_season(season)
            except Exception as e:
                logger.error(f"시즌 처리 실패: {season['season_name']}", exc_info=True)
                continue
                
            elapsed = time.time() - start_time
            logger.info(f"[{idx}/{len(seasons)}] {season['season_name']} 처리 완료 (소요시간: {elapsed:.2f}초)\n")

if __name__ == "__main__":
    crawler = EPLDataCrawler()
    crawler.run()
