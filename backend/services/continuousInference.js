console.log("📦 continuousInference.js loaded");
const db = require("../db");
const { spawn } = require("child_process");
const path = require("path");

let lastProcessedId = null;

function startContinuousInference(intervalMs = 5000) {
  console.log("🧠 Continuous Inference Engine Started");

  setInterval(() => {
    const q = `
      SELECT * FROM spindlereadings
      ORDER BY id DESC
      LIMIT 1
    `;

    db.query(q, (err, rows) => {
      if (err || !rows.length) return;

      const reading = rows[0];

      if (reading.id === lastProcessedId) return;
      lastProcessedId = reading.id;

      const script = path.join(__dirname, "../ml/run_single_inference.py");

      const py = spawn("python", [script, JSON.stringify(reading)], {
        cwd: path.join(__dirname, "../ml")
      });

      let output = "";

      py.stdout.on("data", d => output += d.toString());
      py.stderr.on("data", d => console.error("❌ Python:", d.toString()));

      py.on("close", () => {
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
            reading.id,
            p.health_score,
            p.failure_risk,
            p.anomaly_score,
            p.status,
            p.reconstruction_error
          ]);

          console.log(`🧬 Auto-predicted reading ${reading.id} → ${p.status}`);
        } catch (e) {
          console.error("❌ Inference parse error:", output);
        }
      });
    });
  }, intervalMs);
}

module.exports = { startContinuousInference };
console.log("📦 exports:", module. Exports);


