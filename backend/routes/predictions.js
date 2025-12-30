const express = require("express");
const router = express.Router();
const db = require("../db.js");
const { spawn } = require("child_process");
const path = require("path");

router.get("/latest", (req, res) => {
  const limit = parseInt(req.query.limit || 10);

  const query = `
    SELECT sr.*, p.*
    FROM spindlereadings sr
    LEFT JOIN predictions p ON sr.id = p.reading_id
    ORDER BY sr.id DESC
    LIMIT ?
  `;

  db.query(query, [limit], (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

router.get("/live", (req, res) => {
  const q = `
    SELECT p.*, sr.*
    FROM predictions p
    JOIN spindlereadings sr ON sr.id = p.reading_id
    ORDER BY p.predicted_at DESC
    LIMIT 1
  `;
  db.query(q, (err, rows) => {
    if (err || !rows.length) return res.json(null);
    res.json(rows[0]);
  });
});

router.post("/predict/:id", (req, res) => {
  const readingId = req.params.id;

  db.query("SELECT * FROM spindlereadings WHERE id = ?", [readingId], (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!results.length) return res.status(404).json({ error: "Reading not found" });

    const pythonScript = path.join(__dirname, "../ml/run_single_inference.py");
    const python = spawn("python", [pythonScript, JSON.stringify(results[0])], {
      cwd: path.join(__dirname, "../ml")
    });

    let output = "";

    python.stdout.on("data", data => output += data.toString());
    python.stderr.on("data", err => console.error(err.toString()));

    python.on("close", () => {
      try {
        const p = JSON.parse(output.trim());

        const insert = `
          INSERT INTO predictions
          (reading_id, health_score, failure_risk, anomaly_score, status, reconstruction_error, predicted_at)
          VALUES (?, ?, ?, ?, ?, ?, NOW())
          ON DUPLICATE KEY UPDATE
            health_score=VALUES(health_score),
            failure_risk=VALUES(failure_risk),
            anomaly_score=VALUES(anomaly_score),
            status=VALUES(status),
            reconstruction_error=VALUES(reconstruction_error),
            predicted_at=NOW()
        `;

        db.query(insert, [
          readingId,
          p.health_score,
          p.failure_risk,
          p.anomaly_score,
          p.status,
          p.reconstruction_error
        ]);

        res.json({ reading_id: readingId, ...p });
      } catch {
        res.status(500).json({ error: "Invalid prediction output" });
      }
    });
  });
});

module.exports = router;


