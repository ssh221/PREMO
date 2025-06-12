import time
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

def get_players_from_team(team_squad_url):
    """
    주어진 팀 스쿼드 URL에서 모든 선수의 이름과 개인 페이지 URL을 추출합니다.
    """
    # Selenium WebDriver 설정 (세션 충돌 방지 옵션 포함)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 각 실행마다 고유한 임시 폴더를 사용하도록 설정
    user_data_dir = os.path.join(tempfile.gettempdir(), f'selenium_chrome_profile_{os.getpid()}')
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    players_data = []
    base_url = "https://www.fotmob.com"

    try:
        print(f"'{team_squad_url}' 페이지에 접속하여 선수 목록을 가져옵니다...")
        driver.get(team_squad_url)

        # 선수 목록을 포함하는 링크(<a> 태그)가 최소 10개 이상 로드될 때까지 기다림
        # 이 선택자는 선수 개인 페이지로 연결되는 링크를 직접 가리킵니다.
        player_link_selector = "a.css-9pqpod-SquadPlayerLink" # 클래스 기반 선택자
        
        # 더 안정적인 data-testid 선택자 (존재할 경우 우선 사용)
        # player_link_selector = "a[data-testid^='player-link-']"

        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, player_link_selector)) >= 10)
        
        # 페이지의 모든 선수 링크 요소를 가져옵니다.
        player_links = driver.find_elements(By.CSS_SELECTOR, player_link_selector)
        
        for link_element in player_links:
            # 선수 이름 추출
            player_name = link_element.find_element(By.CSS_SELECTOR, "span[class*='SquadPlayerName']").text
            
            # href 속성에서 상대 URL 추출
            relative_url = link_element.get_attribute('href')
            
            # 완전한 URL로 조합
            full_url = relative_url
            
            players_data.append({
                "name": player_name,
                "url": full_url
            })
            
    except TimeoutException:
        print("선수 목록을 로드하는 데 실패했습니다 (타임아웃).")
    except Exception as e:
        print(f"데이터를 가져오는 중 오류 발생: {e}")
    finally:
        driver.quit()
        
    return players_data

# --- 스크립트 실행 부분 ---
if __name__ == "__main__":
    # 테스트할 팀의 스쿼드 페이지 URL
    liverpool_squad_url = "https://www.fotmob.com/en-GB/teams/8650/squad/liverpool"
    
    # 함수 호출
    liverpool_players = get_players_from_team(liverpool_squad_url)
    
    if liverpool_players:
        print(f"\n--- 리버풀 팀 선수 목록 (총 {len(liverpool_players)}명) ---")
        for player in liverpool_players:
            print(f"  선수: {player['name']}, URL: {player['url']}")

