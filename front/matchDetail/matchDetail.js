/**
 * 경기 세부 정보 페이지 스크립트
 * 탭 전환 및 예측 데이터 관리
 */

// DOM이 완전히 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 탭 전환 기능 초기화
    initTabs();
    
    // 경기 세부 정보 로드
    loadMatchDetail();
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
 * 탭 콘텐츠 로드 함수
 */
function loadTabContent(tabName) {
    console.log(`${tabName} 탭 콘텐츠를 로드합니다.`);
    
    // Preview 탭 클릭 시 matchInfo.html로 이동
    if (tabName === 'preview') {
        const matchId = getMatchId();
        console.log(`matchInfo 페이지로 이동합니다. matchId: ${matchId}`);
        window.location.href = `../matchInfo/matchInfo.html?matchId=${matchId}`;
        return;
    }
    
    // PREMO 탭은 현재 페이지이므로 아무 동작 안함
    if (tabName === 'premo') {
        console.log('PREMO 탭이 선택되었습니다. (현재 페이지)');
        return;
    }
    
    // 다른 탭들은 아직 구현 중
    if (tabName === 'h2h') {
        const matchId = getMatchId();
        console.log(`matchH2h 페이지 새로고침. matchId: ${matchId}`);
        window.location.href = `../matchH2h/matchH2h.html?matchId=${matchId}`;
        return;
    }
}

/**
 * 현재 URL에서 경기 ID 추출
 */
function getMatchId() {
    const urlParams = new URLSearchParams(window.location.search);
    console.log(urlParams.get('matchId'))
    return urlParams.get('matchId');
}

/**
 * 경기 세부 정보 로드 함수
 */
async function loadMatchDetail() {
    const matchId = getMatchId();
    console.log(`경기 ID ${matchId}의 세부 정보를 로드합니다.`);
    
    try {
        // API 호출
        const response = await fetch(`http://localhost:3000/match/matchDetail?matchId=${matchId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API 응답 데이터:', data);
        
        // 🔥 디버깅: 받아온 이미지 데이터 확인
        console.log('=== 이미지 데이터 확인 ===');
        console.log('홈팀 이미지:', data.content.homeTeamImage);
        console.log('어웨이팀 이미지:', data.content.awayTeamImage);
        
        // 받아온 데이터로 화면 업데이트
        if (data.content) {
            const matchData = data.content;
            
            // 각 섹션별로 데이터 업데이트
            updateMatchHeader(matchData);
            updateWinRatePrediction(matchData);
            updateScorePrediction(matchData.predicted);
            updateKeyPlayerSection(matchData.homeKeyPlayer, matchData.awayKeyPlayer);

        } else {
            console.error('경기 데이터가 없습니다.');
            showErrorMessage('경기 데이터가 없습니다.');
        }
        
    } catch (error) {
        console.error('경기 세부 정보를 로드하는 중 오류가 발생했습니다:', error);
        showErrorMessage('경기 정보를 불러오는데 실패했습니다.');
    }
}

/**
 * 경기 헤더 정보 업데이트 함수
 */
function updateMatchHeader(data) {
    console.log('경기 헤더 업데이트:', data);
    
    // 🔥 이미지 경로 처리
    const homeTeamImagePath = processImagePath(data.homeTeamImage);
    const awayTeamImagePath = processImagePath(data.awayTeamImage);
    
    // 🔥 디버깅: 처리된 이미지 경로 확인
    console.log('처리된 홈팀 이미지:', homeTeamImagePath);
    console.log('처리된 어웨이팀 이미지:', awayTeamImagePath);
    
    // 홈팀 정보 업데이트
    const homeTeamContainer = document.querySelector('.team-container.home');
    const homeTeamNameEl = homeTeamContainer.querySelector('.team-name');
    homeTeamNameEl.textContent = data.homeTeamName;
    
    // 🔥 수정된 부분: 실제 이미지 사용
    addTeamLogo(homeTeamContainer, data.homeTeamName, homeTeamImagePath, true);
    
    // 원정팀 정보 업데이트
    const awayTeamContainer = document.querySelector('.team-container.away');
    const awayTeamNameEl = awayTeamContainer.querySelector('.team-name');
    awayTeamNameEl.textContent = data.awayTeamName;
    
    // 🔥 수정된 부분: 실제 이미지 사용
    addTeamLogo(awayTeamContainer, data.awayTeamName, awayTeamImagePath, false);
    
    // 경기 시간 정보 업데이트
    const matchTimeEl = document.querySelector('.match-time');
    matchTimeEl.textContent = data.matchTime;
    
    // 승률 예측 바에도 팀 로고 추가
    updateWinRateLogos(data, homeTeamImagePath, awayTeamImagePath);
    
    // 점수 예측 카드의 팀 로고도 업데이트
    updateScoreCardLogos(data, homeTeamImagePath, awayTeamImagePath);
}

/**
 * 팀 로고 추가 함수 (실제 이미지 적용)
 * @param {HTMLElement} container - 팀 컨테이너
 * @param {string} teamName - 팀명
 * @param {string} imagePath - 처리된 이미지 경로
 * @param {boolean} isHome - 홈팀 여부
 */
function addTeamLogo(container, teamName, imagePath, isHome) {
    let teamLogo = container.querySelector('.team-logo');
    if (!teamLogo) {
        teamLogo = document.createElement('img');
        teamLogo.className = 'team-logo';
        const teamNameEl = container.querySelector('.team-name');
        container.insertBefore(teamLogo, teamNameEl);
    }
    
    // 🔥 실제 이미지가 있으면 사용, 없으면 플레이스홀더
    if (imagePath) {
        teamLogo.onerror = (e) => {
            // 에러 이벤트 전파 중단
            e.preventDefault();
            e.stopPropagation();
            // 실패 시 플레이스홀더 사용
            const initials = teamName.split(' ').map(word => word[0]).join('').substring(0, 3);
            const colors = ['ff0000', '0000ff', '00ff00', '800080', 'ff8c00', '008080'];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            teamLogo.src = `https://via.placeholder.com/80/${randomColor}/ffffff?text=${initials}`;
            // onerror 이벤트 제거하여 무한 루프 방지
            teamLogo.onerror = null;
        };
        teamLogo.src = imagePath;
    } else {
        // 이미지가 없으면 플레이스홀더 사용
        const initials = teamName.split(' ').map(word => word[0]).join('').substring(0, 3);
        const colors = ['ff0000', '0000ff', '00ff00', '800080', 'ff8c00', '008080'];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        teamLogo.src = `https://via.placeholder.com/80/${randomColor}/ffffff?text=${initials}`;
    }
    
    teamLogo.alt = teamName;
}

