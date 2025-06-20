const express = require('express');
const db = require("../data/db.js");
const query = require("./match.sql");
// const {convertS3UrlToHttp} = require('../data/s3')
const router = express.Router();

// const matchController = require('../controllers/matchController');

// 경기 일정 정보 제공 API
router.get('/matchSchedule', async (req, res, next) => {
    const result = {
        "success": false,
        "message": null,
        "content": [],
        "test": []
    }

    try {
      const { matchDate } = req.query;
      
      if (!matchDate) {
        return res.status(400).json({ message: 'matchDate 파라미터가 필요합니다.' });
      }

      const startDate = matchDate + ' 00:00:00';
      const nextDay = new Date(matchDate);
      nextDay.setDate(nextDay.getDate() + 1);
      const endDate = nextDay.toISOString().split('T')[0] + ' 00:00:00';

      const dateValue = [startDate, endDate];
      const [matchData] = await db.query(query.findMatchSchedule, dateValue);

      const matchSchedule = matchData.map(match => ({
        homeTeamName: match.home_team_name,
        awayTeamName: match.away_team_name, 
        matchTime: match.match_time,
        homeTeamImage: match.home_team_image,
        awayTeamImage: match.away_team_image,
        league: "Premier League",
        matchId: match.match_id
      }));
      
      result.content = matchSchedule;

    } catch (error) {
        next(error);
        result.message = err.message
    }
    result.success = true;
    res.json(result)
  });

// 특정 경기 정보 제공 API
router.get('/matchInfo', async (req, res, next) => {
    const result = {
        "success": false,
        "message": null,
        "content": [],
        "test": []
    }

  try {
    const { matchId } = req.query;
    
    if (!matchId) {
      return res.status(400).json({ message: 'matchId 파라미터가 필요합니다.' });
    }

    const queryValue = [matchId];
    const [infoResult] = await db.query(query.findMatchInfo, queryValue);
    const infoData = infoResult[0];

    // home recent matchs
    const queryValue2 = [infoData.home_team_id, infoData.home_team_id, matchId];
    const [homeRecentData] = await db.query(query.findRecentMatchs, queryValue2);

    // away recent matchs
    const queryValue3 = [infoData.away_team_id, infoData.away_team_id, matchId];
    const [awayRecentData] = await db.query(query.findRecentMatchs, queryValue3);
  
    const matchInfo = {
      homeTeamName: infoData.home_team_name,
      awayTeamName: infoData.away_team_name,
      matchTime: infoData.match_time,
      homeTeamImage: infoData.home_team_image,
      awayTeamImage: infoData.away_team_image,
      league: "Premier League",
      matchVenue: infoData.stadium_name,
      winProbability: 0.65, // db 
      betting: 1.75, // db

      homeRecentMatches: homeRecentData.map(match => {
        const isHome = match.home_team_id === infoData.home_team_id;
        const myScore = isHome ? match.home_goals : match.away_goals;
        const opponentScore = isHome ? match.away_goals : match.home_goals;
        const opponent = isHome ? match.away_team_name : match.home_team_name;
        
        const opponentImage = isHome ? match.away_team_image : match.home_team_image;
        
        let result;
        if (myScore > opponentScore) {
          result = "승";
        } else if (myScore < opponentScore) {
          result = "패";
        } else {
          result = "무";
        }
        
        return {
          opponent: opponent,
          opponentImage: opponentImage,
          homeTeamImage: match.home_team_image,
          result: result,
          score: myScore,
          opponentScore: opponentScore
        };
    }),
      
      awayRecentMatches: awayRecentData.map(match => {
        const isHome = match.home_team_id === infoData.away_team_id;
        const myScore = isHome ? match.home_goals : match.away_goals;
        const opponentScore = isHome ? match.away_goals : match.home_goals;
        const opponent = isHome ? match.away_team_name : match.home_team_name;
      
        const opponentImage = isHome ? match.away_team_image : match.home_team_image;
      
        let result;
        if (myScore > opponentScore) {
          result = "승";
        } else if (myScore < opponentScore) {
          result = "패";
        } else {
          result = "무";
        }

        return {
          opponent: opponent,
          opponentImage: opponentImage,  
          homeTeamImage: match.home_team_image,
          result: result,
          score: myScore,
          opponentScore: opponentScore
        };
      })
    };

    result.content = matchInfo;

  } catch (error) {
        next(error);
        result.message = err.message
    }
    result.success = true
    res.json(result)
});

