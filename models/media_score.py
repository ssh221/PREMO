# football_media_analyzer.py
import re
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article
from textblob import TextBlob
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor
from sklearn.feature_extraction.text import TfidfVectorizer
import feedparser
import numpy as np

# 환경 설정
BBC_BASE_URL = "https://www.bbc.com"
BBC_FOOTBALL_RSS = "https://feeds.bbci.co.uk/sport/football/rss.xml"
PREMIER_LEAGUE_TEAMS = [
    "Arsenal", "Aston Villa", "Brentford", "Brighton", 
    "Chelsea", "Crystal Palace", "Everton", 
    "Leeds United", "Leicester City", "Liverpool", 
    "Manchester City", "Manchester United", "Newcastle United", 
    "Southampton", "Tottenham Hotspur", "West Ham United", 
    "Wolverhampton Wanderers"
]

class FootballMediaAnalyzer:
    def __init__(self):
        self.summarizer = pipeline("summarization", model="t5-small")
        self.articles = []
        self.team_scores = {}

    def fetch_bbc_rss_articles(self, max_articles=100):
        """BBC RSS 피드에서 기사 수집"""
        feed = feedparser.parse(BBC_FOOTBALL_RSS)
        articles = []
        
        for entry in feed.entries[:max_articles]:
            try:
                pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                articles.append({
                    'source': 'BBC RSS',
                    'url': entry.link,
                    'date': pub_date,
                    'title': entry.title,
                    'content': entry.summary,
                    'raw_html': None
                })
            except Exception as e:
                print(f"RSS 처리 오류: {e}")
        
        return articles

    def scrape_bbc_web(self, max_articles=50):
        """BBC 웹사이트에서 기사 수집"""
        articles = []
        page = 1
        
        while len(articles) < max_articles and page <= 5:
            try:
                url = f"{BBC_BASE_URL}/sport/football?page={page}"
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 기사 링크 추출
                links = set()
                for a in soup.find_all('a', href=re.compile(r'/sport/football/.*')):
                    href = a['href']
                    if '/video' not in href and '/av' not in href:
                        links.add(href if href.startswith('http') else f"{BBC_BASE_URL}{href}")
                
                # 기사 처리
                with ThreadPoolExecutor(max_workers=10) as executor:
                    results = executor.map(self.process_article, list(links)[:max_articles//5])
                    articles.extend([res for res in results if res])
                
                page += 1
            except Exception as e:
                print(f"웹 크롤링 오류: {e}")
                break
        
        return articles

    def process_article(self, url):
        """개별 기사 처리"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if not article.text or len(article.text) < 100:
                return None
            
            # 요약 생성
            summary = self.summarizer(
                article.text[:1024], 
                max_length=150, 
                min_length=30, 
                do_sample=False
            )[0]['summary_text']
            
            return {
                'source': 'BBC Web',
                'url': url,
                'date': article.publish_date or datetime.now(),
                'title': article.title,
                'content': article.text,
                'summary': summary,
                'raw_html': article.html
            }
        except Exception as e:
            print(f"기사 처리 오류 [{url}]: {e}")
            return None

    def analyze_sentiment(self, text):
        """텍스트 감성 분석"""
        analysis = TextBlob(text)
        return {
            'polarity': analysis.sentiment.polarity,
            'subjectivity': analysis.sentiment.subjectivity
        }

    def calculate_media_scores(self, articles):
        """팀별 미디어 점수 계산"""
        team_articles = {team: [] for team in PREMIER_LEAGUE_TEAMS}
        
        for article in articles:
            content = f"{article['title']} {article['content']}".lower()
            for team in PREMIER_LEAGUE_TEAMS:
                if team.lower() in content:
                    team_articles[team].append(article)
        
        for team, articles in team_articles.items():
            if not articles:
                self.team_scores[team] = 0
                continue
                
            total_score = 0
            total_weight = 0
            
            for article in articles:
                # 감성 분석
                title_sentiment = self.analyze_sentiment(article['title'])
                content_sentiment = self.analyze_sentiment(article['content'])
                
                # 가중치 계산
                days_old = (datetime.now() - article['date']).days if article['date'] else 0
                time_weight = max(0.1, 1 - days_old/30)
                length_weight = min(1.2, len(article['content'])/3000 + 0.8)
                
                # 종합 점수
                weighted_score = (
                    (title_sentiment['polarity'] * 0.4 + content_sentiment['polarity'] * 0.6) 
                    * time_weight 
                    * length_weight
                )
                
                total_score += weighted_score
                total_weight += time_weight * length_weight
            
            # 점수 스케일링 (-10 ~ 10)
            avg_score = total_score / total_weight if total_weight > 0 else 0
            self.team_scores[team] = int(round(avg_score * 10))

    def generate_keywords(self, team_articles):
        """팀별 키워드 추출"""
        vectorizer = TfidfVectorizer(stop_words='english', max_features=50)
        keywords = {}
        
        for team, articles in team_articles.items():
            if not articles:
                keywords[team] = []
                continue
                
            texts = [f"{a['title']} {a['content']}" for a in articles]
            try:
                tfidf = vectorizer.fit_transform(texts)
                feature_names = vectorizer.get_feature_names_out()
                scores = np.array(tfidf.sum(axis=0)).flatten()
                top_indices = scores.argsort()[-10:][::-1]
                keywords[team] = [feature_names[i] for i in top_indices]
            except:
                keywords[team] = []
        
        return keywords

    def run_analysis(self, max_articles=200):
        """전체 분석 프로세스 실행"""
        print("기사 수집 시작...")
        rss_articles = self.fetch_bbc_rss_articles(100)
        web_articles = self.scrape_bbc_web(100)
        self.articles = [a for a in rss_articles + web_articles if a][:max_articles]
        
        print(f"총 {len(self.articles)}개 기사 수집 완료")
        print("감성 분석 및 점수 계산 중...")
        
        self.calculate_media_scores(self.articles)
        keywords = self.generate_keywords(self._get_team_articles())
        
        # 결과 저장
        df = pd.DataFrame(self.articles)
        df.to_csv('bbc_football_articles.csv', index=False)
        
        scores_df = pd.DataFrame([{
            'Team': team, 
            'Media Score': score, 
            'Keywords': ', '.join(keywords.get(team, []))
        } for team, score in self.team_scores.items()])
        
        scores_df.sort_values('Media Score', ascending=False, inplace=True)
        scores_df.to_csv('team_media_scores.csv', index=False)
        print("분석 완료! 결과 파일 저장됨")

    def _get_team_articles(self):
        """팀별 기사 분류 (내부용)"""
        team_articles = {team: [] for team in PREMIER_LEAGUE_TEAMS}
        for article in self.articles:
            content = f"{article['title']} {article['content']}".lower()
            for team in PREMIER_LEAGUE_TEAMS:
                if team.lower() in content:
                    team_articles[team].append(article)
        return team_articles

if __name__ == "__main__":
    analyzer = FootballMediaAnalyzer()
    analyzer.run_analysis(max_articles=150)
    print("\n최종 미디어 점수:")
    print(pd.read_csv('team_media_scores.csv').to_markdown(index=False))
