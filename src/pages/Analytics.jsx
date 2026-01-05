import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import * as stats from "simple-statistics";

const API_BASE = "https://127.0.0.1:8000"; // backend HTTPS

const REFRESH_INTERVAL = 5000; // 5 sec auto refresh

const Analytics = () => {
  const [rows, setRows] = useState([]);
  const [numericColumns, setNumericColumns] = useState([]);
  const [error, setError] = useState("");

  /* ==============================
     FETCH DATA CONTINUOUSLY
  =============================== */
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const res = await axios.get(`${API_BASE}/data`);
      const data = res.data;

      if (!data || data.length === 0) return;

      setRows(data);
      detectNumericColumns(data);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Failed to fetch analytics data");
    }
  };

  /* ==============================
     AUTO-DETECT NUMERIC COLUMNS
  =============================== */
  const detectNumericColumns = (data) => {
    const sample = data[0];
    const nums = Object.keys(sample).filter(
      (key) =>
        typeof sample[key] === "number" &&
        key !== "id" &&
        key !== "machine_id"
    );
    setNumericColumns(nums);
  };

  /* ==============================
     STATS CALCULATION
  =============================== */
  const getStats = (values) => {
    if (!values.length) return {};
    return {
      mean: stats.mean(values).toFixed(2),
      median: stats.median(values).toFixed(2),
      mode:
        stats.mode(values) !== null
          ? stats.mode(values).toFixed(2)
          : "N/A",
    };
  };

  if (error) {
    return <div style={styles.error}>{error}</div>;
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>📊 Spindle Analytics Dashboard</h2>

      {numericColumns.map((col) => {
        const values = rows
          .map((r) => r[col])
          .filter((v) => typeof v === "number");

        const statistics = getStats(values);

        return (
          <div key={col} style={styles.card}>
            <h3 style={styles.paramTitle}>{col}</h3>

            {/* ===== STATS ===== */}
            <div style={styles.statsRow}>
              <Stat label="Mean" value={statistics.mean} />
              <Stat label="Median" value={statistics.median} />
              <Stat label="Mode" value={statistics.mode} />
            </div>

            {/* ===== CHART ===== */}
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" hide />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey={col}
                  stroke="#2563eb"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
};

/* ==============================
     SMALL COMPONENTS
============================== */
const Stat = ({ label, value }) => (
  <div style={styles.statBox}>
    <div style={styles.statLabel}>{label}</div>
    <div style={styles.statValue}>{value}</div>
  </div>
);

/* ==============================
     STYLES
============================== */
const styles = {
  container: {
    padding: "20px",
    background: "#f8fafc",
  },
  title: {
    textAlign: "center",
    marginBottom: "25px",
  },
  card: {
    background: "#ffffff",
    marginBottom: "30px",
    padding: "20px",
    borderRadius: "10px",
    boxShadow: "0 4px 10px rgba(0,0,0,0.08)",
  },
  paramTitle: {
    marginBottom: "10px",
    color: "#0f172a",
  },
  statsRow: {
    display: "flex",
    gap: "20px",
    marginBottom: "15px",
  },
  statBox: {
    background: "#e5e7eb",
    padding: "10px 16px",
    borderRadius: "8px",
    minWidth: "110px",
    textAlign: "center",
  },
  statLabel: {
    fontSize: "12px",
    color: "#475569",
  },
  statValue: {
    fontSize: "18px",
    fontWeight: "bold",
  },
  error: {
    color: "red",
    textAlign: "center",
    marginTop: "50px",
  },
};

export default Analytics;


