// backend/routes/data.js
const express = require("express");
const router = express.Router();
const db = require("../db.js");

/* =====================================================
   EXISTING ROUTES (UNCHANGED)
===================================================== */

// ➤ Fetch first 500 spindle readings
router.get("/", (req, res) => {
  const query = `
    SELECT * FROM spindlereadings
    ORDER BY id ASC
    LIMIT 500
  `;

  db.query(query, (err, results) => {
    if (err) {
      console.log("❌ Error fetching spindlereadings:", err);
      return res.status(500).send(err);
    }
    res.json(results);
  });
});

// ➤ Add new spindle reading
router.post("/add", (req, res) => {
  const { spindleId, status, load, temperature, timestamp } = req.body;

  const query = `
    INSERT INTO spindlereadings (spindleId, status, load, temperature, timestamp)
    VALUES (?, ?, ?, ?, ?)
  `;

  db.query(
    query,
    [spindleId, status, load, temperature, timestamp],
    (err) => {
      if (err) {
        console.log("❌ Insert Error:", err);
        return res.status(500).send(err);
      }
      res.json({ message: "Reading added successfully" });
    }
  );
});

// ➤ Delete zero spindle readings
router.delete("/delete-zero", (req, res) => {
  const query = `
    DELETE FROM spindlereadings
    WHERE Grinding_spindle_mist_pressure = 0
      AND Grinding_Spindle_Temp = 0
      AND Grinding_spindle_Current = 0
      AND speed = 0
  `;

  db.query(query, (err, results) => {
    if (err) {
      console.log("❌ Delete Error:", err);
      return res.status(500).send(err);
    }
    res.json({
      message: `Deleted ${results.affectedRows} records successfully`,
    });
  });
});

/* =====================================================
   🆕 NEW ROUTE: FETCH LATEST ML PREDICTION
===================================================== */

// ➤ Fetch latest ML prediction for a machine
router.get("/predictions/latest", (req, res) => {
  const { machine_id } = req.query;

  if (!machine_id) {
    return res.status(400).json({
      error: "machine_id query parameter is required",
    });
  }

  const query = `
    SELECT *
    FROM spindle_predictions
    WHERE machine_id = ?
    ORDER BY timestamp DESC
    LIMIT 1
  `;

  db.query(query, [machine_id], (err, results) => {
    if (err) {
      console.log("❌ Error fetching spindle prediction:", err);
      return res.status(500).send(err);
    }

    if (results.length === 0) {
      return res.json({
        message: "No prediction available yet",
        health_score: null,
        failure_risk: null,
        status: "UNKNOWN",
      });
    }

    res.json(results[0]);
  });
});

module.exports = router;


