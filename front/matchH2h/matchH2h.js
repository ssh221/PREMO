/**
 * Head to Head 페이지 스크립트
 * 두 팀간의 역대 전적을 표시합니다.
 */

// DOM이 완전히 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 탭 전환 기능 초기화
    initTabs();
    
    // H2H 데이터 로드
    loadH2HData();
});

/**
 * 이미지 경로 처리 함수
 * @param {string} imagePath - 백엔드에서 받은 이미지 경로
 * @returns {string} 로컬 절대경로
 */
function processImagePath(imagePath) {
    if (!imagePath) return null;
    
    // 🔥 백엔드에서 받은 경로를 로컬 절대경로로 변환
    const fileName = imagePath.split('/').pop();
    return `file:///Users/parkryun/Downloads/pics/team_logos/${fileName}`;
}

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
 * 현재 URL에서 경기 ID 추출
 * @returns {string} 경기 ID
 */
function getMatchId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('matchId'); 
}

/**
 * 탭 콘텐츠 로드 함수
 * @param {string} tabName - 탭 이름 ('preview', 'premo', 'h2h', 'table')
 */
function loadTabContent(tabName) {
    const matchId = getMatchId();
    
    if (!matchId) {
        console.error('matchId가 없어서 페이지 이동할 수 없습니다.');
        return;
    }
    
    console.log(`${tabName} 탭 콘텐츠를 로드합니다.`);

    switch(tabName) {
        case 'preview':
            console.log(`Preview 페이지로 이동합니다. matchId: ${matchId}`);
            window.location.href = `../matchInfo/matchInfo.html?matchId=${matchId}`;
            break;
            
        case 'premo':
            console.log(`PREMO 페이지로 이동합니다. matchId: ${matchId}`);
            window.location.href = `../matchDetail/matchDetail.html?matchId=${matchId}`;
            break;
            
        case 'h2h':
            console.log(`현재 Head to Head 페이지입니다.`);
            // 현재 페이지이므로 아무것도 하지 않음
            break;
            
        case 'table':
            console.log(`Table 페이지 기능은 아직 구현되지 않았습니다.`);
            break;
            
        default:
            console.log(`알 수 없는 탭: ${tabName}`);
            break;
    }
}

/**
 * H2H 데이터 로드 함수
 */
