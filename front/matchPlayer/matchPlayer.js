// 선수 세부정보 페이지 스크립트
// 탭 전환 및 레이더 차트

document.addEventListener('DOMContentLoaded', function() {
    // 탭 전환 기능 초기화
    initTabs();
    
    // 선수 데이터 로드
    loadPlayerData();
});

// 탭 기능 초기화
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
 * 팀 이미지 업데이트 함수
 * @param {string} teamName - 팀 이름
 */
function updateTeamImage(teamName, teamId) {
    const teamLogoEl = document.querySelector('.team-logo'); // 팀 로고 이미지 요소
    
    if (!teamLogoEl || !teamName) return;
    
    // 팀명을 파일명으로 변환 (공백을 언더스코어로 변경, 소문자로 변환)
    const teamFileName = teamName.toLowerCase().replace(/\s+/g, '_');
    const teamImageSrc = `file:///Users/parkryun/Downloads/pics/team_logos/${teamId}.png`;
    
    teamLogoEl.src = teamImageSrc;
    teamLogoEl.onerror = function() {
        // 이미지 로드 실패 시 플레이스홀더 사용  
        const initials = teamName.split(' ').map(word => word[0]).join('').substring(0, 3);
        const colors = ['ff0000', '0000ff', '00ff00', '800080', 'ff8c00', '008080'];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        this.src = `https://via.placeholder.com/80/${randomColor}/ffffff?text=${initials}`;
        this.onerror = null;
    };
}

/**
 * 팀 컬러 적용 함수
 * @param {string} teamColor - 팀 컬러 (예: "141413", "7d1142")
 */
function applyTeamColor(teamColor) {
    if (!teamColor) return;
    
    // hex 코드 형식으로 변환 (# 추가)
    const hexColor = `#${teamColor}`;
    
    // player-header 요소 찾기
    const playerHeader = document.querySelector('.player-header');
    if (playerHeader) {
        playerHeader.style.backgroundColor = hexColor;
        console.log(`player-header 배경색 적용: ${hexColor}`);
    }
    
    // tab-container 요소 찾기
    const tabContainer = document.querySelector('.tab-container');
    if (tabContainer) {
        tabContainer.style.backgroundColor = hexColor;
        console.log(`tab-container 배경색 적용: ${hexColor}`);
    }
}

/**
 * 탭 콘텐츠 로드 함수
 * @param {string} tabName - 탭 이름 ('profile', 'matches', 'stats', 'career')
 */
function loadTabContent(tabName) {
    console.log(`${tabName} 탭 콘텐츠를 로드합니다.`);
    
    // 현재는 기본 Profile 탭만 표시되므로 추가 구현 없음
    if (tabName !== 'profile') {
        alert(`${tabName} 탭은 현재 구현 중입니다.`);
    }
}

/**
 * 현재 URL에서 matchId와 playerId 추출 
 * @returns {Object} matchId와 playerId
 */
function getUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    return {
        matchId: urlParams.get('matchId'),
        playerId: urlParams.get('playerId')
    };
}

