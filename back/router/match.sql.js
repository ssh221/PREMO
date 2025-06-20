const findMatchSchedule = `
SELECT 
   m.match_id,
   m.home_team_id,
   m.away_team_id,
   TIME_FORMAT(m.kr_start_time, '%H:%i') as match_time,
   ht.team_common_name as home_team_name,
   at.team_common_name as away_team_name,
   ht.image_url as home_team_image,
   at.image_url as away_team_image
FROM premo.match m
JOIN premo.team ht ON m.home_team_id = ht.team_id
JOIN premo.team at ON m.away_team_id = at.team_id
WHERE m.kr_start_time >= ? 
AND m.kr_start_time < ?
ORDER BY m.kr_start_time ASC
`;

const findMatchInfo = `
SELECT 
   m.home_team_id,
   m.away_team_id,
   TIME_FORMAT(m.kr_start_time, '%H:%i') as match_time,
   ht.team_common_name as home_team_name,
   ht.stadium_name as stadium_name,
   at.team_common_name as away_team_name,
   ht.image_url as home_team_image,
   at.image_url as away_team_image
   FROM premo.match m
   JOIN premo.team ht ON m.home_team_id = ht.team_id
   JOIN premo.team at ON m.away_team_id = at.team_id
   WHERE m.match_id = ?
`;

const findRecentMatchs = `
SELECT 
   m.match_id,
   m.home_team_id,
   m.away_team_id,
   m.home_goals,
   m.away_goals,
   ht.team_common_name as home_team_name,
   at.team_common_name as away_team_name,
   ht.image_url as home_team_image,
   at.image_url as away_team_image
   FROM premo.match m
   JOIN premo.team ht ON m.home_team_id = ht.team_id
   JOIN premo.team at ON m.away_team_id = at.team_id
   WHERE (m.home_team_id = ? OR m.away_team_id = ?)
   AND m.match_id != ?
   AND m.home_goals IS NOT NULL 
   AND m.away_goals IS NOT NULL
   ORDER BY m.kr_start_time DESC
   LIMIT 5
`

const findHeadToHead = `
SELECT 
     m.match_id,
     m.home_goals,
     m.away_goals,
     ht.team_common_name as home_team_name,
     at.team_common_name as away_team_name,
     ht.stadium_name as home_stadium,
     at.stadium_name as away_stadium,
     DATE_FORMAT(m.kr_start_time, '%Y-%m-%d') as match_date,
     m.status,
     ht.image_url as home_team_image,
     at.image_url as away_team_image
   FROM premo.match m
   JOIN premo.team ht ON m.home_team_id = ht.team_id
   JOIN premo.team at ON m.away_team_id = at.team_id
   WHERE ((m.home_team_id = ? AND m.away_team_id = ?) 
       OR (m.home_team_id = ? AND m.away_team_id = ?))
     AND m.match_id != ?
     AND m.home_goals IS NOT NULL 
     AND m.away_goals IS NOT NULL
   ORDER BY m.kr_start_time DESC
`;

const findModelOutput = `
    SELECT 
      home_winrate,
      drawrate,
      home_score_1,
      away_score_1,
      score_1_prob,
      home_score_2,
      away_score_2,
      score_2_prob,
      home_score_3,
      away_score_3,
      score_3_prob,
      home_keyplayer_id,
      away_keyplayer_id
    FROM premo.model_output 
    WHERE match_id = ?
`
const findKeyPlayerStat = `
   SELECT 
       p.player_id,
       p.full_name,
       ps.touches_percentile,
       ps.shot_attempts_percentile,
       ps.goals_percentile,
       ps.defensive_actions_percentile,
       ps.aerial_duels_won_percentile,
       ps.chances_created_percentile
   FROM premo.player p
   LEFT JOIN premo.player_stat ps ON p.player_id = ps.player_id
   WHERE p.player_id = ? AND ps.season_id = 719;
`

module.exports = {
    findMatchSchedule: findMatchSchedule,
    findMatchInfo: findMatchInfo,
    findRecentMatchs: findRecentMatchs,
    findHeadToHead: findHeadToHead,
    findModelOutput: findModelOutput,
    findKeyPlayerStat: findKeyPlayerStat
}