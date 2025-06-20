/**
 * 경기 미리보기 페이지 스크립트
 * 탭 전환 및 인사이트, 뉴스 데이터 관리
 */

// DOM이 완전히 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 탭 전환 기능 초기화
    initTabs();
    
    // 경기 정보 로드
    loadMatchPreview();
});

/**
 * 탭 기능 초기화
 */
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 현재 활성화된 탭을 비활성화
            document.querySelector('.tab.active').classList.remove('active');
            
            // 클릭한 탭 활성화
            this.classList.add('active');
            
            // 데이터 탭 값 가져오기
            const tabName = this.getAttribute('data-tab');
            
            // 해당 탭의 콘텐츠 로드
            loadTabContent(tabName);
        });
    });
}

/**
 * 탭 콘텐츠 로드 함수
 * @param {string} tabName - 탭 이름 ('preview', 'premo', 'h2h', 'table')
 */
function loadTabContent(tabName) {
    console.log(`${tabName} 탭 콘텐츠를 로드합니다.`);
    
    // 실제 구현에서는 탭에 따라 다른 API 호출 또는 콘텐츠 로드
    /*
    fetch(`/api/match/${getMatchId()}/${tabName}`)
        .then(response => response.json())
        .then(data => {
            // 탭에 따라 다른 콘텐츠 렌더링
            renderTabContent(tabName, data);
        })
        .catch(error => {
            console.error(`${tabName} 탭 콘텐츠를 로드하는 중 오류가 발생했습니다:`, error);
        });
    */
    
    // 현재는 기본 Preview 탭만 표시되므로 추가 구현 없음
    if (tabName !== 'preview') {
        alert(`${tabName} 탭은 현재 구현 중입니다.`);
    }
}

/**
 * 현재 URL에서 경기 ID 추출 (예시 함수)
 * @returns {string} 경기 ID
 */
function getMatchId() {
    // URL에서 ID 파라미터 추출 (예: ?id=123)
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || '1'; // 기본값 1
}

/**
 * 경기 미리보기 정보 로드 함수
 */
function loadMatchPreview() {
    const matchId = getMatchId();
    console.log(`경기 ID ${matchId}의 미리보기 정보를 로드합니다.`);
    
    // 실제 구현에서는 API에서 경기 정보 가져오기
    /*
    fetch(`/api/match/${matchId}/preview`)
        .then(response => response.json())
        .then(data => {
            updateMatchHeader(data);
            updateInsights(data.insights);
            updateNews(data.news);
        })
        .catch(error => {
            console.error('경기 미리보기 정보를 로드하는 중 오류가 발생했습니다:', error);
        });
    */
    
    // 현재는 미리 작성된 HTML로 표시
}

/**
 * 경기 헤더 정보 업데이트 함수 (실제 API 구현 시 사용)
 * @param {Object} data - 경기 데이터
 */
function updateMatchHeader(data) {
    // 홈팀 정보 업데이트
    const homeTeamContainer = document.querySelector('.team-container.home');
    homeTeamContainer.querySelector('.team-logo').src = data.homeTeam.logoUrl;
    homeTeamContainer.querySelector('.team-logo').alt = data.homeTeam.name;
    homeTeamContainer.querySelector('.team-name').textContent = data.homeTeam.name;
    
    // 원정팀 정보 업데이트
    const awayTeamContainer = document.querySelector('.team-container.away');
    awayTeamContainer.querySelector('.team-logo').src = data.awayTeam.logoUrl;
    awayTeamContainer.querySelector('.team-logo').alt = data.awayTeam.name;
    awayTeamContainer.querySelector('.team-name').textContent = data.awayTeam.name;
    
    // 경기 시간 정보 업데이트
    document.querySelector('.match-time').textContent = data.time;
    document.querySelector('.match-date').textContent = data.date;
}

/**
 * 인사이트 정보 업데이트 함수 (실제 API 구현 시 사용)
 * @param {Object} insights - 인사이트 데이터
 */
function updateInsights(insights) {
    // 홈팀 인사이트 업데이트
    const homeInsightBody = document.querySelector('.team-insight:first-child .insight-body');
    homeInsightBody.innerHTML = ''; // 기존 내용 비우기
    
    if (insights.home && insights.home.length > 0) {
        insights.home.forEach(item => {
            const insightItem = document.createElement('div');
            insightItem.className = `insight-item ${item.type}`;
            insightItem.innerHTML = `
                <span class="bullet ${item.type}">●</span>
                <span class="insight-text">${item.text}</span>
            `;
            homeInsightBody.appendChild(insightItem);
        });
    } else {
        homeInsightBody.innerHTML = '<div class="insight-item">인사이트 정보가 없습니다.</div>';
    }
    
    // 원정팀 인사이트 업데이트
    const awayInsightBody = document.querySelector('.team-insight:last-child .insight-body');
    awayInsightBody.innerHTML = ''; // 기존 내용 비우기
    
    if (insights.away && insights.away.length > 0) {
        insights.away.forEach(item => {
            const insightItem = document.createElement('div');
            insightItem.className = `insight-item ${item.type}`;
            insightItem.innerHTML = `
                <span class="bullet ${item.type}">●</span>
                <span class="insight-text">${item.text}</span>
            `;
            awayInsightBody.appendChild(insightItem);
        });
    } else {
        awayInsightBody.innerHTML = '<div class="insight-item">인사이트 정보가 없습니다.</div>';
    }
}

