import React, { useEffect, useState } from "react";
import "/src/pages/data.css";

const RECORDS_PER_PAGE = 50;

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
  const loadRecords = async () => {
    setLoading(true);
    setError("");
    try {
      let url = `/records?machine=${machine}&rtype=${type}`;

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

      const text = await res.text();
      if (!text) {
        setRecords([]);
        setColumns([]);
        return;
      }

      const data = JSON.parse(text);

      if (!Array.isArray(data)) {
        setError("Invalid response from backend.");
        return;
      }

      setRecords(data);
      setCurrentPage(1);

      if (data.length > 0) {
        setColumns(Object.keys(data[0]));
      } else {
        setColumns([]);
      }

      setError("");
    } catch (err) {
      console.error("Load records error:", err);
      setError("Failed to load records: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  /* ===============================
     EFFECTS
  =============================== */
  useEffect(() => {
    loadRecords();
  }, [machine, type, fromDate, toDate]);

  /* ===============================
     PAGINATION
  =============================== */
  const indexOfLastRecord = currentPage * RECORDS_PER_PAGE;
  const indexOfFirstRecord = indexOfLastRecord - RECORDS_PER_PAGE;
  const currentRecords = records.slice(
    indexOfFirstRecord,
    indexOfLastRecord
  );

  const totalPages = Math.ceil(records.length / RECORDS_PER_PAGE);

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
            style={{ marginLeft: 8, marginRight: 20 }}
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
            style={{ marginLeft: 8, marginRight: 20 }}
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
            style={{ marginLeft: 8, marginRight: 20 }}
          />
        </label>

        <label>
          To:
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            style={{ marginLeft: 8 }}
          />
        </label>

        <button
          style={{ marginLeft: 20, padding: "6px 12px", cursor: "pointer" }}
          onClick={loadRecords}
        >
          Refresh
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

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
          <span>
            Page {currentPage} of {totalPages} ({records.length} total records)
          </span>
          <button
            onClick={() => paginate(currentPage + 1)}
            disabled={currentPage === totalPages}
            style={{ padding: "6px 12px", marginLeft: 10 }}
          >
            Next
          </button>
        </div>
      )}

      {/* TABLE */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) =>
                col === "timestamp" ? (
                  <React.Fragment key={col}>
                    <th>Date</th>
                    <th>Time</th>
                  </React.Fragment>
                ) : (
                  <th key={col}>{col}</th>
                )
              )}
            </tr>
          </thead>

          <tbody>
            {currentRecords.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} style={{ textAlign: "center" }}>
                  {records.length === 0
                    ? "No records found"
                    : "No records for this page"}
                </td>
              </tr>
            ) : (
              currentRecords.map((row, i) => (
                <tr key={indexOfFirstRecord + i}>
                  {columns.map((col) =>
                    col === "timestamp" ? (
                      <React.Fragment key={col}>
                        <td>
                          {new Date(row[col]).toLocaleDateString()}
                        </td>
                        <td>
                          {new Date(row[col]).toLocaleTimeString()}
                        </td>
                      </React.Fragment>
                    ) : (
                      <td key={col}>{row[col]}</td>
                    )
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


