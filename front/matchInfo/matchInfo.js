/**
 * 경기 정보 페이지 스크립트
 * 탭 전환 및 투표 기능 등을 관리합니다.
 */

// DOM이 완전히 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 탭 전환 기능 초기화
    initTabs();
    
    // 투표 기능 초기화
    initVoting();
    
    // 경기 정보 로드
    loadMatchInfo();
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
 * 투표 기능 초기화
 */
function initVoting() {
    const voteButtons = document.querySelectorAll('.vote-btn');
    
    voteButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 이전에 선택된 버튼 스타일 초기화
            document.querySelectorAll('.vote-btn').forEach(btn => {
                btn.style.backgroundColor = '';
                btn.style.borderColor = '#ddd';
            });
            
            // 선택된 버튼 스타일 변경
            this.style.backgroundColor = '#f0f0f0';
            this.style.borderColor = '#999';
            
            // 투표한 팀 정보
            const votedTeam = this.getAttribute('data-team');
            
            // 투표 처리 함수 호출
            processVote(votedTeam);
        });
    });
}

/**
 * 이미지 경로 처리 함수
 * @param {string} imagePath - 백엔드에서 받은 이미지 경로
 * @returns {string} 로컬 절대경로
 */
function processImagePath(imagePath) {
    if (!imagePath) return null;
    
    // 🔥 백엔드에서 받은 경로를 로컬 절대경로로 변환
    // "/pics/team_logos/23.png" → "file:///Users/parkryun/Downloads/pics/team_logos/23.png"
    const fileName = imagePath.split('/').pop();
    return `file:///Users/parkryun/Downloads/pics/team_logos/${fileName}`;
}

/**
 * 투표 처리 함수
 * @param {string} team - 투표한 팀 ('home', 'draw', 'away')
 */
function processVote(team) {
    console.log(`${team}에 투표했습니다.`);
    
    // 투표 수 시뮬레이션 (실제로는 서버에서 받은 데이터로 업데이트)
    let currentVotes = parseInt(document.querySelector('.voting-stats').textContent.replace(/[^0-9]/g, ''));
    currentVotes++;
    updateVotingStats(currentVotes);
}

/**
 * 투표 통계 업데이트 함수
 * @param {number} totalVotes - 총 투표 수
 */
function updateVotingStats(totalVotes) {
    document.querySelector('.voting-stats').textContent = `Total votes: ${totalVotes.toLocaleString()}`;
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
    console.log(`${tabName} 탭 콘텐츠를 로드합니다.`);

    if (tabName === 'premo') {
        const matchId = getMatchId();
        console.log(`matchDetail 페이지로 이동합니다. matchId: ${matchId}`);
        window.location.href = `../matchDetail/matchDetail.html?matchId=${matchId}`;
        return;
    }
    else if (tabName === 'h2h') {
        const matchId = getMatchId();
        console.log(`matchH2h 페이지 새로고침. matchId: ${matchId}`);
        window.location.href = `../matchH2h/matchH2h.html?matchId=${matchId}`;
        return;
    }
    else if (tabName === 'preview') {
        const matchId = getMatchId();
        console.log(`matchInfo 페이지 새로고침. matchId: ${matchId}`);
        window.location.href = `../matchInfo/matchInfo.html?matchId=${matchId}`;
        return;
    }
}

/**
 * 경기 정보 로드 함수
 */
