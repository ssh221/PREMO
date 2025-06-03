import os
import time
import requests
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

class PLPlayerCrawler:
    def __init__(self, season_id=719):  # 2024/25 시즌 ID
        self.base_url = "https://footballapi.pulselive.com/football"
        self.headers = {
            'Origin': 'https://www.premierleague.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        self.season_id = season_id
        self.stats_mapping = {
            # 기본 정보
            'position': '포지션',
            'preferredfoot': '주발',
            'height': '키(cm)',
            'weight': '몸무게(kg)',
            
            # 경기 참여
            'appearances': '경기 출전',
            'starts': '선발 출전',
            'substitute_in': '교체 투입',
            'substitute_out': '교체 아웃',
            'mins_played': '출전 시간(분)',
            
            # 공격
            'goals': '득점',
            'assists': '어시스트',
            'chances_created': '찬스 창출',
            'shots': '슈팅 시도', 
            'shots_on_target': '유효 슈팅',
            'big_chances_missed': '빅찬스 실패',
            'dribbles': '드리블 성공',
            'offsides': '오프사이드',
            
            # 수비
            'tackles': '태클 시도',
            'tackles_won': '성공 태클', 
            'interceptions': '인터셉트',
            'clearances': '클리어링',
            'blocks': '슈팅 차단',
            'aerial_duels_won': '공중 경합 승리',
            
            # 패스
            'passes': '패스 시도',
            'accurate_passes': '정확한 패스',
            'key_passes': '키 패스',
            'crosses': '크로스',
            'long_balls': '롱 볼',
            'accurate_pass_percent': '패스 성공률',
            
            # 골키퍼
            'saves': '선방',
            'claims': '공중볼 처리',
            'clean_sheets': '무실점',
            'goals_conceded': '실점',
            'penalty_save': '페널티 선방',
            'penalty_faced': '페널티 상황',
            
            # 기타
            'fouls': '파울', 
            'yellow_cards': '옐로카드',
            'red_cards': '레드카드',
            'rating': '평점',
            'dispossessed': '볼 소유권 상실'
        }

    def get_all_players(self):
        """선수 기본 정보 수집"""
        players = []
        page = 0
        while True:
            url = f"{self.base_url}/players"
            params = {
                'compSeasons': self.season_id,
                'pageSize': 100,
                'page': page,
                'altIds': 'true'
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                for player in data['content']:
                    players.append({
                        'player_id': int(player['id']),
                        'name': player['name']['display'],
                        'position': player.get('info', {}).get('position', ''),
                        'preferredfoot': player.get('info', {}).get('preferredFoot', ''),
                        'height': player.get('info', {}).get('height', ''),
                        'weight': player.get('info', {}).get('weight', ''),
                        'nationality': player.get('nationalTeam', {}).get('country', '')
                    })
                
                if page >= data['pageInfo']['numPages'] - 1:
                    break
                page += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"선수 목록 조회 실패: {str(e)}")
                break
        
        return players

    def get_player_stats(self, player_id):
        """선수 통계 수집 (강화된 버전)"""
        try:
            url = f"{self.base_url}/stats/player/{player_id}"
            params = {'compSeasons': self.season_id, 'comps': 1}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 기본 정보 초기화
            stat_dict = {
                'player_id': player_id,
                'current_team_id': data.get('entity', {}).get('currentTeam', {}).get('id', 0)
            }
            
            # 통계 데이터 파싱
            for stat in data.get('stats', []):
                name = stat['name'].lower().replace(' ', '_')
                value = stat.get('value', 0)
                
                # 특수 케이스: 페널티
                if name == 'penalty_save':
                    faced = next((s['value'] for s in data['stats'] if s['name'].lower() == 'penalty_faced'), 0)
                    stat_dict['페널티 선방'] = f"{int(value)}/{int(faced)}"
                elif name in self.stats_mapping:
                    # 데이터 타입 변환
                    if isinstance(value, (int, float)):
                        if name in ['rating', 'accurate_pass_percent']:
                            stat_dict[self.stats_mapping[name]] = round(float(value), 1)
                        else:
                            stat_dict[self.stats_mapping[name]] = int(value)
                    else:
                        stat_dict[self.stats_mapping[name]] = 0

            return stat_dict
            
        except Exception as e:
            logger.error(f"선수 {player_id} 통계 조회 실패: {str(e)}")
            return None

    def save_to_csv(self, data, filename):
        """CSV 저장 (NaN/Inf 완전 제거 및 안전한 타입 변환)"""
        
        df = pd.DataFrame(data)
        
        # 1. 모든 NaN/Inf 값을 0으로 대체
        df = df.replace([np.inf, -np.inf], np.nan)  # 먼저 inf를 NaN으로 변환
        df = df.fillna(0)
        
        # 2. 숫자형 컬럼 동적 검출
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        
        # 3. 각 컬럼별 안전한 타입 변환
        for col in numeric_cols:
            try:
                # 먼저 float으로 변환 (문자열 등이 섞인 경우 처리)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # 다시 NaN/Inf 처리
                df[col] = df[col].replace([np.inf, -np.inf], 0).fillna(0)
                # 정수 변환 시도
                if (df[col] % 1 == 0).all():
                    df[col] = df[col].astype(int)
                else:
                    df[col] = df[col].astype(float)
            except Exception as e:
                logger.error(f"컬럼 {col} 처리 실패: {str(e)}")
                continue
        
        # 4. 컬럼 순서 정렬
        meta_cols = ['player_id', 'current_team_id', '포지션', '주발', '키(cm)', '몸무게(kg)']
        other_cols = [col for col in df.columns if col not in meta_cols]
        ordered_cols = meta_cols + other_cols
        
        df = df.reindex(columns=ordered_cols)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"{filename} 저장 완료 ({len(df)}건)")


    def run(self):
        # 선수 기본 정보 수집
        logger.info("선수 기본 정보 수집 시작...")
        players = self.get_all_players()
        self.save_to_csv(players, 'players_meta.csv')
        
        # 선수 통계 병렬 수집
        logger.info("선수 통계 수집 시작...")
        stats_data = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.get_player_stats, p['player_id']): p for p in players}
            
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                if result:
                    stats_data.append(result)
                if (i+1) % 50 == 0:
                    logger.info(f"진행 현황: {i+1}/{len(players)}")
                time.sleep(0.5)
        
        # 최종 저장
        self.save_to_csv(stats_data, 'player_full_stats_24_25.csv')

if __name__ == "__main__":
    crawler = PLPlayerCrawler()
    crawler.run()
