import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import logging

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
            logger.debug("팀 정보 처리 시작")
            self.process_teams(season, season_folder)
            logger.debug("팀 정보 처리 완료")

            # 2. 팀 통계
            logger.debug("팀 통계 처리 시작")
            self.process_team_stats(season, season_folder)
            logger.debug("팀 통계 처리 완료")

            # 3. 경기 정보
            logger.debug("경기 정보 처리 시작")
            self.process_matches(season, season_folder)
            logger.debug("경기 정보 처리 완료")

            # 4. 선수 정보
            logger.debug("선수 정보 처리 시작")
            self.process_players(season, season_folder)
            logger.debug("선수 정보 처리 완료")

            # 5. 선수 통계
            logger.debug("선수 통계 처리 시작")
            self.process_player_stats(season, season_folder)
            logger.debug("선수 통계 처리 완료")

        except Exception as e:
            logger.error(f"시즌 처리 중 치명적 오류: {str(e)}", exc_info=True)
            raise

        logger.info(f"=== {season['season_name']} 시즌 처리 완료 ===")

    def process_teams(self, season, season_folder):
        """팀 기본 정보 처리"""
        try:
            logger.debug(f"팀 정보 요청: season_id={season['season_id']}")
            response = self.session.get(
                f"{self.base_url}/teams",
                params={
                    'compSeasons': season['season_id'],
                    'comps': 1,
                    'pageSize': 30,
                    'altIds': 'true'
                },
                headers=self.headers
            )
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
                updated = pd.concat([existing, pd.DataFrame(team_data)])
                updated = updated.drop_duplicates('team_id', keep='last')
            else:
                updated = pd.DataFrame(team_data)
            
            updated.to_csv(all_teams_path, index=False)
            logger.info(f"[{season['season_name']}] 팀 정보 저장 완료: {len(team_data)}개 팀")

        except Exception as e:
            logger.error(f"팀 정보 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_team_stats(self, season, season_folder):
        """팀 시즌 통계 처리"""
        try:
            logger.debug(f"팀 통계 요청: season_id={season['season_id']}")
            response = self.session.get(
                f"{self.base_url}/standings",
                params={
                    'compSeasons': season['season_id'],
                    'altIds': 'true'
                },
                headers=self.headers
            )
            response.raise_for_status()
            
            standings = response.json().get('tables', [{}])[0].get('entries', [])
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
            
            pd.DataFrame(stats_data).to_csv(
                os.path.join(season_folder, 'team_info.csv'), 
                index=False
            )
            logger.info(f"[{season['season_name']}] 팀 통계 저장 완료: {len(stats_data)}개 팀")

        except Exception as e:
            logger.error(f"팀 통계 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_matches(self, season, season_folder):
        """경기 정보 처리"""
        try:
            logger.debug(f"경기 정보 요청: season_id={season['season_id']}")
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
                time.sleep(1.5)  # 1.5초 딜레이 추가
            
            pd.DataFrame(all_matches).to_csv(
                os.path.join(season_folder, 'match_info.csv'), 
                index=False
            )
            logger.info(f"[{season['season_name']}] 경기 정보 저장 완료: {len(all_matches)}경기")

        except Exception as e:
            logger.error(f"경기 정보 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_players(self, season, season_folder):
        """선수 기본 정보 처리"""
        try:
            logger.debug(f"선수 정보 요청: season_id={season['season_id']}")
            url = f"{self.base_url}/players"
            params = {
                'compSeasons': season['season_id'],
                'pageSize': 100,
                'page': 0,
                'altIds': 'true'
            }
            
            all_players = []
            total_players = 0
            
            while True:
                response = self.session.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                total_players = data.get('pageInfo', {}).get('totalResults', 0)
                logger.debug(f"선수 페이지 {params['page']+1} 처리 중 ({len(all_players)}/{total_players})")
                
                for player in data.get('content', []):
                    player_data = {
                        'player_id': int(player['id']),
                        'full_name': player['name']['display'],
                        'birth_date': player.get('birth', {}).get('date', {}).get('label', ''),
                        'nationality': player.get('nationalTeam', {}).get('country', ''),
                        'position': player.get('info', {}).get('position', '')
                    }
                    
                    # 외부 사이트 데이터 보강
                    fotmob_data = self.get_fotmob_data(player_data['full_name'])
                    market_value = self.get_transfermarkt_value(player_data['full_name'])
                    
                    player_data.update(fotmob_data)
                    player_data['market_value'] = market_value
                    
                    all_players.append(player_data)
                
                if params['page'] >= data.get('pageInfo', {}).get('numPages', 0) - 1:
                    break
                params['page'] += 1
                time.sleep(1.5)  # 1.5초 딜레이 추가
            
            # 글로벌 선수 정보 저장
            players_path = os.path.join(self.base_folder, 'players.csv')
            if os.path.exists(players_path):
                existing = pd.read_csv(players_path)
                updated = pd.concat([existing, pd.DataFrame(all_players)])
                updated = updated.drop_duplicates('player_id', keep='last')
            else:
                updated = pd.DataFrame(all_players)
            
            updated.to_csv(players_path, index=False)
            logger.info(f"[{season['season_name']}] 선수 정보 저장 완료: {len(all_players)}명")

        except Exception as e:
            logger.error(f"선수 정보 처리 실패: {str(e)}", exc_info=True)
            raise

    def process_player_stats(self, season, season_folder):
        """선수 통계 처리 (FotMob)"""
        try:
            logger.debug(f"선수 통계 처리 시작: season_id={season['season_id']}")
            players_path = os.path.join(self.base_folder, 'players.csv')
            if not os.path.exists(players_path):
                logger.warning("선수 정보 파일이 존재하지 않습니다.")
                return
                
            players_df = pd.read_csv(players_path)
            stats_data = []
            total_players = len(players_df)
            
            for idx, (_, player) in enumerate(players_df.iterrows(), 1):
                if idx % 10 == 0:
                    logger.debug(f"선수 통계 처리 진행: {idx}/{total_players}")
                
                stats = self.get_fotmob_stats(player['full_name'])
                if stats:
                    stats['player_id'] = player['player_id']
                    stats['season_id'] = season['season_id']
                    stats_data.append(stats)
                time.sleep(0.5)  # FotMob 요청 간격
            
            if stats_data:
                pd.DataFrame(stats_data).to_csv(
                    os.path.join(season_folder, 'player_stat.csv'), 
                    index=False
                )
                logger.info(f"[{season['season_name']}] 선수 통계 저장 완료: {len(stats_data)}명")
                
        except Exception as e:
            logger.error(f"선수 통계 처리 실패: {str(e)}", exc_info=True)
            raise

    def get_fotmob_data(self, player_name):
        """FotMob에서 선수 추가 정보 추출"""
        try:
            logger.debug(f"FotMob 요청: {player_name}")
            search_url = f"https://www.fotmob.com/search?q={player_name}"
            res = requests.get(search_url, timeout=10)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            player_link = soup.find('a', class_='css-1gaqulq')['href']
            
            player_url = f"https://www.fotmob.com{player_link}"
            res = requests.get(player_url, timeout=10)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            return {
                'height': self.parse_fotmob_value(soup, 'Height'),
                'number': self.parse_fotmob_value(soup, 'Shirt number'),
                'preferred_foot': self.parse_fotmob_value(soup, 'Preferred foot')
            }
        except Exception as e:
            logger.warning(f"FotMob 데이터 추출 실패: {player_name} - {str(e)}")
            return {}

    def get_fotmob_stats(self, player_name):
        """FotMob에서 선수 통계 추출"""
        try:
            logger.debug(f"FotMob 통계 요청: {player_name}")
            search_url = f"https://www.fotmob.com/search?q={player_name}"
            res = requests.get(search_url, timeout=10)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            player_link = soup.find('a', class_='css-1gaqulq')['href']
            
            player_url = f"https://www.fotmob.com{player_link}"
            res = requests.get(player_url, timeout=10)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            return {
                'appearances': self.parse_fotmob_stat(soup, 'Appearances'),
                'goals': self.parse_fotmob_stat(soup, 'Goals'),
                'assists': self.parse_fotmob_stat(soup, 'Assists'),
                'rating': self.parse_fotmob_stat(soup, 'Rating')
            }
        except Exception as e:
            logger.warning(f"FotMob 통계 추출 실패: {player_name} - {str(e)}")
            return {}

    def parse_fotmob_value(self, soup, label):
        try:
            return soup.find('div', text=label).find_next_sibling().text.strip()
        except:
            return None

    def parse_fotmob_stat(self, soup, label):
        try:
            return float(soup.find('span', text=label).find_next('span').text)
        except:
            return 0

    def get_transfermarkt_value(self, player_name):
        """Transfermarkt에서 시장 가치 추출"""
        try:
            logger.debug(f"Transfermarkt 요청: {player_name}")
            search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name}"
            res = requests.get(
                search_url, 
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            value = soup.find('td', class_='rechts hauptlink').text.strip()
            return float(value.replace('€', '').replace('m', '')) * 1_000_000
        except Exception as e:
            logger.warning(f"Transfermarkt 데이터 추출 실패: {player_name} - {str(e)}")
            return None

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
