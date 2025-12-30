
// backend/db.js
const mysql = require("mysql2");

const db = mysql.createPool({
    host: "localhost",
    user: "spindless_user",
    password: "Admin@123",
    database: "spindless_db"
});

db.getConnection((err, connection) => {
    if (err) {
        console.log("❌ Database Connection Failed:", err);
    } else {
        console.log("🟢 MySQL Connected Successfully");
        connection.release();
    }
});

module.exports = db;

