import time
import os
import tempfile
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

def get_player_list(driver, team_squad_url):
    """
    팀 스쿼드 페이지에서 감독을 제외한 모든 선수의 이름과 상대 URL을 추출합니다.
    """
    wait = WebDriverWait(driver, 15)
    player_info_list = []
    
    print(f"\n'{team_squad_url}' 접속: 선수 목록 수집 시작...")
    driver.get(team_squad_url)

    squad_table_selector = "table[class*='Squad']"
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, squad_table_selector)))
    player_rows = driver.find_elements(By.CSS_SELECTOR, f"{squad_table_selector} tr")

    for row in player_rows:
        try:
            link_element = row.find_element(By.CSS_SELECTOR, "a[href*='/players/']")
            player_name = link_element.find_element(By.CSS_SELECTOR, "span[class*='SquadPlayerName']").text
            relative_url = link_element.get_attribute('href')
            if player_name and relative_url:
                player_info_list.append({"name": player_name, "url": relative_url})
        except (NoSuchElementException, StaleElementReferenceException):
            continue
    
    if player_info_list:
        print(f"'{player_info_list[0]['name']}' 감독 제외.")
        return player_info_list[1:]
    return []

def get_player_details(driver, player_url):
    """
    선수 개인 페이지에서 공통 정보, 주 포지션, 시즌 성적을 모두 추출합니다.
    StaleElementReferenceException에 대한 재시도 로직을 포함합니다.
    """
    details = {}
    for attempt in range(3): # 최대 3번 재시도
        try:
            driver.get(player_url)
            wait = WebDriverWait(driver, 10)
            
            # 1. 바이오 정보 추출
            bio_stats = {}
            bio_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='PlayerBioCSS']")))
            stats = bio_container.find_elements(By.CSS_SELECTOR, "div[class*='PlayerBioStatCSS']")
            for stat in stats:
                try:
                    title = stat.find_element(By.CSS_SELECTOR, "div[class*='StatTitleCSS'] > span").text.strip().lower()
                    value = stat.find_element(By.CSS_SELECTOR, "div[class*='StatValueCSS']").text.strip()
                    if title in ['height', 'shirt', 'preferred foot', 'market value']:
                        bio_stats[title.replace(' ', '_')] = value
                except NoSuchElementException:
                    continue
            details.update(bio_stats)

            # 2. 주 포지션 추출
            try:
                position_badge = driver.find_element(By.CSS_SELECTOR, "div[class*='-Badge '][title]")
                details['primary_position'] = position_badge.text.strip()
            except NoSuchElementException:
                details['primary_position'] = 'N/A'


            # 3. 시즌 성적 추출
            season_stats = {}
            stats_container = driver.find_element(By.CSS_SELECTOR, "div[class*='StatsContainer']")
            stat_boxes = stats_container.find_elements(By.CSS_SELECTOR, "div[class*='StatBox']")
            for box in stat_boxes:
                try:
                    title = box.find_element(By.CSS_SELECTOR, "span[class*='StatTitle']").text.strip().lower().replace(' ', '_')
                    value = box.find_element(By.CSS_SELECTOR, "[class*='StatValue'], [class*='PlayerRating']").text.strip()
                    season_stats[title] = value
                except NoSuchElementException:
                    continue
            details['season_stats'] = season_stats
            
            return details # 성공 시 즉시 반환

        except StaleElementReferenceException:
            print(f"  - Stale element 오류 발생. 재시도합니다... ({attempt + 1}/3)")
            time.sleep(2)
        except TimeoutException:
            print(f"  - 페이지 로딩 시간 초과. 다음 선수로 넘어갑니다.")
            return {}
        except Exception as e:
            print(f"  - 상세 정보 수집 중 알 수 없는 오류: {e}")
            return {}
            
    return {} # 모든 재시도 실패 시

def save_to_csv(data_list, filename):
    """
    주어진 데이터를 CSV 파일로 저장합니다.
    """
    if not data_list:
        return

    headers = set()
    for item in data_list:
        headers.update(item.keys())
    
    # URL은 최종 결과에 필요 없으므로 헤더에서 제외
    headers.discard('url')
    
    preferred_order = ['name', 'primary_position', 'height', 'shirt', 'preferred_foot', 'market_value']
    sorted_headers = sorted(list(headers), key=lambda x: (x not in preferred_order, x))

    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted_headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
        print(f"\n'{filename}' 파일이 업데이트되었습니다. (총 {len(data_list)}명 데이터)")
    except Exception as e:
        print(f"CSV 저장 중 오류 발생: {e}")


