import React, { useEffect, useState, useCallback } from "react";
import "/src/pages/data.css";




const RECORDS_PER_PAGE = 50;
const API_BASE = "http://localhost:5173"; // Added absolute URL to match Analytics.jsx


export default function Data() {
  const [records, setRecords] = useState([]);
  const [columns, setColumns] = useState([]);
  const [machine, setMachine] = useState("SSB1080");
  const [type, setType] = useState("Spindle");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);




  /* ===============================
     LOAD SPINDLE RECORDS
  =============================== */
  // Wrapped in useCallback to prevent unnecessary re-renders in useEffect
  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      //Use absolute URL with API_BASE
      let url = `${API_BASE}/records?machine=${machine}&rtype=${type}`;




      if (fromDate) url += `&from_date=${fromDate}`;
      if (toDate) {
        const nextDay = new Date(toDate);
        nextDay.setDate(nextDay.getDate() + 1);
        url += `&to_date=${nextDay.toISOString().split("T")[0]}`;
      }


      const res = await fetch(url);


      if (!res.ok) {
        throw new Error(`Server error: ${res.status} ${res.statusText}`);
      }




      /*const text = await res.text();
      if (!text) {
        setRecords([]);
        setColumns([]);
        return;
      }*/


      //const data = JSON.parse(text);
     
      const data = await res.json();


      if (!Array.isArray(data)) {
        setError("Invalid response from backend. Expected an Array.");
        return;
      }




      setRecords(data);
      setCurrentPage(1);




      if (data.length > 0) {
        setColumns(Object.keys(data[0]));
      } else {
        setColumns([]);
      }




      //setError("");
    } catch (err) {
      console.error("Load records error:", err);
      setError("Failed to load records: " + err.message);
    } finally {
      setLoading(false);
    }
  }, [machine, type, fromDate, toDate]);




  /* ===============================
     EFFECTS
  =============================== */
  useEffect(() => {
    loadRecords();
  }, [loadRecords]);




  /* ===============================
     PAGINATION
  =============================== */
  const indexOfLastRecord = (currentPage ) * RECORDS_PER_PAGE;
  const indexOfFirstRecord = (currentPage - 1) * RECORDS_PER_PAGE;
 
  const totalPages = Math.ceil(records.length / RECORDS_PER_PAGE);
  const currentRecords = records.slice(
    indexOfFirstRecord,
    indexOfLastRecord
  );


  const paginate = (pageNumber) => {
    if (pageNumber > 0 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };




  /* ===============================
     RENDER
  =============================== */
  return (
    <div className="data-page">
      <h2 className="page-title">Machine Data Records</h2>




      {/* FILTERS */}
      <div className="filters" style={{ textAlign: "center", marginBottom: 20 }}>
        <label>
          Machine:
          <select
            value={machine}
            onChange={(e) => setMachine(e.target.value)}
            style={{ margin: "0 10px" }}
          >
            <option value="SSB1080">SSB1080</option>
            <option value="SSB1081">SSB1081</option>
          </select>
        </label>




        <label>
          Type:
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            style={{ margin: "0 10px" }}
          >
            <option value="Spindle">Spindle</option>
            <option value="Test">Test</option>
          </select>
        </label>




        <label>
          From:
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            style={{ margin: "0 10px" }}
          />
        </label>




        <label>
          To:
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            style={{ margin: "0 10px" }}
          />
        </label>




        <button
          style={{ marginLeft: 20, padding: "6px 12px", cursor: "pointer" }}
          onClick={loadRecords}
        >
          Refresh
        </button>
      </div>


      {loading && <p style={{ textAlign: "center" }}>Loading...</p>}
      {error && <p className="error" style={{ color: "red", textAlign: "center" }}>{error}</p>}




      {/* PAGINATION CONTROLS */}
      {records.length > RECORDS_PER_PAGE && (
        <div style={{ textAlign: "center", marginBottom: 15 }}>
          <button
            onClick={() => paginate(currentPage - 1)}
            disabled={currentPage === 1}
            style={{ padding: "6px 12px", marginRight: 10 }}
          >
            Previous
          </button>
          <span style={{ margin: "0 15px" }}>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => paginate(currentPage + 1)}
            disabled={currentPage === totalPages}
            //style={{ padding: "6px 12px", marginLeft: 10 }}
          >
            Next
          </button>
        </div>
      )}




      {/* TABLE */}
      <div className="table-wrapper" style={{ overflowX: "auto" }}>
        <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#eee" }}>
              {columns.map((col) => (
                <th key={col} style={{ padding: "10px", border: "1px solid #ddd" }}>{col}</th>
              ))}
            </tr>
          </thead>


          <tbody>
              {currentRecords.map((row, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col} style={{ padding: "10px", border: "1px solid #ddd" }}>
                      {col === "timestamp" ? new Date(row[col]).toLocaleString() : row[col]}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

