const findPlayerStat = `
    SELECT 
      p.full_name,
      p.nationality,
      p.birth_date,
      p.height,
      p.preferred_foot,
      p.shirt,
      p.primary_position,
      ps.matches,
      ps.goals,
      ps.assists,
      ps.rating
    FROM premo.player p
    JOIN premo.player_stat ps ON p.player_id = ps.player_id
    WHERE p.player_id = ? AND ps.season_id = 719
`;

const findPlayerSubStat = `
   SELECT 
       ps.touches_percentile,
       ps.shot_attempts_percentile,
       ps.goals_percentile,
       ps.defensive_actions_percentile,
       ps.aerial_duels_won_percentile,
       ps.chances_created_percentile,
       t.team_common_name,
       t.team_color,
       t.team_id
   FROM premo.player_stat ps
   LEFT JOIN premo.team t ON ps.team_id = t.team_id
   WHERE ps.player_id = ? AND ps.season_id = 719
`;

module.exports = {
    findPlayerStat: findPlayerStat,
    findPlayerSubStat: findPlayerSubStat
}