// 경기 분석 및 인사이트 제공 API
router.get('/matchInsight', async (req, res, next) => {
    const result = {
      "success": false,
      "message": null,
      "content": [],
      "test": []
    }

    try {

      // matchId db connect
      const { matchId } = req.query;
      
      if (!matchId) {
        return res.status(400).json({ message: 'matchId 파라미터가 필요합니다.' });
      }
      
      const matchInsight = {
        homeTeamName: "Manchester United",
        awayTeamName: "Real Madrid",
        matchTime: "17:30",
        homeTeamImage: null,
        awayTeamImage: null,
        league: "Premier League",
        matchVenue: "Old Trafford, Manchester",
        homeInsight: "최근 홈 경기에서 높은 점유율과 안정적인 수비력을 보여주고 있습니다.",
        awayInsight: "원정 경기에서는 카운터 어택에 의존하는 전략을 주로 사용합니다.",
        newsSummary: "주전 공격수의 부상으로 인해 2선 공격수의 활약이 중요할 것으로 예상됩니다."
      };

      result.content = matchInsight;
      
    } catch (error) {
        next(error);
        result.message = err.message
    }
    result.success = true
    result.message = ""

    res.json(result)
  });

// 경기 세부정보, 예측, 데이터 분석 제공 API
router.get('/matchDetail', async (req, res, next) => {
    const result = {
        "success": false,
        "message": null,
        "content": [],
        "test": []
    }

    try {
        const { matchId } = req.query;
    
        if (!matchId) {
          return res.status(400).json({ message: 'matchId 파라미터가 필요합니다.' });
        }

        const queryValue = [matchId];
        const [infoResult] = await db.query(query.findMatchInfo, queryValue);
        const infoData = infoResult[0];

        const [modelOutputResult] = await db.query(query.findModelOutput, queryValue);
        const modelOutputData = modelOutputResult[0];

        const [homeKeyPlayerStatResult] = await db.query(query.findKeyPlayerStat, modelOutputData.home_keyplayer_id);
        const homeKeyPlayerStatData = homeKeyPlayerStatResult[0];

        const [awayKeyPlayerStatResult] = await db.query(query.findKeyPlayerStat, modelOutputData.away_keyplayer_id);
        const awayKeyPlayerStatData = awayKeyPlayerStatResult[0];

        const matchDetail = {
          homeTeamName: infoData.home_team_name,
          awayTeamName: infoData.away_team_name,
          matchTime: infoData.match_time,
          homeTeamImage: infoData.home_team_image,
          awayTeamImage: infoData.away_team_image,
          league: "Premier League",
          matchVenue: infoData.stadium_name,
          winProbability: modelOutputData.home_winrate,
          drawProbability: modelOutputData.drawrate,
          loseProbability: 100 - modelOutputData.winProbability - modelOutputData.drawProbability,
          predicted: [
            { 
              homeScore: modelOutputData.home_score_1,
              awayScore: modelOutputData.away_score_1,
              probability: modelOutputData.score_1_prob
            },
            { 
              homeScore: modelOutputData.home_score_2,
              awayScore: modelOutputData.away_score_2,
              probability: modelOutputData.score_2_prob
            },
            { 
              homeScore: modelOutputData.home_score_3,
              awayScore: modelOutputData.away_score_3,
              probability: modelOutputData.score_3_prob
            }
          ],

          homeKeyPlayer: {
            playerId: modelOutputData.home_keyplayer_id,
            name: homeKeyPlayerStatData.full_name,
            touches_percentile: homeKeyPlayerStatData.touches_percentile,
            shot_attempts_percentile: homeKeyPlayerStatData.shot_attempts_percentile,
            goals_percentile: homeKeyPlayerStatData.goals_percentile,
            aerial_duels_won_percentile: homeKeyPlayerStatData.aerial_duels_won_percentile,
            defensive_actions_percentile: homeKeyPlayerStatData.defensive_actions_percentile,
            chances_creted_percentile: homeKeyPlayerStatData.chances_creted_percentile
          },
          awayKeyPlayer: {
            playerId: modelOutputData.away_keyplayer_id,
            name: awayKeyPlayerStatData.full_name,
            touches_percentile: awayKeyPlayerStatData.touches_percentile,
            shot_attempts_percentile: awayKeyPlayerStatData.shot_attempts_percentile,
            goals_percentile: awayKeyPlayerStatData.goals_percentile,
            aerial_duels_won_percentile: awayKeyPlayerStatData.aerial_duels_won_percentile,
            defensive_actions_percentile: awayKeyPlayerStatData.defensive_actions_percentile,
            chances_creted_percentile: awayKeyPlayerStatData.chances_creted_percentile
          }
        };
        
        result.content = matchDetail;
    } catch (error) {
        next(error);
        result.message = err.message
    }
    
    result.success = true
    res.json(result)
});