/**
 * 승률 예측 정보 업데이트 함수
 */
function updateWinRatePrediction(data) {
    if (!data.winProbability) return;
    
    const homeWinRate = Math.round(data.winProbability);
    const drawRate = Math.round(data.drawProbability);
    const awayWinRate = 100 - homeWinRate - drawRate;
    
    console.log('승률 정보 업데이트:', {
        home: homeWinRate,
        draw: drawRate,
        away: awayWinRate
    });
    
    // 승률 바 업데이트
    const homeRateEl = document.querySelector('.home-rate');
    const drawRateEl = document.querySelector('.draw-rate');
    const awayRateEl = document.querySelector('.away-rate');
    
    if (homeRateEl) homeRateEl.style.width = `${homeWinRate}%`;
    if (drawRateEl) drawRateEl.style.width = `${drawRate}%`;
    if (awayRateEl) awayRateEl.style.width = `${awayWinRate}%`;
    
    // 승률 라벨 업데이트
    const homeRateLabelEl = document.querySelector('.rate-label.home span');
    const drawRateLabelEl = document.querySelector('.rate-label.draw span');
    const awayRateLabelEl = document.querySelector('.rate-label.away span');
    
    if (homeRateLabelEl) homeRateLabelEl.textContent = `${homeWinRate}%`;
    if (drawRateLabelEl) drawRateLabelEl.textContent = `Draw ${drawRate}%`;
    if (awayRateLabelEl) awayRateLabelEl.textContent = `${awayWinRate}%`;
}

/**
 * 승률 예측 바의 팀 로고 업데이트
 * @param {Object} data - 경기 데이터
 * @param {string} homeTeamImagePath - 처리된 홈팀 이미지 경로
 * @param {string} awayTeamImagePath - 처리된 어웨이팀 이미지 경로
 */