async function loadMatchInfo() {
    const matchId = getMatchId();
    
    if (!matchId) {
        console.error('matchId가 없습니다.');
        return;
    }
    
    console.log(`경기 ID ${matchId}의 정보를 로드합니다.`);
    
    try {
        const response = await fetch(`http://localhost:3000/match/matchInfo?matchId=${matchId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 🔥 디버깅: 받아온 이미지 데이터 확인
        console.log('=== 이미지 데이터 확인 ===');
        console.log('홈팀 이미지:', data.content.homeTeamImage);
        console.log('어웨이팀 이미지:', data.content.awayTeamImage);
        
        if (data.success) {
            updateMatchHeader(data.content);
            updateMatchDetails(data.content);
            updateTeamForm(data.content);
            updateBettingOdds(data.content);
        } else {
            console.error('API 응답 오류:', data.message);
        }
        
    } catch (error) {
        console.error('경기 정보를 로드하는 중 오류가 발생했습니다:', error);
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
    
    // 🔥 수정된 부분: 로컬 절대경로 사용
    if (homeTeamImagePath) {
        homeTeamLogo.src = homeTeamImagePath;
        homeTeamLogo.onload = () => console.log('✅ 홈팀 이미지 로드 성공:', homeTeamImagePath);
        homeTeamLogo.onerror = () => console.log('❌ 홈팀 이미지 로드 실패:', homeTeamImagePath);
    } else {
        // 팀명 첫 글자들로 플레이스홀더 생성
        const initials = data.homeTeamName.split(' ').map(word => word[0]).join('');
        homeTeamLogo.src = `https://via.placeholder.com/80/ff0000/ffffff?text=${initials}`;
    }
    homeTeamLogo.alt = data.homeTeamName;
    
    // 원정팀 정보 업데이트
    const awayTeamContainer = document.querySelector('.team-container.away');
    const awayTeamLogo = awayTeamContainer.querySelector('.team-logo');
    const awayTeamName = awayTeamContainer.querySelector('.team-name');
    
    awayTeamName.textContent = data.awayTeamName;
    
    // 🔥 수정된 부분: 로컬 절대경로 사용
    if (awayTeamImagePath) {
        awayTeamLogo.src = awayTeamImagePath;
        awayTeamLogo.onload = () => console.log('✅ 어웨이팀 이미지 로드 성공:', awayTeamImagePath);
        awayTeamLogo.onerror = () => console.log('❌ 어웨이팀 이미지 로드 실패:', awayTeamImagePath);
    } else {
        const initials = data.awayTeamName.split(' ').map(word => word[0]).join('');
        awayTeamLogo.src = `https://via.placeholder.com/80/0000ff/ffffff?text=${initials}`;
    }
    awayTeamLogo.alt = data.awayTeamName;
    
    // 경기 시간 정보 업데이트
    document.querySelector('.match-time').textContent = data.matchTime;
    
    // 투표 버튼의 로고도 업데이트
    updateVotingLogos(data, homeTeamImagePath, awayTeamImagePath);
}

/**
 * 투표 섹션 로고 업데이트
 * @param {Object} data - 경기 데이터
 * @param {string} homeTeamImagePath - 처리된 홈팀 이미지 경로
 * @param {string} awayTeamImagePath - 처리된 어웨이팀 이미지 경로
 */
function updateVotingLogos(data, homeTeamImagePath, awayTeamImagePath) {
    const voteBtns = document.querySelectorAll('.vote-btn');
    
    // 홈팀 투표 버튼
    const homeVoteBtn = voteBtns[0];
    const homeVoteLogo = homeVoteBtn.querySelector('.vote-logo');
    if (homeVoteLogo) {
        if (homeTeamImagePath) {
            homeVoteLogo.src = homeTeamImagePath;
            homeVoteLogo.onload = () => console.log('✅ 홈팀 투표 버튼 이미지 로드 성공');
            homeVoteLogo.onerror = () => console.log('❌ 홈팀 투표 버튼 이미지 로드 실패');
        } else {
            const initials = data.homeTeamName.split(' ').map(word => word[0]).join('');
            homeVoteLogo.src = `https://via.placeholder.com/24/ff0000/ffffff?text=${initials}`;
        }
        homeVoteLogo.alt = data.homeTeamName;
    }
    
    // 원정팀 투표 버튼
    const awayVoteBtn = voteBtns[2];
    const awayVoteLogo = awayVoteBtn.querySelector('.vote-logo');
    if (awayVoteLogo) {
        if (awayTeamImagePath) {
            awayVoteLogo.src = awayTeamImagePath;
            awayVoteLogo.onload = () => console.log('✅ 어웨이팀 투표 버튼 이미지 로드 성공');
            awayVoteLogo.onerror = () => console.log('❌ 어웨이팀 투표 버튼 이미지 로드 실패');
        } else {
            const initials = data.awayTeamName.split(' ').map(word => word[0]).join('');
            awayVoteLogo.src = `https://via.placeholder.com/24/0000ff/ffffff?text=${initials}`;
        }
        awayVoteLogo.alt = data.awayTeamName;
    }
}

/**
 * 경기 상세 정보 업데이트 함수
 * @param {Object} data - 경기 데이터
 */
function updateMatchDetails(data) {
    const detailItems = document.querySelectorAll('.detail-item');
    
    // 현재 날짜 정보 (실제로는 API에서 날짜 정보를 받아와야 함)
    const today = new Date();
    const dateStr = today.toLocaleDateString('en-US', { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
    
    // 날짜 정보
    detailItems[0].querySelector('.detail-text').textContent = `${dateStr}, ${data.matchTime}`;
    
    // 대회 정보
    detailItems[1].querySelector('.detail-text').textContent = data.league;
    
    // 경기장 정보
    detailItems[2].querySelector('.detail-text').textContent = data.matchVenue;
}

/**
 * 배팅 정보 업데이트 함수
 * @param {Object} data - 경기 데이터
 */
function updateBettingOdds(data) {
    const oddsItems = document.querySelectorAll('.odds-value');
    
    // winProbability를 기반으로 배당률 계산 (간단한 예시)
    const homeWinProb = data.winProbability;
    const awayWinProb = 1 - homeWinProb - 0.25; // 무승부 확률을 25%로 가정
    const drawProb = 0.25;
    
    // 배당률 = 1 / 확률 (약간의 마진 추가)
    const homeOdds = (1 / homeWinProb * 0.9).toFixed(2);
    const drawOdds = (1 / drawProb * 0.9).toFixed(2);
    const awayOdds = (1 / awayWinProb * 0.9).toFixed(2);
    
    // 홈팀 승 배당
    oddsItems[0].textContent = homeOdds;
    
    // 무승부 배당
    oddsItems[1].textContent = drawOdds;
    
    // 원정팀 승 배당
    oddsItems[2].textContent = awayOdds;
    
    // 투표 수는 기본값 유지 (실제로는 API에서 받아와야 함)
}

/**
 * 팀 폼 업데이트 함수
 * @param {Object} data - 경기 데이터
 */
function updateTeamForm(data) {
    const formItems = document.querySelectorAll('.form-item');
    
    // 모든 form-item 제거
    formItems.forEach(item => item.remove());
    
    // 새로운 form-items 컨테이너 가져오기
    const formContainer = document.querySelector('.form-items');
    
    // 최대 5경기까지 표시
    const maxMatches = Math.min(5, Math.max(data.homeRecentMatches.length, data.awayRecentMatches.length));
    
    for (let i = 0; i < maxMatches; i++) {
        // 홈팀 최근 경기
        // 홈팀 최근 경기 부분 수정
        if (i < data.homeRecentMatches.length) {
            const homeMatch = data.homeRecentMatches[i];
            const homeFormItem = createFormItem(
                data.homeTeamName,
                homeMatch.opponent,
                homeMatch.score,
                homeMatch.opponentScore,
                homeMatch.result,
                true, // 홈팀 기준
                processImagePath(data.homeTeamImage), // 홈팀 이미지 추가
                
                processImagePath(homeMatch.opponentImage) // 상대팀 이미지 추가
            );
 
            formContainer.appendChild(homeFormItem);
        }

        // 원정팀 최근 경기 부분 수정
        if (i < data.awayRecentMatches.length) {
            const awayMatch = data.awayRecentMatches[i];
            const awayFormItem = createFormItem(
                awayMatch.opponent,
                data.awayTeamName,
                awayMatch.opponentScore,
                awayMatch.score,
                awayMatch.result,
                false, // 원정팀 기준
                processImagePath(awayMatch.opponentImage), // 상대팀 이미지 추가
                processImagePath(data.awayTeamImage) // 원정팀 이미지 추가
            );
            formContainer.appendChild(awayFormItem);
        }
    }
}

function createFormItem(leftTeam, rightTeam, leftScore, rightScore, result, isHomeTeam, leftTeamImage, rightTeamImage) {
    const formItem = document.createElement('div');
    formItem.className = 'form-item';
    
    // 결과에 따른 클래스 설정
    let resultClass = '';
    switch(result) {
        case '승':
            resultClass = 'win';
            break;
        case '패':
            resultClass = 'loss';
            break;
        case '무':
            resultClass = 'draw';
            break;
    }
    
    // 🔥 이미지 처리 - 실제 이미지가 있으면 사용, 없으면 플레이스홀더
    let leftImageSrc, rightImageSrc;
    
    if (leftTeamImage) {
        leftImageSrc = leftTeamImage;
    } else {
        const leftInitials = leftTeam.split(' ').map(word => word[0]).join('').substring(0, 3);
        const leftColor = isHomeTeam ? 'ff0000' : getRandomColor();
        leftImageSrc = `https://via.placeholder.com/30/${leftColor}/ffffff?text=${leftInitials}`;
    }
    
    if (rightTeamImage) {
        rightImageSrc = rightTeamImage;
    } else {
        const rightInitials = rightTeam.split(' ').map(word => word[0]).join('').substring(0, 3);
        const rightColor = isHomeTeam ? getRandomColor() : '0000ff';
        rightImageSrc = `https://via.placeholder.com/30/${rightColor}/ffffff?text=${rightInitials}`;
    }
    
    formItem.innerHTML = `
        <img src="${leftImageSrc}" 
             alt="${leftTeam}" class="form-team-logo"
             onload="console.log('✅ 폼 이미지 로드 성공: ${leftTeam}')"
             onerror="console.log('❌ 폼 이미지 로드 실패: ${leftTeam}')">
        <div class="form-result ${resultClass}">${leftScore} - ${rightScore}</div>
        <img src="${rightImageSrc}" 
             alt="${rightTeam}" class="form-team-logo"
             onload="console.log('✅ 폼 이미지 로드 성공: ${rightTeam}')"
             onerror="console.log('❌ 폼 이미지 로드 실패: ${rightTeam}')">
    `;
    
    return formItem;
}

/**
 * 랜덤 색상 생성 함수 (플레이스홀더용)
 * @returns {string} 헥스 색상 코드
 */
function getRandomColor() {
    const colors = ['3498db', 'e74c3c', '2ecc71', 'f39c12', '9b59b6', '1abc9c', 'e67e22'];
    return colors[Math.floor(Math.random() * colors.length)];
}