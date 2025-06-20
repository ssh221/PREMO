
document.addEventListener('DOMContentLoaded', function() {
    // 날짜 탭 클릭 이벤트 처리
    initDateTabs();
    
    // 경기 항목 클릭 이벤트 처리
    initMatchItemEvents();
    
    // 초기 경기 데이터 로드 (오늘 날짜)
    const today = document.querySelector('.date-tab.active').getAttribute('data-date');
    loadMatchesByDate(today);
});


// 날짜 탭 초기화 함수
function initDateTabs() {
    generateDateTabs();
    
    const dateTabs = document.querySelectorAll('.date-tab');
    
    dateTabs.forEach(tab => {
        tab.addEventListener('click', function() {

            dateTabs.forEach(t => t.classList.remove('active'));

            this.classList.add('active');

            showLoading(true);

            const selectedDate = this.getAttribute('data-date');
            
            loadMatchesByDate(selectedDate);
        });
    });
}


// 경기 항목 클릭 이벤트 초기화 함수
function initMatchItemEvents() {
    document.querySelectorAll('.match-item').forEach(match => {
        match.addEventListener('click', function() {
            const matchId = this.getAttribute('data-match-id');
            // 경기 상세 페이지로 이동
            navigateToMatchDetail(matchId);
        });
    });
}


