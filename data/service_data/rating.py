import requests
import pandas as pd
import time
import random
from itertools import cycle
from fake_useragent import UserAgent
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class AdvancedSofascoreCrawler:
    def __init__(self, proxy_list=None):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.ua = UserAgent()
        self.proxy_pool = cycle(proxy_list) if proxy_list else None
        self.session = self._create_session()
        self.headers = self._generate_headers()

    def _create_session(self):
        """재시도 전략이 적용된 세션 생성"""
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=frozenset(['GET'])
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def _generate_headers(self):
        """동적으로 헤더 생성"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.sofascore.com/',
            'Origin': 'https://www.sofascore.com',
            'DNT': '1'
        }

    def _rotate_proxy(self):
        """프록시 회전 로직"""
        return {'http': next(self.proxy_pool)} if self.proxy_pool else None

    def _make_request(self, url, params=None):
        """개선된 요청 처리 메커니즘"""
        for attempt in range(3):
            try:
                proxies = self._rotate_proxy()
                self.headers['User-Agent'] = self.ua.random
                
                response = self.session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    proxies=proxies,
                    timeout=10,
                    verify=True
                )
                
                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                print(f"Attempt {attempt+1} failed: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        return None

    def get_season_id(self, tournament_id=17):
        """시즌 ID 획득 로직 강화"""
        url = f"{self.base_url}/unique-tournament/{tournament_id}/seasons"
        data = self._make_request(url)
        return data['seasons'][0]['id'] if data else None

    def crawl_player_stats(self, season_id):
        """선수 통계 크롤링 핵심 로직"""
        all_players = []
        limit = 100
        offset = 0

        while True:
            params = {
                'limit': limit,
                'offset': offset,
                'accumulation': 'total',
                'group': 'summary'
            }
            
            url = f"{self.base_url}/unique-tournament/17/season/{season_id}/statistics"
            data = self._make_request(url, params)
            
            if not data or not data.get('results'):
                break

            all_players.extend(data['results'])
            offset += limit
            time.sleep(random.uniform(1, 3))  # 랜덤 지연

        return all_players

    def process_data(self, raw_data):
        """데이터 처리 파이프라인"""
        processed = []
        for player in raw_data:
            processed.append({
                'player_id': player['player']['id'],
                'name': player['player']['name'],
                'team': player['team']['name'],
                'position': player['player']['position'],
                'rating': player['statistics']['rating'],
                'appearances': player['statistics']['appearances'],
                'goals': player['statistics'].get('goals', 0),
                'assists': player['statistics'].get('assists', 0)
            })
        return pd.DataFrame(processed)

    def execute(self):
        """크롤링 실행 엔트리 포인트"""
        season_id = self.get_season_id()
        if not season_id:
            raise ValueError("Season ID를 획득할 수 없습니다")

        raw_data = self.crawl_player_stats(season_id)
        df = self.process_data(raw_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"premier_league_ratings_{timestamp}.xlsx"
        df.to_excel(filename, index=False)
        return df

# 사용 예시
if __name__ == "__main__":
    # 프록시 목록 (실제 유효한 프록시로 교체 필요)
    PROXIES = [
        'http://user:pass@proxy1:port',
        'http://user:pass@proxy2:port',
        'http://user:pass@proxy3:port'
    ]

    crawler = AdvancedSofascoreCrawler(proxy_list=PROXIES)
    
    try:
        result_df = crawler.execute()
        print("크롤링 성공:\n", result_df.head())
    except Exception as e:
        print(f"크롤링 실패: {str(e)}")
