
const express = require("express");
const router = express.Router();
const db = require("../db");

router.get("/", (req, res) => {
    const query = `
        SELECT *
        FROM alerts
        ORDER BY triggered_at DESC
        LIMIT 50
    `;

    db.query(query, (err, results) => {
        if (err) return res.status(500).send(err);
        res.json(results);
    });
});

module.exports = router;
