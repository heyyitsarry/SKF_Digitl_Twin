import React, { useState, useEffect } from "react";
import "./predictions.css";

export default function Predictions() {
  const [activeTab, setActiveTab] = useState("prediction");
  const [showResults, setShowResults] = useState(false);
  const [livePrediction, setLivePrediction] = useState(null);

  useEffect(() => {
    if (!showResults) return;

    const fetchLive = async () => {
      const res = await fetch("http://localhost:5000/api/predictions/live");
      const data = await res.json();
      setLivePrediction(data);
    };

    fetchLive();
    const t = setInterval(fetchLive, 5000);
    return () => clearInterval(t);
  }, [showResults]);

  return (
    <div className="predictions-page">
      <header className="main-header">
        <h2>Predictive Maintenance</h2>
        <p>ML-based failure prediction and root cause analysis for your machines.</p>
      </header>

      <div className="tabs">
        <button className={`tab-link ${activeTab === "prediction" ? "active" : ""}`}
          onClick={() => setActiveTab("prediction")}>Prediction</button>
        <button className={`tab-link ${activeTab === "analysis" ? "active" : ""}`}
          onClick={() => setActiveTab("analysis")}>Analysis</button>
        <button className={`tab-link ${activeTab === "advanced" ? "active" : ""}`}
          onClick={() => setActiveTab("advanced")}>Advanced ML</button>
      </div>

      {!showResults && (
        <div id="analysis-setup-content">
          <button className="btn-primary" onClick={() => setShowResults(true)}>
            Run Analysis
          </button>
        </div>
      )}

      {showResults && (
        <div id="analysis-results-content">
          <div className="health-index-header">
            <h4>Machine Health Index</h4>
            <span className="health-score">
              {livePrediction ? Math.round(livePrediction.health_score) : "--"} <small>/100</small>
            </span>
          </div>

          <p className="prediction-probability">
            {livePrediction ? Math.round(livePrediction.failure_risk * 100) : "--"}%
          </p>

          <span className={`status-tag ${livePrediction?.status?.toLowerCase()}`}>
            {livePrediction?.status || "Waiting..."}
          </span>
        </div>
      )}
    </div>
  );
}


