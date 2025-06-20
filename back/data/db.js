const mysql = require('mysql2/promise');
require('dotenv').config();

const pool = mysql.createPool({
    host: 'premo-instance.czwmu86ms4yl.us-east-1.rds.amazonaws.com',
    database: 'premo',
    user: 'admin',
    password: 'tteam891',
});


module.exports = pool; 