// 선수 데이터 로드 
function loadPlayerData() {
    const { playerId } = getUrlParams();
    
    if (!playerId) {
        console.error('playerId가 없습니다.');
        return;
    }
    
    console.log(`playerId: ${playerId}의 데이터를 로드합니다.`);
    
    // API 호출
    fetch(`http://localhost:3000/player/matchPlayer?playerId=${playerId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('API 응답:', data);
            if (data.success && data.content) {
                updatePlayerProfile(data.content);
                // 🔥 레이더 차트에 실제 데이터 적용
                initRadarChart(data.content);
                // 🔥 팀 컬러 적용
                applyTeamColor(data.content.teamColor);
            } else {
                console.error('API 응답 오류:', data);
            }
        })
        .catch(error => {
            console.error('선수 데이터를 로드하는 중 오류가 발생했습니다:', error);
        });
}

/**
 * 선수 프로필 정보 업데이트 함수
 * @param {Object} data - 선수 데이터
 */
function updatePlayerProfile(data) {
    console.log('선수 프로필 업데이트:', data);
    
    // 선수 기본 정보 업데이트
    const playerNameEl = document.querySelector('.player-name');
    const playerTeamEl = document.querySelector('.player-team span');
    const profileImgEl = document.querySelector('.profile-img');
    
    if (playerNameEl) playerNameEl.textContent = data.Name || 'Unknown Player';
    if (playerTeamEl) playerTeamEl.textContent = data.teamName || 'Unknown Team';
    
    // 🔥 선수 이미지 업데이트 - playerId 기반 동적 경로
    if (profileImgEl) {
        const { playerId } = getUrlParams();
        const imageSrc = `file:///Users/parkryun/Downloads/pics/profile_pictures/${playerId}.png`;
        
        profileImgEl.src = imageSrc;
        profileImgEl.onerror = function() {
            // 이미지 로드 실패 시 플레이스홀더 사용
            const initials = (data.Name || 'UK').split(' ').map(word => word[0]).join('').substring(0, 2);
            this.src = `https://via.placeholder.com/120/0066cc/ffffff?text=${initials}`;
            this.onerror = null;
        };
    }
    
    // 🔥 팀 이미지 업데이트 - 팀명 기반 동적 경로
    updateTeamImage(data.teamName, data.teamId);
    
    // 프로필 통계 업데이트
    const statItems = document.querySelectorAll('.stats-grid .stat-item');
    
    if (statItems.length >= 6) {
        // 키
        const heightEl = statItems[0].querySelector('.stat-value');
        if (heightEl) heightEl.textContent = `${data.playerHeight || 0} cm`;
        
        // 나이 및 생년월일
        if (data.playerBirth) {
            const birthDate = new Date(data.playerBirth);
            const age = calculateAge(birthDate);
            const formattedBirthDate = formatDate(birthDate);
            
            const ageEl = statItems[1].querySelector('.stat-value');
            const birthEl = statItems[1].querySelector('.stat-label');
            if (ageEl) ageEl.textContent = `${age} years`;
            if (birthEl) birthEl.textContent = formattedBirthDate;
        }
        
        // 국적
        const nationalityEl = statItems[2].querySelector('.stat-value');
        if (nationalityEl) {
            // 🔥 백엔드에서 받은 국적 데이터 사용
            nationalityEl.textContent = data.playerNationality || 'Unknown';
        }
        
        // 등번호
        const numberEl = statItems[3].querySelector('.stat-value');
        if (numberEl) numberEl.textContent = data.playerBackNumber || 0;
        
        // 주발
        const footEl = statItems[4].querySelector('.stat-value');
        if (footEl) footEl.textContent = data.playerPreferredFoot || 'Unknown';
        
        // 시장 가치는 그대로 유지 (API에서 제공하지 않음)
    }
    
    // 시즌 통계 업데이트
    updateSeasonStats({
        matches: data.appearances || 0,
        goals: data.goals || 0,
        assists: data.assists || 0,
        rating: data.averageRating || 0
    });
}

/**
 * 시즌 통계 업데이트 함수
 * @param {Object} seasonStats - 시즌 통계 데이터
 */
function updateSeasonStats(seasonStats) {
    // 통계 업데이트
    const statItems = document.querySelectorAll('.season-stats-grid .season-stat-item');
    
    if (statItems.length >= 4) {
        // 경기 수
        const matchesEl = statItems[0].querySelector('.season-stat-value');
        if (matchesEl) matchesEl.textContent = seasonStats.matches;
        
        // 골
        const goalsEl = statItems[1].querySelector('.season-stat-value');
        if (goalsEl) goalsEl.textContent = seasonStats.goals;
        
        // 어시스트
        const assistsEl = statItems[2].querySelector('.season-stat-value');
        if (assistsEl) assistsEl.textContent = seasonStats.assists;
        
        // 평점
        const ratingEl = statItems[3].querySelector('.season-stat-value');
        if (ratingEl) {
            const rating = parseFloat(seasonStats.rating) || 0;
            ratingEl.textContent = rating.toFixed(2);
            
            // 평점에 따른 색상 조정
            if (rating >= 7.5) {
                ratingEl.style.color = '#4caf50'; // 녹색 (아주 좋음)
            } else if (rating >= 7.0) {
                ratingEl.style.color = '#8bc34a'; // 연두색 (좋음)
            } else if (rating >= 6.5) {
                ratingEl.style.color = '#ffc107'; // 노란색 (보통)
            } else {
                ratingEl.style.color = '#ff5722'; // 주황색 (나쁨)
            }
        }
    }
}

