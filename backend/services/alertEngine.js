const db = require("../db");

const CHECK_INTERVAL_MS = 10_000;
const REQUIRED_COUNT = 1;

console.log("🚨 Alert Engine LOADED");

// --------------------------------------------------
// COMMON ALERT INSERT (NO DUPLICATES)
// --------------------------------------------------
function insertAlert(payload) {
  const {
    alert_type,
    severity,
    title,
    description,
    machine,
    parameter_name,
    parameter_value,
    threshold_value
  } = payload;

  const duplicateQuery = `
    SELECT id FROM alerts
    WHERE alert_type = ? AND acknowledged = 0
    LIMIT 1
  `;

  db.query(duplicateQuery, [alert_type], (err, rows) => {
    if (err) return console.log("❌ Duplicate check error:", err);
    if (rows.length > 0) return;

    const insertQuery = `
      INSERT INTO alerts
      (
        alert_type,
        severity,
        title,
        description,
        machine,
        parameter_name,
        parameter_value,
        threshold_value,
        triggered_at,
        acknowledged
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), 0)
    `;

    db.query(
      insertQuery,
      [
        alert_type,
        severity,
        title,
        description,
        machine,
        parameter_name,
        parameter_value,
        threshold_value
      ],
      (err) => {
        if (err) {
          console.log("❌ Alert insert error:", err);
        } else {
          console.log(`🚨 ALERT STORED → ${title}`);
        }
      }
    );
  });
}

// --------------------------------------------------
// 1️⃣ LOW SPINDLE CURRENT (< 5A)
// --------------------------------------------------
function checkLowSpindleCurrent() {
  const THRESHOLD = 5;

  db.query(
    `
    SELECT GRINDING_SPINDLE_CURRENT
    FROM spindlereadings
    ORDER BY id DESC
    LIMIT ?
    `,
    [REQUIRED_COUNT],
    (err, rows) => {
      if (!rows || rows.length < REQUIRED_COUNT) return;

      if (rows.every(r => r.GRINDING_SPINDLE_CURRENT < THRESHOLD)) {
        insertAlert({
          alert_type: "Spindle Current",
          severity: "Critical",
          title: "Low Spindle Current",
          description: "Spindle current dropped below 5A",
          machine: "SSB1080",
          parameter_name: "GRINDING_SPINDLE_CURRENT",
          parameter_value: rows[0].GRINDING_SPINDLE_CURRENT,
          threshold_value: THRESHOLD
        });
      }
    }
  );
}

// --------------------------------------------------
// 2️⃣ HIGH TEMPERATURE (> 40°C)
// --------------------------------------------------
function checkHighTemperature() {
  const THRESHOLD = 40;

  db.query(
    `
    SELECT GRINDING_SPINDLE_TEMP
    FROM spindlereadings
    ORDER BY id DESC
    LIMIT ?
    `,
    [REQUIRED_COUNT],
    (err, rows) => {
      if (!rows || rows.length < REQUIRED_COUNT) return;

      if (rows.every(r => r.GRINDING_SPINDLE_TEMP > THRESHOLD)) {
        insertAlert({
          alert_type: "Spindle Temperature",
          severity: "Warning",
          title: "High Spindle Temperature",
          description: "Spindle temperature exceeded 40°C",
          machine: "SSB1080",
          parameter_name: "GRINDING_SPINDLE_TEMP",
          parameter_value: rows[0].GRINDING_SPINDLE_TEMP,
          threshold_value: THRESHOLD
        });
      }
    }
  );
}

// --------------------------------------------------
// 3️⃣ LOW MIST PRESSURE (< 2)
// --------------------------------------------------
function checkLowMistPressure() {
  const THRESHOLD = 2;

  db.query(
    `
    SELECT Grinding_spindle_mist_pressure
    FROM spindlereadings
    ORDER BY id DESC
    LIMIT ?
    `,
    [REQUIRED_COUNT],
    (err, rows) => {
      if (!rows || rows.length < REQUIRED_COUNT) return;

      if (rows.every(r => r.Grinding_spindle_mist_pressure < THRESHOLD)) {
        insertAlert({
          alert_type: "Mist Pressure",
          severity: "Critical",
          title: "Low Coolant Pressure",
          description: "Coolant mist pressure below safe limit",
          machine: "SSB1080",
          parameter_name: "Grinding_spindle_mist_pressure",
          parameter_value: rows[0].Grinding_spindle_mist_pressure,
          threshold_value: THRESHOLD
        });
      }
    }
  );
}

// --------------------------------------------------
// 4️⃣ ABNORMAL SPEED (<10000 OR >16000)
// --------------------------------------------------
function checkAbnormalSpeed() {
  const LOW = 10000;
  const HIGH = 16000;

  db.query(
    `
    SELECT SPINDLE_ACTUAL_SPEED
    FROM spindlereadings
    ORDER BY id DESC
    LIMIT ?
    `,
    [REQUIRED_COUNT],
    (err, rows) => {
      if (!rows || rows.length < REQUIRED_COUNT) return;

      const abnormal = rows.every(
        r =>r.SPEED > HIGH
      );

      if (abnormal) {
        insertAlert({
          alert_type: "Spindle Speed",
          severity: "Critical",
          title: "Abnormal Spindle Speed",
          description: "Spindle speed outside 10k–16k RPM range",
          machine: "SSB1080",
          parameter_name: "SPEED",
          parameter_value: rows[0].SPEED,
          threshold_value: `${LOW}-${HIGH}`
        });
      }
    }
  );
}

module.exports = {
  checkLowSpindleCurrent,
  checkHighTemperature,
  checkLowMistPressure,
  checkAbnormalSpeed
};



