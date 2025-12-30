console.log("🚀 Backend server starting...");

const express = require("express");
const cors = require("cors");
const path = require("path");
const db = require("./db");

const usersRoute = require("./routes/users");
const alertsRoute = require("./routes/alerts");
const predictionsRoute = require("./routes/predictions");
const dataRoute = require("./routes/data");

const {
  checkLowSpindleCurrent,
  checkHighTemperature,
  checkLowMistPressure,
  checkAbnormalSpeed
} = require("./services/alertEngine");
const { startContinuousInference } = require("./services/continuousInference");

const app = express();

app.use(cors());
app.use(express.json());

db.query("SELECT 1", (err) => {
  if (err) console.log("❌ MySQL connection failed:", err);
  else console.log("🟢 MySQL Connected Successfully");
});

app.use("/api/users", usersRoute);
app.use("/api/alerts", alertsRoute);
app.use("/api/predictions", predictionsRoute);
app.use("/api/data", dataRoute);

app.get("/", (req, res) => {
  res.send("Backend Running");
});

console.log("🧠 Alert Engine Scheduler Started");

setInterval(() => {
  checkLowSpindleCurrent();
  checkHighTemperature();
  checkLowMistPressure();
  checkAbnormalSpeed();
}, 10000);

const PORT = 5000;
const HOST = "0.0.0.0";
startContinuousInference(5000);
app.listen(PORT, HOST, () => {
  console.log(`🟢 Server Running on ${HOST}:${PORT}`);
});