function updateWinRateLogos(data, homeTeamImagePath, awayTeamImagePath) {
    // 홈팀 로고 (승률 바 왼쪽)
    const homeRateLabel = document.querySelector('.rate-label.home');
    let homeRateLogo = homeRateLabel.querySelector('.team-mini-logo');
    
    if (!homeRateLogo) {
        homeRateLogo = document.createElement('img');
        homeRateLogo.className = 'team-mini-logo';
        const span = homeRateLabel.querySelector('span');
        homeRateLabel.insertBefore(homeRateLogo, span);
    }
    
    // 🔥 실제 이미지 사용
    if (homeTeamImagePath) {
        homeRateLogo.onerror = (e) => {
            e.preventDefault();
            e.stopPropagation();
            const homeInitials = data.homeTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
            homeRateLogo.src = `https://via.placeholder.com/25/ff0000/ffffff?text=${homeInitials}`;
            homeRateLogo.onerror = null;
        };
        homeRateLogo.src = homeTeamImagePath;
    } else {
        const homeInitials = data.homeTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
        homeRateLogo.src = `https://via.placeholder.com/25/ff0000/ffffff?text=${homeInitials}`;
    }
    homeRateLogo.alt = data.homeTeamName;
    
    // 원정팀 로고 (승률 바 오른쪽)
    const awayRateLabel = document.querySelector('.rate-label.away');
    let awayRateLogo = awayRateLabel.querySelector('.team-mini-logo');
    
    if (!awayRateLogo) {
        awayRateLogo = document.createElement('img');
        awayRateLogo.className = 'team-mini-logo';
        const span = awayRateLabel.querySelector('span');
        awayRateLabel.appendChild(awayRateLogo);
    }
    
    // 🔥 실제 이미지 사용
    if (awayTeamImagePath) {
        awayRateLogo.onerror = (e) => {
            e.preventDefault();
            e.stopPropagation();
            const awayInitials = data.awayTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
            awayRateLogo.src = `https://via.placeholder.com/25/0000ff/ffffff?text=${awayInitials}`;
            awayRateLogo.onerror = null;
        };
        awayRateLogo.src = awayTeamImagePath;
    } else {
        const awayInitials = data.awayTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
        awayRateLogo.src = `https://via.placeholder.com/25/0000ff/ffffff?text=${awayInitials}`;
    }
    awayRateLogo.alt = data.awayTeamName;
}

/**
 * 점수 예측 카드의 팀 로고 업데이트 함수
 * @param {Object} data - 경기 데이터
 * @param {string} homeTeamImagePath - 처리된 홈팀 이미지 경로
 * @param {string} awayTeamImagePath - 처리된 어웨이팀 이미지 경로
 */
function updateScoreCardLogos(data, homeTeamImagePath, awayTeamImagePath) {
    const scoreContainers = document.querySelectorAll('.team-score-container');
    
    // 홈팀 로고 (왼쪽)
    if (scoreContainers[0]) {
        let homeLogo = scoreContainers[0].querySelector('.score-team-logo');
        if (!homeLogo) {
            homeLogo = document.createElement('img');
            homeLogo.className = 'score-team-logo';
            scoreContainers[0].appendChild(homeLogo);
        }
        
        // 🔥 실제 이미지 사용
        if (homeTeamImagePath) {
            homeLogo.onerror = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const homeInitials = data.homeTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
                homeLogo.src = `https://via.placeholder.com/60/ff0000/ffffff?text=${homeInitials}`;
                homeLogo.onerror = null;
            };
            homeLogo.src = homeTeamImagePath;
        } else {
            const homeInitials = data.homeTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
            homeLogo.src = `https://via.placeholder.com/60/ff0000/ffffff?text=${homeInitials}`;
        }
        homeLogo.alt = data.homeTeamName;
    }
    
    // 원정팀 로고 (오른쪽)
    if (scoreContainers[1]) {
        let awayLogo = scoreContainers[1].querySelector('.score-team-logo');
        if (!awayLogo) {
            awayLogo = document.createElement('img');
            awayLogo.className = 'score-team-logo';
            scoreContainers[1].appendChild(awayLogo);
        }
        
        // 🔥 실제 이미지 사용
        if (awayTeamImagePath) {
            awayLogo.onerror = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const awayInitials = data.awayTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
                awayLogo.src = `https://via.placeholder.com/60/0000ff/ffffff?text=${awayInitials}`;
                awayLogo.onerror = null;
            };
            awayLogo.src = awayTeamImagePath;
        } else {
            const awayInitials = data.awayTeamName.split(' ').map(word => word[0]).join('').substring(0, 2);
            awayLogo.src = `https://via.placeholder.com/60/0000ff/ffffff?text=${awayInitials}`;
        }
        awayLogo.alt = data.awayTeamName;
    }
}

/**
 * 점수 예측 정보 업데이트 함수
 */