// 날짜별 경기 데이터 불러오기 함수
async function loadMatchesByDate(date) {
    
    // 로딩 중 표시
    showLoading(true);
    
    try {
        const response = await fetch(`http://localhost:3000/match/matchSchedule?matchDate=${date}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(data)
        // 받아온 데이터로 화면 업데이트
        updateMatchesContainer(data.content || []);
        
    } catch (error) {
        console.error('경기 데이터를 불러오는 중 오류가 발생했습니다:', error);
        
        // 오류 발생 시 빈 배열로 업데이트 (또는 오류 메시지 표시)
        updateMatchesContainer([]);
        
        // 사용자에게 오류 알림 (선택사항)
        alert('경기 데이터를 불러오는데 실패했습니다. 다시 시도해주세요.');
        
    } finally {
        // 로딩 숨기기
        showLoading(false);
    }
}


// 매치 컨테이너 업데이트 함수
function updateMatchesContainer(matches) {
    const container = document.getElementById('matches-container');
    
    // 기존 내용 비우기
    container.innerHTML = '';
    
    // 경기가 없는 경우
    if (!matches || matches.length === 0) {
        container.innerHTML = '<div class="no-matches">해당 날짜에 예정된 경기가 없습니다.</div>';
        return;
    }
    
    // 단순한 매치 리스트 생성
    const matchList = document.createElement('div');
    matchList.className = 'match-list';
    
    // 모든 매치 항목 추가
    matches.forEach((match, index) => {
        const matchItem = createMatchItem(match, index);
        matchList.appendChild(matchItem);
    });
    
    container.appendChild(matchList);
    
    // 경기 항목 클릭 이벤트 다시 초기화
    initMatchItemEvents();
}

function createMatchItem(match, index) {
    const item = document.createElement('div');
    item.className = 'match-item';
    
    // API에서 받아온 실제 matchId 사용
    item.setAttribute('data-match-id', match.matchId);
    
    // 경기 데이터를 data 속성으로 저장 (선택사항)
    item.setAttribute('data-match-data', JSON.stringify(match));
    
    // 팀 이미지 처리 (null인 경우 기본 이미지 사용)
    // const homeTeamImage = match.homeTeamImage 
    //     ? `../../..${match.homeTeamImage}` 
    //     : getDefaultTeamImage(match.homeTeamName);
        
    // // const homeTeamImage = match.homeTeamImage 
    // // ? `file:///Users/parkryun/Downloads/pics/team_logos/${match.homeTeamImage.split('/').pop()}`
    // // : getDefaultTeamImage(match.homeTeamName);

    // const awayTeamImage = match.awayTeamImage 
    //     ? `../../..${match.awayTeamImage}` 
    //     : getDefaultTeamImage(match.awayTeamName);
    const homeTeamImage = match.homeTeamImage 
        ? `file:///Users/parkryun/Downloads/pics/team_logos/${match.homeTeamImage.split('/').pop()}`
        : getDefaultTeamImage(match.homeTeamName);
    
    const awayTeamImage = match.awayTeamImage 
        ? `file:///Users/parkryun/Downloads/pics/team_logos/${match.awayTeamImage.split('/').pop()}`
        : getDefaultTeamImage(match.awayTeamName);

    console.log(homeTeamImage)
    console.log(awayTeamImage)

    item.innerHTML = `
        <div class="team-info">
            <span class="team-name">${match.homeTeamName}</span>
            <img src="${homeTeamImage}" alt="${match.homeTeamName}" class="team-logo">
        </div>
        <div class="match-time">${match.matchTime}</div>
        <div class="team-info right">
            <img src="${awayTeamImage}" alt="${match.awayTeamName}" class="team-logo">
            <span class="team-name">${match.awayTeamName}</span>
        </div>
    `;
    
    return item;
}

function navigateToMatchDetail(matchId) {
    window.location.href = `../matchInfo/matchInfo.html?matchId=${matchId}`;
}

function showLoading(show) {
    const loadingEl = document.querySelector('.loading');
    const matchesContainer = document.getElementById('matches-container');
    
    if (show) {
        loadingEl.classList.add('active');
        matchesContainer.style.display = 'none';
    } else {
        loadingEl.classList.remove('active');
        matchesContainer.style.display = 'block';
    }
}

// 오늘 날짜를 기준으로 날짜 탭을 동적으로 생성하는 함수
 function generateDateTabs() {
    const today = new Date();
    const dateTabsContainer = document.querySelector('.date-tabs');
    
    // 기존 탭들 제거
    dateTabsContainer.innerHTML = '';
    
    // -2일부터 +2일까지 5개의 탭 생성
    for (let i = -2; i <= 2; i++) {
        const targetDate = new Date(today);
        targetDate.setDate(today.getDate() + i);
        
        const tab = document.createElement('div');
        tab.className = 'date-tab';
        tab.setAttribute('data-date', formatDateForAPI(targetDate)); // YYYY-MM-DD 형식
        
        // 탭 텍스트 설정
        tab.textContent = getDateTabText(i, targetDate);
        
        // 오늘이면 active 클래스 추가
        if (i === 0) {
            tab.classList.add('active');
        }
        
        dateTabsContainer.appendChild(tab);
    }
}

// 날짜 탭 텍스트를 반환하는 함수
function getDateTabText(dayOffset, date) {
    switch (dayOffset) {
        case -1:
            return 'Yesterday';
        case 0:
            return 'Today';
        case 1:
            return 'Tomorrow';
        default:
            // -2일, +2일의 경우 "Thu 22 May" 형식으로 표시
            return formatDateForDisplay(date);
    }
}

// 날짜를 "Thu 22 May" 형식으로 포맷하는 함수
function formatDateForDisplay(date) {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const dayName = days[date.getDay()];
    const day = date.getDate();
    const monthName = months[date.getMonth()];
    
    return `${dayName} ${day} ${monthName}`;
}

// 날짜를 API용 YYYY-MM-DD 형식으로 포맷하는 함수
function formatDateForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

// 팀명에 따른 기본 이미지를 반환하는 함수
function getDefaultTeamImage(teamName) {
    // 팀명의 첫 글자들로 간단한 로고 생성
    const initials = teamName.split(' ').map(word => word[0]).join('').substring(0, 3);
    const colors = ['ff0000', '0000ff', '00ff00', '800080', 'ff8c00', '008080'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    
    return `https://via.placeholder.com/36/${randomColor}/ffffff?text=${initials}`;
}