/**
 * 뉴스 정보 업데이트 함수 (실제 API 구현 시 사용)
 * @param {Object} news - 뉴스 데이터
 */
function updateNews(news) {
    // 홈팀 뉴스 업데이트
    const homeNewsContent = document.querySelector('.news-item:first-child .news-content');
    homeNewsContent.innerHTML = ''; // 기존 내용 비우기
    
    if (news.home && news.home.length > 0) {
        news.home.forEach(item => {
            const newsItem = document.createElement('p');
            newsItem.textContent = `${item.text} - ${item.source}`;
            homeNewsContent.appendChild(newsItem);
        });
    } else {
        homeNewsContent.innerHTML = '<p>최근 뉴스가 없습니다.</p>';
    }
    
    // 원정팀 뉴스 업데이트
    const awayNewsContent = document.querySelector('.news-item:last-child .news-content');
    awayNewsContent.innerHTML = ''; // 기존 내용 비우기
    
    if (news.away && news.away.length > 0) {
        news.away.forEach(item => {
            const newsItem = document.createElement('p');
            newsItem.textContent = `${item.text} - ${item.source}`;
            awayNewsContent.appendChild(newsItem);
        });
    } else {
        awayNewsContent.innerHTML = '<p>최근 뉴스가 없습니다.</p>';
    }
}

/**
 * 팀 로고 오류 처리
 */
document.addEventListener('DOMContentLoaded', function() {
    const teamLogos = document.querySelectorAll('.team-logo, .insight-team-logo, .news-team-logo');
    
    teamLogos.forEach(logo => {
        logo.addEventListener('error', function() {
            // 로고 로드 실패 시 대체 이미지 설정
            this.src = 'https://via.placeholder.com/60/cccccc/666666?text=Team';
        });
    });
});

/**
 * 탭 콘텐츠 렌더링 함수 (실제 API 구현 시 사용)
 * @param {string} tabName - 탭 이름
 * @param {Object} data - 탭 콘텐츠 데이터
 */
function renderTabContent(tabName, data) {
    const contentContainer = document.querySelector('.content-container');
    
    // 기존 콘텐츠 백업 (Preview 탭 콘텐츠)
    if (!window.previewContent && tabName !== 'preview') {
        window.previewContent = contentContainer.innerHTML;
    }
    
    switch (tabName) {
        case 'preview':
            // Preview 탭이 기본 콘텐츠이므로 백업된 내용이 있으면 복원
            if (window.previewContent) {
                contentContainer.innerHTML = window.previewContent;
            }
            break;
            
        case 'premo':
            // PREMO 탭 콘텐츠 렌더링
            contentContainer.innerHTML = renderPremoContent(data);
            break;
            
        case 'h2h':
            // Head to Head 탭 콘텐츠 렌더링
            contentContainer.innerHTML = renderHeadToHeadContent(data);
            break;
            
        case 'table':
            // Table 탭 콘텐츠 렌더링
            contentContainer.innerHTML = renderTableContent(data);
            break;
            
        default:
            console.error(`알 수 없는 탭 이름: ${tabName}`);
    }
}

/**
 * PREMO 탭 콘텐츠 렌더링 함수 (예시)
 * @param {Object} data - PREMO 데이터
 * @returns {string} HTML 콘텐츠
 */
function renderPremoContent(data) {
    return `
        <div class="section-card">
            <h2 class="section-title">PREMO™ 분석</h2>
            <div class="premo-content">
                <p>PREMO 분석 콘텐츠가 여기에 표시됩니다.</p>
            </div>
        </div>
    `;
}

/**
 * Head to Head 탭 콘텐츠 렌더링 함수 (예시)
 * @param {Object} data - Head to Head 데이터
 * @returns {string} HTML 콘텐츠
 */
function renderHeadToHeadContent(data) {
    return `
        <div class="section-card">
            <h2 class="section-title">Head to Head</h2>
            <div class="h2h-content">
                <p>Head to Head 콘텐츠가 여기에 표시됩니다.</p>
            </div>
        </div>
    `;
}

/**
 * Table 탭 콘텐츠 렌더링 함수 (예시)
 * @param {Object} data - Table 데이터
 * @returns {string} HTML 콘텐츠
 */
function renderTableContent(data) {
    return `
        <div class="section-card">
            <h2 class="section-title">Table</h2>
            <div class="table-content">
                <p>Table 콘텐츠가 여기에 표시됩니다.</p>
            </div>
        </div>
    `;
}