function updateScorePrediction(predicted) {
    console.log('=== updateScorePrediction 시작 ===');
    console.log('predicted 데이터:', predicted);
    
    if (!predicted || !Array.isArray(predicted)) {
        console.error('predicted 데이터가 유효하지 않습니다:', predicted);
        return;
    }
    
    const scoreResultsContainer = document.querySelector('.score-results');
    if (!scoreResultsContainer) {
        console.error('.score-results 요소를 찾을 수 없습니다!');
        return;
    }
    
    // 기존 내용 비우기
    scoreResultsContainer.innerHTML = '';
    
    // 예측 결과 표시 (최대 3개)
    predicted.slice(0, 3).forEach((scoreData, index) => {
        console.log(`${index + 1}번째 아이템 처리:`, scoreData);
        
        const scoreItem = document.createElement('div');
        scoreItem.className = 'score-result-item';
        scoreItem.innerHTML = `
            <div class="score">${scoreData.homeScore}:${scoreData.awayScore}</div>
            <div class="probability">${scoreData.probability}%</div>
        `;
        scoreResultsContainer.appendChild(scoreItem);
    });
    
    console.log('=== updateScorePrediction 완료 ===');
}

/**
 * 핵심 선수 섹션 업데이트 함수
 */
 function updateKeyPlayerSection(homeKeyPlayer, awayKeyPlayer) {
    console.log('핵심 선수 정보 업데이트:', { homeKeyPlayer, awayKeyPlayer });
    
    // 기존 선수 컨테이너 비우기
    const playersContainer = document.querySelector('.players-container');
    if (!playersContainer) {
        console.error('.players-container 요소를 찾을 수 없습니다!');
        return;
    }
    
    playersContainer.innerHTML = '';
    
    // 홈팀 키 플레이어 추가
    if (homeKeyPlayer) {
        const homePlayerElement = createPlayerElement(homeKeyPlayer, 'home');
        playersContainer.appendChild(homePlayerElement);
    }
    
    // 어웨이팀 키 플레이어 추가
    if (awayKeyPlayer) {
        const awayPlayerElement = createPlayerElement(awayKeyPlayer, 'away');
        playersContainer.appendChild(awayPlayerElement);
    }
}

/**
 * 선수 요소 생성 함수
 */
 function createPlayerElement(player, teamType) {
    const playerItem = document.createElement('div');
    playerItem.className = 'player-item';
    playerItem.style.cursor = 'pointer';
    
    // 선수 이미지 생성 (고정된 프로필 이미지 경로 사용)
    const playerImg = document.createElement('img');
    playerImg.className = 'player-img';
    
    const imageSrc = `file:///Users/parkryun/Downloads/pics/profile_pictures/${player.playerId}.png`;
    
    playerImg.src = imageSrc;
    playerImg.alt = player.name;
    
    // 이미지 로드 실패 시 플레이스홀더로 대체
    playerImg.onerror = function(e) {
        e.preventDefault();
        e.stopPropagation();
        const initials = player.name.split(' ').map(word => word[0]).join('').substring(0, 2);
        const bgColor = teamType === 'home' ? 'ff0000' : '0000ff';
        this.src = `https://via.placeholder.com/60/${bgColor}/ffffff?text=${initials}`;
        this.onerror = null; // 무한 루프 방지
    };
    
    // 선수 이름
    const playerName = document.createElement('div');
    playerName.className = 'player-name';
    playerName.textContent = player.name;
    
    // 예상 득점 확률 (임시값)
    const playerProbability = document.createElement('div');
    playerProbability.className = 'player-probability';
    playerProbability.textContent = '25%';
    
    // 요소들 추가
    playerItem.appendChild(playerImg);
    playerItem.appendChild(playerName);
    playerItem.appendChild(playerProbability);
    
    // 클릭 이벤트 추가 - playerId만 전달
    playerItem.addEventListener('click', function() {
        console.log(`선수 클릭: ${player.name}, playerId: ${player.playerId}`);
        window.location.href = `../matchPlayer/matchPlayer.html?playerId=${player.playerId}`;
    });
    
    // 호버 효과
    playerItem.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.05)';
        this.style.transition = 'transform 0.2s ease';
    });
    
    playerItem.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
    
    return playerItem;
}

/**
 * 오류 메시지 표시 함수
 */
function showErrorMessage(message) {
    const container = document.querySelector('.content-container');
    container.innerHTML = `
        <div class="error-message" style="text-align: center; padding: 40px; color: #666;">
            <h3>오류 발생</h3>
            <p>${message}</p>
            <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">
                다시 시도
            </button>
        </div>
    `;
}