/**
 * 🔥 간단한 레이더 차트 초기화 함수
 * @param {Object} playerData - 백엔드에서 받은 선수 데이터
 */
function initRadarChart(playerData) {
    const radarData = document.getElementById('radar-data');
    
    if (!radarData) return;
    
    // 백엔드에서 받은 실제 퍼센타일 데이터 사용
    const data = {
        top: playerData.touches_percentile || 0,                    // 12시 - Touches
        topRight: playerData.chances_creted_percentile || 0,        // 2시 - Chances Created  
        bottomRight: playerData.defensive_actions_percentile || 0,  // 4시 - Defensive Actions
        bottom: playerData.goals_percentile || 0,                   // 6시 - Goals
        bottomLeft: playerData.shot_attempts_percentile || 0,       // 8시 - Shot Attempts
        topLeft: playerData.aerial_duels_won_percentile || 0        // 10시 - Aerial Duels
    };
    
    console.log('레이더 차트 데이터:', data);
    
    // 축 라벨 업데이트 (퍼센트 표시)
    updateAxisLabels(data);
    
    // 레이더 차트 모양 업데이트
    updateSimpleRadarChart(data);
}

/**
 * 🔥 축 라벨 업데이트 (6개 위치 고정)
 * @param {Object} data - 퍼센타일 데이터 (0~100)
 */
function updateAxisLabels(data) {
    const labels = [
        { class: 'top', value: data.top, name: 'Touches' },
        { class: 'top-right', value: data.topRight, name: 'Chances Created' },
        { class: 'bottom-right', value: data.bottomRight, name: 'Defensive Actions' },
        { class: 'bottom', value: data.bottom, name: 'Goals' },
        { class: 'bottom-left', value: data.bottomLeft, name: 'Shot Attempts' },
        { class: 'top-left', value: data.topLeft, name: 'Aerial Duels' }
    ];
    
    labels.forEach(label => {
        const element = document.querySelector(`.axis-label.${label.class}`);
        if (element) {
            element.innerHTML = `
                <span class="percentage">${Math.round(label.value)}%</span>
                <span class="stat-name">${label.name}</span>
            `;
        }
    });
}

/**
 * 🔥 간단한 레이더 차트 업데이트
 * @param {Object} data - 퍼센타일 데이터 (0~100)
 */
function updateSimpleRadarChart(data) {
    const radarData = document.getElementById('radar-data');
    if (!radarData) return;
    
    // 정규화된 데이터 (0~1 사이 값)
    const normalizedData = {
        top: data.top / 100,
        topRight: data.topRight / 100,
        bottomRight: data.bottomRight / 100,
        bottom: data.bottom / 100,
        bottomLeft: data.bottomLeft / 100,
        topLeft: data.topLeft / 100
    };
    
    // 6각형 좌표 계산
    const polygonPoints = calculateSimpleRadarPolygon(normalizedData);
    
    // 클립 패스 적용 (빨간색 고정)
    radarData.style.clipPath = `polygon(${polygonPoints})`;
    radarData.style.backgroundColor = 'rgba(229, 57, 53, 0.7)'; // 빨간색 고정
}

/**
 * 🔥 6각형 좌표 계산 (위치 정확히 고정)
 * @param {Object} data - 6가지 방향의 데이터 값 (0~1 사이)
 * @returns {string} 다각형 좌표 문자열
 */