async function loadH2HData() {
    const matchId = getMatchId();
    
    if (!matchId) {
        console.error('matchId가 없습니다.');
        showEmptyMessage('경기 ID를 찾을 수 없습니다.');
        return;
    }
    
    console.log(`경기 ID ${matchId}의 H2H 정보를 로드합니다.`);
    
    try {
        // H2H API 호출 (팀 정보와 H2H 데이터를 한번에 받음)
        const h2hResponse = await fetch(`http://localhost:3000/match/matchHeadToHead?matchId=${matchId}`);
        
        if (!h2hResponse.ok) {
            throw new Error(`H2H API 오류! status: ${h2hResponse.status}`);
        }
        
        const h2hData = await h2hResponse.json();
        
        // 🔥 디버깅: 받아온 이미지 데이터 확인
        console.log('=== H2H 이미지 데이터 확인 ===');
        console.log('홈팀 이미지:', h2hData.content.homeTeamImage);
        console.log('어웨이팀 이미지:', h2hData.content.awayTeamImage);
        
        if (h2hData.success) {
            // 헤더 정보 업데이트
            updateMatchHeader(h2hData.content);
            
            // H2H 콘텐츠 업데이트
            updateH2HContent(h2hData.content);
        } else {
            console.error('H2H API 응답 오류:', h2hData.message);
            showEmptyMessage('H2H 데이터를 불러올 수 없습니다.');
        }
        
    } catch (error) {
        console.error('H2H 정보를 로드하는 중 오류가 발생했습니다:', error);
        showEmptyMessage('데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

/**
 * 경기 헤더 정보 업데이트 함수
 * @param {Object} data - 경기 데이터
 */
function updateMatchHeader(data) {
    // 🔥 이미지 경로 처리
    const homeTeamImagePath = processImagePath(data.homeTeamImage);
    const awayTeamImagePath = processImagePath(data.awayTeamImage);
    
    // 🔥 디버깅: 처리된 이미지 경로 확인
    console.log('처리된 홈팀 이미지:', homeTeamImagePath);
    console.log('처리된 어웨이팀 이미지:', awayTeamImagePath);
    
    // 홈팀 정보 업데이트
    const homeTeamContainer = document.querySelector('.team-container.home');
    const homeTeamLogo = homeTeamContainer.querySelector('.team-logo');
    const homeTeamName = homeTeamContainer.querySelector('.team-name');
    
    homeTeamName.textContent = data.homeTeamName;
    
    // 🔥 수정된 부분: 실제 이미지 사용
    if (homeTeamImagePath) {
        homeTeamLogo.onerror = (e) => {
            e.preventDefault();
            e.stopPropagation();
            const initials = data.homeTeamName.split(' ').map(word => word[0]).join('');
            homeTeamLogo.src = `https://via.placeholder.com/80/ff0000/ffffff?text=${initials}`;
            homeTeamLogo.onerror = null;
        };
        homeTeamLogo.src = homeTeamImagePath;
    } else {
        const initials = data.homeTeamName.split(' ').map(word => word[0]).join('');
        homeTeamLogo.src = `https://via.placeholder.com/80/ff0000/ffffff?text=${initials}`;
    }
    homeTeamLogo.alt = data.homeTeamName;
    
    // 원정팀 정보 업데이트
    const awayTeamContainer = document.querySelector('.team-container.away');
    const awayTeamLogo = awayTeamContainer.querySelector('.team-logo');
    const awayTeamName = awayTeamContainer.querySelector('.team-name');
    
    awayTeamName.textContent = data.awayTeamName;
    
    // 🔥 수정된 부분: 실제 이미지 사용
    if (awayTeamImagePath) {
        awayTeamLogo.onerror = (e) => {
            e.preventDefault();
            e.stopPropagation();
            const initials = data.awayTeamName.split(' ').map(word => word[0]).join('');
            awayTeamLogo.src = `https://via.placeholder.com/80/0000ff/ffffff?text=${initials}`;
            awayTeamLogo.onerror = null;
        };
        awayTeamLogo.src = awayTeamImagePath;
    } else {
        const initials = data.awayTeamName.split(' ').map(word => word[0]).join('');
        awayTeamLogo.src = `https://via.placeholder.com/80/0000ff/ffffff?text=${initials}`;
    }
    awayTeamLogo.alt = data.awayTeamName;
    
    // 경기 시간 정보 업데이트
    document.querySelector('.match-time').textContent = data.matchTime;
}

/**
 * H2H 콘텐츠 업데이트 함수
 * @param {Object} h2hData - H2H 데이터
 */
function updateH2HContent(h2hData) {
    // 통계 업데이트
    updateH2HStats(h2hData);
    
    // 경기 히스토리 업데이트
    updateMatchHistory(h2hData.matchInfo, h2hData);
}

/**
 * H2H 통계 업데이트 함수
 * @param {Object} h2hData - H2H 데이터
 */
function updateH2HStats(h2hData) {
    const statsItems = document.querySelectorAll('.stats-item .stats-number');
    
    // 홈팀 승수
    statsItems[0].textContent = h2hData.homeWin || 0;
    
    // 무승부 수
    statsItems[1].textContent = h2hData.draw || 0;
    
    // 원정팀 승수
    statsItems[2].textContent = h2hData.awayWin || 0;
}

/**
 * 경기 히스토리 업데이트 함수
 * @param {Array} matchHistory - 경기 히스토리 배열
 * @param {Object} h2hData - H2H 데이터 (팀 정보 포함)
 */
function updateMatchHistory(matchHistory, h2hData) {
    const historyContainer = document.querySelector('.match-history');
    
    // 로딩 메시지 제거
    const loadingMessage = historyContainer.querySelector('.loading-message');
    if (loadingMessage) {
        loadingMessage.remove();
    }
    
    if (!matchHistory || matchHistory.length === 0) {
        showEmptyMessage('이전 경기 기록이 없습니다.');
        return;
    }
    
    // 경기 히스토리 렌더링
    matchHistory.forEach(match => {
        const historyItem = createHistoryItem(match, h2hData);
        historyContainer.appendChild(historyItem);
    });
}

/**
 * 히스토리 아이템 생성 함수
 * @param {Object} match - 경기 데이터
 * @param {Object} h2hData - H2H 데이터 (팀 정보 포함)
 * @returns {HTMLElement} 히스토리 아이템 엘리먼트
 */
function createHistoryItem(match, h2hData) {
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    
    // 클릭 이벤트 추가 (match_id가 있는 경우에만)
    if (match.match_id) {
        historyItem.style.cursor = 'pointer';
        historyItem.addEventListener('click', function() {
            navigateToMatchDetail(match.match_id);
        });
        
        // 호버 효과 추가
        historyItem.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        historyItem.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    }
    
    // 날짜 포맷팅
    const matchDate = new Date(match.matchDate);
    const dateString = matchDate.toLocaleDateString('en-US', { 
        weekday: 'short', 
        day: 'numeric', 
        month: 'short', 
        year: 'numeric' 
    });
    
    // 🔥 각 경기마다 홈팀을 왼쪽, 어웨이팀을 오른쪽으로 배치
    // 백엔드에서 각 경기의 실제 홈팀/어웨이팀 정보를 보내줌
    const leftTeamName = match.homeTeamName;    // 그 경기의 실제 홈팀명
    const rightTeamName = match.awayTeamName;   // 그 경기의 실제 어웨이팀명
    const leftScore = match.homeScore;          // 홈팀 득점
    const rightScore = match.awayScore;         // 어웨이팀 득점
    const leftTeamImagePath = processImagePath(match.homeTeamImage);   // 홈팀 이미지
    const rightTeamImagePath = processImagePath(match.awayTeamImage);  // 어웨이팀 이미지
    
    // 🔥 실제 이미지 또는 null 설정
    let leftImageSrc, rightImageSrc;
    
    if (leftTeamImagePath) {
        leftImageSrc = leftTeamImagePath;
    } else {
        leftImageSrc = null;
    }
    
    if (rightTeamImagePath) {
        rightImageSrc = rightTeamImagePath;
    } else {
        rightImageSrc = null;
    }
    
    // 클릭 가능한 경우 시각적 표시 추가
    const clickableClass = match.match_id ? 'clickable' : '';
    
    historyItem.innerHTML = `
        <div class="match-date-info">
            <div class="match-date-text">${dateString}</div>
            <div class="match-competition">${match.league}</div>
        </div>
        <div class="match-teams ${clickableClass}">
            <div class="team-info home">
                <span class="history-team-name">${leftTeamName}</span>
                ${leftImageSrc ? `<img src="${leftImageSrc}" alt="${leftTeamName}" class="history-team-logo">` : ''}
            </div>
            <div class="match-score">
                <div class="score-text">${leftScore} - ${rightScore}</div>
            </div>
            <div class="team-info away">
                ${rightImageSrc ? `<img src="${rightImageSrc}" alt="${rightTeamName}" class="history-team-logo">` : ''}
                <span class="history-team-name">${rightTeamName}</span>
            </div>
        </div>
        <div class="match-venue">
            <div class="venue-text">${match.matchVenue || ''}</div>
        </div>
        ${match.match_id ? '<div class="click-indicator">→</div>' : ''}
    `;
    
    return historyItem;
}

/**
 * 빈 상태 메시지 표시 함수
 * @param {string} message - 표시할 메시지
 */
function showEmptyMessage(message) {
    const historyContainer = document.querySelector('.match-history');
    
    // 기존 콘텐츠 제거
    historyContainer.innerHTML = '';
    
    // 빈 상태 메시지 생성
    const emptyMessage = document.createElement('div');
    emptyMessage.className = 'empty-message';
    emptyMessage.textContent = message;
    
    historyContainer.appendChild(emptyMessage);
}

/**
 * 경기 상세 페이지로 이동
 * @param {number} matchId - 이동할 경기 ID
 */
function navigateToMatchDetail(matchId) {
    console.log(`경기 상세 페이지로 이동합니다. matchId: ${matchId}`);
    
    // matchInfo 페이지로 이동
    window.location.href = `../matchInfo/matchInfo.html?matchId=${matchId}`;
}