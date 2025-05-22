import requests
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("premier_league_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class PremierLeagueScraper:
    def __init__(self, output_folder="premier_league_data", max_workers=4):
        self.output_folder = output_folder
        self.max_workers = max_workers
        self.headers = {
            'Origin': 'https://www.premierleague.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        
        # 세션 설정
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

    def get_seasons(self):
        """시즌 정보 수집 메소드"""
        url = "https://footballapi.pulselive.com/football/competitions/1/compseasons"
        params = {'page': 0, 'pageSize': 100}
        
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict) and 'content' in data:
                return data['content']
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"시즌 정보 수집 실패: {str(e)}")
            return []

    def get_players_page(self, season_id, page=0):
        """선수 페이지 처리"""
        url = "https://footballapi.pulselive.com/football/players"
        params = {
            'pageSize': 30,
            'compSeasons': int(season_id),
            'altIds': 'true',
            'page': page,
            'type': 'player',
            'id': -1,
            'compSeasonId': int(season_id)
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"시즌 {season_id}, 페이지 {page} 오류: {e}")
            return None

    def download_player_image(self, player_id, alt_ids, player_name, season_folder):
        """선수 이미지 다운로드"""
        clean_name = "".join(x for x in player_name if x.isalnum() or x in [' ', '_', '-']).replace(' ', '_')
        image_urls = [
            f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player_id}.png",
            f"https://resources.premierleague.com/premierleague/photos/players/250x250/{player_id}.png"
        ]
        
        if alt_ids:
            image_urls.append(f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{alt_ids.get('opta')}.png")
            image_urls.append(f"https://resources.premierleague.com/premierleague/photos/players/250x250/{alt_ids.get('opta')}.png")

        for url in image_urls:
            try:
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                file_path = os.path.join(season_folder, f"{clean_name}_{player_id}.png")
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return file_path
            except Exception:
                continue
        return None

    def process_player(self, player, season_folder):
        """선수 정보 처리"""
        try:
            player_id = int(player['id'])
            player_data = {
                'player_id': player_id,
                'name': player['name']['display'],
                'nationality': player.get('nationalTeam', {}).get('country', ''),
                'position': player.get('info', {}).get('position', ''),
                'shirt_number': player.get('info', {}).get('shirtNum', '')
            }

            # 이미지 다운로드
            player_data['image_path'] = self.download_player_image(
                player_id,
                player.get('altIds', {}),
                player_data['name'],
                season_folder
            )

            return player_data
        except Exception as e:
            logger.error(f"선수 처리 오류: {e}")
            return None

    def process_season(self, season):
        """시즌 처리"""
        try:
            season_id = season['id']
            season_label = season['label'].replace('/', '_')  # 2023/24 -> 2023_24
            folder_suffix = season_label.replace('20', '').replace('_', '')  # 2324
            season_folder = os.path.join(self.output_folder, f"season_{folder_suffix}")

            if not os.path.exists(season_folder):
                os.makedirs(season_folder)

            logger.info(f"시즌 처리 시작: {season_label} (폴더: {season_folder})")

            all_players = []
            page = 0
            
            while True:
                players_data = self.get_players_page(season_id, page)
                if not players_data or not players_data.get('content'):
                    break
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [
                        executor.submit(self.process_player, p, season_folder) 
                        for p in players_data['content']
                    ]
                    
                    for future in futures:
                        result = future.result()
                        if result:
                            all_players.append(result)
                
                page += 1
                time.sleep(1)

            # CSV 저장
            if all_players:
                df = pd.DataFrame(all_players)
                csv_path = os.path.join(self.output_folder, f"players_{folder_suffix}.csv")
                df.to_csv(csv_path, index=False, encoding='utf-8')
                logger.info(f"CSV 저장 완료: {csv_path}")
            
            return all_players
        except Exception as e:
            logger.error(f"시즌 처리 실패: {e}")
            return []

    def run(self):
        """실행 메인 함수"""
        seasons = self.get_seasons()
        if not seasons:
            logger.error("시즌 정보를 가져올 수 없습니다.")
            return
        
        # 모든 시즌 처리 (최신 시즌부터 내림차순)
        for season in reversed(seasons):
            self.process_season(season)  # ID 필터링 조건 제거

def main():
    scraper = PremierLeagueScraper(max_workers=8)
    scraper.run()

if __name__ == "__main__":
    main()