function calculateSimpleRadarPolygon(data) {
    const centerX = 50;
    const centerY = 50;
    const maxRadius = 35;
    
    // 🔥 정확한 6각형 각도 (30도씩)
    const angles = [
        -Math.PI/2,          // top (12시)
        -Math.PI/6,          // top-right (2시)  
        Math.PI/6,           // bottom-right (4시)
        Math.PI/2,           // bottom (6시)
        5*Math.PI/6,         // bottom-left (8시)
        -5*Math.PI/6         // top-left (10시)
    ];
    
    // 데이터 배열 (시계방향 순서)
    const dataValues = [
        data.top,         // 12시
        data.topRight,    // 2시
        data.bottomRight, // 4시
        data.bottom,      // 6시
        data.bottomLeft,  // 8시
        data.topLeft      // 10시
    ];
    
    // 각 꼭지점 좌표 계산
    let points = [];
    
    for (let i = 0; i < 6; i++) {
        // 최소값 보장 (0%일 때도 중앙에서 약간 떨어지게)
        const radius = Math.max(maxRadius * dataValues[i], maxRadius * 0.05);
        const x = centerX + radius * Math.cos(angles[i]);
        const y = centerY + radius * Math.sin(angles[i]);
        points.push(`${x.toFixed(1)}% ${y.toFixed(1)}%`);
    }
    
    return points.join(', ');
}

/**
 * 나이 계산 함수
 * @param {Date} birthDate - 생년월일
 * @returns {number} 나이
 */
function calculateAge(birthDate) {
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    return age;
}

/**
 * 날짜 포맷 함수
 * @param {Date} date - 날짜 객체
 * @returns {string} 포맷된 날짜 문자열 (예: "8 Sept 1994")
 */
function formatDate(date) {
    const day = date.getDate();
    const month = date.toLocaleString('en-US', { month: 'short' });
    const year = date.getFullYear();
    
    return `${day} ${month} ${year}`;
}

/**
 * 탭 콘텐츠 렌더링 함수 (실제 API 구현 시 사용)
 * @param {string} tabName - 탭 이름
 * @param {Object} data - 탭 콘텐츠 데이터
 */
function renderTabContent(tabName, data) {
    const contentContainer = document.querySelector('.content-container');
    
    if (!contentContainer) return;
    
    // 기존 콘텐츠 백업 (Profile 탭 콘텐츠)
    if (!window.profileContent && tabName !== 'profile') {
        window.profileContent = contentContainer.innerHTML;
    }
    
    switch (tabName) {
        case 'profile':
            // Profile 탭이 기본 콘텐츠이므로 백업된 내용이 있으면 복원
            if (window.profileContent) {
                contentContainer.innerHTML = window.profileContent;
            }
            break;
            
        case 'matches':
            // Matches 탭 콘텐츠 렌더링
            contentContainer.innerHTML = renderMatchesContent(data);
            break;
            
        case 'stats':
            // Stats 탭 콘텐츠 렌더링
            contentContainer.innerHTML = renderStatsContent(data);
            break;
            
        case 'career':
            // Career 탭 콘텐츠 렌더링
            contentContainer.innerHTML = renderCareerContent(data);
            break;
            
        default:
            console.error(`알 수 없는 탭 이름: ${tabName}`);
    }
}

/**
 * Matches 탭 콘텐츠 렌더링 함수 (예시)
 * @param {Object} data - Matches 데이터
 * @returns {string} HTML 콘텐츠
 */
function renderMatchesContent(data) {
    return `
        <div class="section-card">
            <h2 class="section-title">최근 경기</h2>
            <div class="matches-list">
                <p>최근 경기 목록이 여기에 표시됩니다.</p>
            </div>
        </div>
    `;
}

/**
 * Stats 탭 콘텐츠 렌더링 함수 (예시)
 * @param {Object} data - Stats 데이터
 * @returns {string} HTML 콘텐츠
 */
function renderStatsContent(data) {
    return `
        <div class="section-card">
            <h2 class="section-title">세부 통계</h2>
            <div class="stats-content">
                <p>세부 통계 정보가 여기에 표시됩니다.</p>
            </div>
        </div>
    `;
}

/**
 * Career 탭 콘텐츠 렌더링 함수 (예시)
 * @param {Object} data - Career 데이터
 * @returns {string} HTML 콘텐츠
 */
function renderCareerContent(data) {
    return `
        <div class="section-card">
            <h2 class="section-title">경력 정보</h2>
            <div class="career-content">
                <p>선수 경력 정보가 여기에 표시됩니다.</p>
            </div>
        </div>
    `;
}