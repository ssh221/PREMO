
const express = require('express');
const db = require("../data/db.js");
const query = require("./player.sql")
// const {convertS3UrlToHttp} = require('../data/s3')


// const playerController = require('../controllers/playerController');
const router = express.Router();

// 선수 세부정보 제공 API
router.get('/matchPlayer', async (req, res, next) => {
    const result = {
        "success": false,
        "message": null,
        "content": [],
        "test": []
    }
    
    try {
      const { playerId } = req.query;
      
      if (!playerId) {
        return res.status(400).json({ message: 'playerId 파라미터가 필요합니다.' });
      }

      const queryValue = [playerId];
      const [playerResult] = await db.query(query.findPlayerStat, queryValue);
      const playerData = playerResult[0];

      const [playerSubStatResult] = await db.query(query.findPlayerSubStat, queryValue);
      const playerSubStatData = playerSubStatResult[0];

      
      const playerInfo = {
        Name: playerData.full_name,
        teamName: playerSubStatData.team_common_name,
        teamId: playerSubStatData.team_id,
        teamColor: playerSubStatData.team_color,
        playerImage: "null",
        playerBirth: playerData.birth_date,
        playerNationality: playerData.nationality,
        playerHeight: playerData.height,  
        playerPreferredFoot: playerData.preferred_foot, 
        playerBackNumber: playerData.shirt,  
        position: playerData.primary_position,
        appearances: playerData.matches,
        goals: playerData.goals,
        assists: playerData.assists,
        averageRating: playerData.rating,

        touches_percentile: playerSubStatData.touches_percentile,
        shot_attempts_percentile: playerSubStatData.shot_attempts_percentile,
        goals_percentile: playerSubStatData.goals_percentile,
        aerial_duels_won_percentile: playerSubStatData.aerial_duels_won_percentile,
        defensive_actions_percentile: playerSubStatData.defensive_actions_percentile,
        chances_creted_percentile: playerSubStatData.chances_creted_percentile
      };

      result.content = playerInfo;
      
    } catch (error) {
        next(error);
        result.message = err.message
    }
    result.success = true
    res.json(result)
});

module.exports = router;