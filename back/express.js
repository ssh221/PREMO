const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const port = 3000;

const matchApi = require('./router/match');
const playerApi = require('./router/player');
const leagueApi = require('./router/league');


const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use('/pics', express.static(path.join(__dirname, '../../pics')));
app.use('/front', express.static(path.join(__dirname, '../front')));


app.use('/match', matchApi);
app.use('/player', playerApi);
app.use('/league', leagueApi);

app.use((req, res, next) => {
  res.status(404).json({ message: '요청하신 경로를 찾을 수 없습니다.' });
});


app.listen(PORT, () => {
  console.log(`http://localhost:${PORT} 실행 중`);
});

module.exports = app;