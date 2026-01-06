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
 
// Backend base URL
const API_BASE = "http://localhost:5000";
 
// Refresh every 5 seconds
const REFRESH_INTERVAL = 5000;
 
const Analytics = () => {
  const [rows, setRows] = useState([]);
  const [numericColumns, setNumericColumns] = useState([]);
  const [error, setError] = useState("");
 
  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(timer);
  }, []);
 
  const fetchData = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/data`);
      const data = res.data;
 
      if (!Array.isArray(data) || data.length === 0) return;
 
      setRows(data);
      detectNumericColumns(data);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Failed to fetch analytics data");
    }
  };
 
  const detectNumericColumns = (data) => {
    const sample = data[0];
    const cols = Object.keys(sample).filter(
      (key) =>
        typeof sample[key] === "number" &&
        key !== "id" &&
        key !== "machine_id"
    );
    setNumericColumns(cols);
  };
 
  const calculateStats = (values) => {
    if (!values.length) return { mean: "-", median: "-", mode: "-" };
 
    return {
      mean: stats.mean(values).toFixed(2),
      median: stats.median(values).toFixed(2),
      mode:
        stats.mode(values) !== null
          ? stats.mode(values).toFixed(2)
          : "N/A",
    };
  };
 
  if (error) return <h3 style={{ color: "red" }}>{error}</h3>;
 
  return (
<div style={{ padding: 20 }}>
<h2 style={{ textAlign: "center" }}>📊 Spindle Analytics Dashboard</h2>
 
      {numericColumns.map((col) => {
        const values = rows.map((r) => r[col]).filter(Number.isFinite);
        const s = calculateStats(values);
 
        return (
<div key={col} style={styles.card}>
<h3>{col}</h3>
 
            <div style={styles.statsRow}>
<Stat label="Mean" value={s.mean} />
<Stat label="Median" value={s.median} />
<Stat label="Mode" value={s.mode} />
</div>
 
            <ResponsiveContainer width="100%" height={250}>
<LineChart data={rows}>
<CartesianGrid strokeDasharray="3 3" />
<XAxis dataKey="timestamp" hide />
<YAxis />
<Tooltip />
<Line dataKey={col} stroke="#2563eb" dot={false} />
</LineChart>
</ResponsiveContainer>
</div>
        );
      })}
</div>
  );
};
 
const Stat = ({ label, value }) => (
<div style={styles.statBox}>
<div style={{ fontSize: 12 }}>{label}</div>
<div style={{ fontSize: 18, fontWeight: "bold" }}>{value}</div>
</div>
);
 
const styles = {
  card: {
    background: "#fff",
    marginBottom: 30,
    padding: 20,
    borderRadius: 10,
    boxShadow: "0 4px 10px rgba(0,0,0,.08)",
  },
  statsRow: { display: "flex", gap: 20, marginBottom: 10 },
  statBox: {
    background: "#e5e7eb",
    padding: "10px 16px",
    borderRadius: 8,
    minWidth: 110,
    textAlign: "center",
  },
};
 
export default Analytics;