import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import axios from "axios";

const BACKEND_URL = "http://10.179.2.149:8000"; // same as Data tab

export default function Analytics() {
  const [data, setData] = useState([]);
  const [parameter, setParameter] = useState("01_HE4_DE");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  useEffect(() => {
    fetchData();
  }, [parameter, fromDate, toDate]);

  const fetchData = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/records`, {
        params: {
          machine: "SSB1080",
          rtype: "Spindle",
          from_date: fromDate || undefined,
          to_date: toDate || undefined,
          limit: 500
        }
      });
      setData(res.data.reverse()); // time order
    } catch (err) {
      console.error("Analytics fetch failed", err);
    }
  };

  const timestamps = data.map(d => d.timestamp);
  const values = data.map(d => d[parameter]);

  return (
    <div style={{ padding: "20px" }}>
      <h2>Spindle Analytics</h2>

      {/* Controls */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
        <select value={parameter} onChange={e => setParameter(e.target.value)}>
          <option value="01_HE4_DE">01_HE4_DE</option>
          <option value="01_HV_DE">01_HV_DE</option>
          <option value="01_HA_DE">01_HA_DE</option>
          <option value="02_HE4_NDE">02_HE4_NDE</option>
        </select>

        <input type="date" onChange={e => setFromDate(e.target.value)} />
        <input type="date" onChange={e => setToDate(e.target.value)} />
      </div>

      {/* Graph */}
      <Plot
        data={[
          {
            x: timestamps,
            y: values,
            type: "scatter",
            mode: "lines+markers",
            marker: { color: "blue" },
            name: parameter
          }
        ]}
        layout={{
          title: `${parameter} Trend`,
          xaxis: { title: "Time" },
          yaxis: { title: parameter },
          height: 500
        }}
        style={{ width: "100%" }}
      />
    </div>
  );
}


