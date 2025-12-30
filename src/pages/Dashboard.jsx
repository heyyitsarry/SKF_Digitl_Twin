import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import SpindleView from "../components/SpindleView";

const stats = [
  {
    title: "Total Machines",
    value: 1,
    color: "blue",
    icon: "https://img.icons8.com/ios-filled/24/007bff/speedometer.png",
  },
  {
    title: "Active Machines",
    value: 1,
    color: "green",
    change: "+8% from last period",
    icon: "https://img.icons8.com/ios-filled/24/00c853/activity.png",
  },
  {
    title: "Machines with Alerts",
    value: 1,
    color: "yellow",
    change: "-5% from last period",
    icon: "https://img.icons8.com/ios-filled/24/ffa000/appointment-reminders.png",
  },
  {
    title: "Critical Status",
    value: 1,
    color: "red",
    icon: "https://img.icons8.com/ios-filled/24/f44336/pulse.png",
  },
];

const machines = [
  { id: "M-001", name: "Spindle A", status: "active" },
  { id: "M-002", name: "Spindle B", status: "alert" },
  { id: "M-003", name: "Spindle C", status: "active" },
  { id: "M-004", name: "Spindle D", status: "critical" },
];

export default function Dashboard() {
  const [view, setView] = useState("3d");

  return (
    <div className="dashboard">
      <h1 className="page-title">SpindleTwin Dashboard</h1>

      {/* Stats Section */}
      <div className="stats-grid">
        {stats.map((s) => (
          <div key={s.title} className={`stat-card ${s.color}`}>
            <div className="stat-header">
              <span>{s.title}</span>
              <img src={s.icon} alt="icon" />
            </div>
            <h2 className="stat-value">{s.value}</h2>
            {s.change && (
              <p
                className={`stat-change ${
                  s.change.includes("+") ? "positive" : "negative"
                }`}
              >
                {s.change}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Spindle Section */}
      <div className="card spindle-section">
        <div className="spindle-header">
          <h2>Spindle Visualization</h2>
          <div className="health-badge">93% Health</div>
        </div>

        <div className="view-buttons">
          <button
            onClick={() => setView("2d")}
            className={view === "2d" ? "active-btn" : ""}
          >
            2D View
          </button>
          <button
            onClick={() => setView("3d")}
            className={view === "3d" ? "active-btn" : ""}
          >
            3D View
          </button>
          <button
            onClick={() => setView("map")}
            className={view === "map" ? "active-btn" : ""}
          >
            Sensor Map
          </button>
        </div>

        <div className="spindle-view">
          {view === "3d" ? (
            <SpindleView />
          ) : (
            <div className="placeholder">
              {view === "2d"
                ? "2D View Placeholder"
                : "Sensor Map Placeholder"}
            </div>
          )}
        </div>
      </div>

      {/* Machines and Alerts */}
      <div className="machine-alert-grid">
        <div className="card">
          <h3>Machines</h3>
          <ul className="machine-list">
            {machines.map((m) => (
              <li key={m.id}>
                <span>{m.name}</span>
                <span className={`status ${m.status}`}>{m.status}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h3>Alerts</h3>
          <ul className="alert-list">
            <li>Spindle D: Critical vibration level</li>
            <li>Spindle B: Temperature rising</li>
            <li>Spindle A: Minor imbalance detected</li>
          </ul>
        </div>
      </div>

      {/* ✅ THIS IS THE ONLY ADDITION */}
      <Outlet />
    </div>
  );
}


