const express = require("express");
const router = express.Router();
const db = require("../db.js");

// ➤ Fetch all
router.get("/", (req, res) => {
  db.query("SELECT * FROM users", (err, results) => {
    if (err) return res.status(500).send(err);
    res.json(results);
  });
});

// ➤ Add new user
router.post("/add", (req, res) => {
  const { name, email, role } = req.body;

  console.log("📩 Add User Request:", req.body);   // <–– Debug Log

  db.query(
    "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
    [name, email, role],
    (err) => {
      if (err) {
        console.log("❌ DB Insert Error:", err);
        return res.status(500).send(err);
      }
      res.json({ message: "User added successfully" });
    }
  );
});

module.exports = router;