// 경기 헤드투헤드 분석 제공 API
router.get('/matchHeadToHead', async (req, res, next) => {
    const result = {
        "success": false,
        "message": null,
        "content": [],
        "test": []
    }

    try {
      const { matchId } = req.query;
      
      if (!matchId) {
        return res.status(400).json({ message: 'matchId 파라미터가 필요합니다.' });
      }

      const queryValue = [matchId];
      const [infoResult] = await db.query(query.findMatchInfo, queryValue);
      const infoData = infoResult[0];

      const queryValue2 = [infoData.home_team_id, infoData.away_team_id, infoData.away_team_id, infoData.home_team_id, matchId];
      const [headToHeadData] = await db.query(query.findHeadToHead, queryValue2);
 
      // 승패 통계 계산
      let homeWin = 0;
      let awayWin = 0;
      let draw = 0;

      const matchInfo = headToHeadData.map(match => {
        
        // 현재 홈팀 기준으로 승패 계산
        const isCurrentHomeTeamAtHome = match.home_team_name === infoData.home_team_name;
        if (isCurrentHomeTeamAtHome) {
          // 현재 홈팀이 실제로 홈에서 경기한 경우
          if (match.home_goals > match.away_goals) {
            homeWin++;
          } else if (match.home_goals < match.away_goals) {
            awayWin++;
          } else {
            draw++;
          }
        } else {
          // 현재 홈팀이 어웨이에서 경기한 경우
          if (match.away_goals > match.home_goals) {
            homeWin++;
          } else if (match.away_goals < match.home_goals) {
            awayWin++;
          } else {
            draw++;
          }
        }

        return {
          league: "Premier League",
          matchDate: match.match_date,
          matchVenue: match.home_stadium, // 홈팀의 경기장
          homeScore: match.home_goals,
          awayScore: match.away_goals,
          match_id: match.match_id,
          homeTeamName: match.home_team_name,
          awayTeamName: match.away_team_name,
          homeTeamImage: match.home_team_image,
          awayTeamImage: match.away_team_image
        };
      });

      const headToHead = {
        homeTeamName: infoData.home_team_name,
        awayTeamName: infoData.away_team_name,
        homeTeamImage: infoData.home_team_image,
        awayTeamImage: infoData.away_team_image,
        matchInfo: matchInfo,
        homeWin: homeWin,
        awayWin: awayWin,
        draw: draw
      };

      result.content = headToHead;

    } catch (error) {
        next(error);
        result.message = err.message
    }
    result.success = true
    res.json(result)
  });

module.exports = router;