# --- 메인 스크립트 실행 부분 ---
if __name__ == "__main__":
    team_urls = [
        "https://www.fotmob.com/en-GB/teams/8650/squad/liverpool",
        "https://www.fotmob.com/en-GB/teams/9825/squad/arsenal",
        "https://www.fotmob.com/en-GB/teams/8456/squad/manchester-city",
        "https://www.fotmob.com/en-GB/teams/8455/squad/chelsea",
        "https://www.fotmob.com/en-GB/teams/10261/squad/newcastle-united",
        "https://www.fotmob.com/en-GB/teams/10252/squad/aston-villa",
        "https://www.fotmob.com/en-GB/teams/10203/squad/nottingham-forest",
        "https://www.fotmob.com/en-GB/teams/10204/squad/brighton-hove-albion",
        "https://www.fotmob.com/en-GB/teams/8678/squad/afc-bournemouth",
        "https://www.fotmob.com/en-GB/teams/9937/squad/brentford",
        "https://www.fotmob.com/en-GB/teams/9879/squad/fulham",
        "https://www.fotmob.com/en-GB/teams/9826/squad/crystal-palace",
        "https://www.fotmob.com/en-GB/teams/8668/squad/everton",
        "https://www.fotmob.com/en-GB/teams/8654/squad/west-ham-united"
        "https://www.fotmob.com/en-GB/teams/10260/squad/manchester-united",
        "https://www.fotmob.com/en-GB/teams/8602/squad/wolverhampton-wanderers",
        "https://www.fotmob.com/en-GB/teams/8586/squad/tottenham-hotspur",
        "https://www.fotmob.com/en-GB/teams/8197/squad/leicester-city",
        "https://www.fotmob.com/en-GB/teams/9902/squad/ipswich-town",
        "https://www.fotmob.com/en-GB/teams/8466/squad/southampton"
    ]
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    user_data_dir = os.path.join(tempfile.gettempdir(), f'selenium_chrome_profile_{os.getpid()}')
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    base_url = "https://www.fotmob.com"

    # 전체 데이터를 누적할 리스트
    all_goalkeepers_data = []
    all_outfield_players_data = []

    for team_url in team_urls:
        players = get_player_list(driver, team_url)
        
        if not players:
            print(f"'{team_url}'에서 선수 정보를 찾지 못해 다음 팀으로 넘어갑니다.")
            continue
            
        print(f"총 {len(players)}명의 선수 정보를 찾았습니다. 각 선수 페이지에서 상세 스탯을 추출합니다...")
        
        for i, player in enumerate(players):
            print(f"({i+1}/{len(players)}) {player['name']} 선수 데이터 처리 중...")
            
            full_player_url = player['url']
            details = get_player_details(driver, full_player_url)
            
            if details:
                # 기본 정보와 상세 정보를 결합
                player_full_data = player.copy()
                player_full_data['primary_position'] = details.get('primary_position')
                player_full_data['height'] = details.get('height')
                player_full_data['shirt'] = details.get('shirt')
                player_full_data['preferred_foot'] = details.get('preferred_foot')
                player_full_data['market_value'] = details.get('market_value')
                
                # 시즌 스탯 추가
                if 'season_stats' in details:
                    player_full_data.update(details['season_stats'])
                
                # 포지션에 따라 데이터 리스트에 추가
                # 주 포지션(primary_position)을 기준으로 GK 여부 판단
                if details.get('primary_position') == 'GK':
                    all_goalkeepers_data.append(player_full_data)
                else:
                    all_outfield_players_data.append(player_full_data)
            
            time.sleep(1) # 서버 부하 방지

        # 한 팀의 작업이 끝날 때마다 현재까지 누적된 전체 데이터를 CSV 파일로 덮어쓰기
        print(f"'{team_url.split('/')[-1]}' 팀의 데이터 수집 완료. CSV 파일을 업데이트합니다...")
        save_to_csv(all_goalkeepers_data, "all_teams_goalkeepers_detailed_stats.csv")
        save_to_csv(all_outfield_players_data, "all_teams_outfield_players_detailed_stats.csv")
    
    driver.quit()
    print("\n모든 작업이 완료되었습니다.")
