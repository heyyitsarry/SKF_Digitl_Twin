
import React, { useEffect, useState } from "react";
import "./alerts.css";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/api/alerts")
      .then(res => res.json())
      .then(setAlerts);
  }, []);

  return (
    <div className="alerts-page">
      <h2>Alerts</h2>
      <p>{alerts.length} alerts found</p>

      {alerts.map(alert => (
        <div key={alert.id} className={`alert-card ${alert.severity}`}>
          <div className="alert-content">
            <h4>
              {alert.title}
              <span className={`severity ${alert.severity}`}>
                {alert.severity.toUpperCase()}
              </span>
            </h4>
            <p>{alert.description}</p>
            <small>
              {alert.machine} • {new Date(alert.triggered_at).toLocaleString()}
            </small>
          </div>
        </div>
      ))}

      {alerts.length === 0 && (
        <p style={{ textAlign: "center", marginTop: 20 }}>
          No active alerts 🎉
        </p>
      )}
    </div>
  );
}

