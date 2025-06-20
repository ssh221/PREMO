// src/routes/leagueRoutes.js - 리그 관련 라우트
const express = require('express');
// const leagueController = require('../controllers/leagueController');
const router = express.Router();

// 리그 정보 제공 API
router.get('/leagueInfo', async (req, res, next) => {
    const result = {
        "success": false,
        "message": null,
        "content": [],
        "test": []
    }

    try {
      const { leagueId } = req.query;
      
      if (!leagueId) {
        return res.status(400).json({ message: 'leagueId 파라미터가 필요합니다.' });
      }
      
      // 리그 정보 데이터 가져오기 (DB 또는 외부 API에서)
      // 여기서는 간단한 예시 데이터를 반환
      const leagueInfo = {
        league: "K리그1",
        leagueInfo: [
          {
            rank: 1,
            teamName: "울산 현대",
            wins: 15,
            draws: 5,
            losses: 3,
            goalsFor: 45,
            goalsAgainst: 20,
            goalDifference: 25
          },
          {
            rank: 2,
            teamName: "전북 현대",
            wins: 14,
            draws: 6,
            losses: 3,
            goalsFor: 40,
            goalsAgainst: 18,
            goalDifference: 22
          }
        ]
      };
      
      res.status(200).json(leagueInfo);
    } catch (error) {
        next(error);
        result.message = err.message
    }
    result.success = true
    result.message = ""

    res.json(result)
  });

module.exports = router;
