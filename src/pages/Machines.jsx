import { useNavigate } from "react-router-dom";
import React, { useState } from "react";
import "./machines.css"; // We will create this CSS file next

export default function Machines() {
  const [activeTab, setActiveTab] = useState("machines");
  const navigate = useNavigate();


  return (
    <div className="machines-page">
      {/* Header */}
      <header className="main-header">
        <div>
          <h2>Machine Management</h2>
          <p>Manage your CNC machines and spindles</p>
        </div>

        <button className="btn-primary">
          <i className="fas fa-plus"></i> Add Spindle
        </button>
      </header>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab-link ${activeTab === "machines" ? "active" : ""}`}
          onClick={() => setActiveTab("machines")}
        >
          Machines
        </button>

        <button
          className={`tab-link ${activeTab === "spindles" ? "active" : ""}`}
          onClick={() => setActiveTab("spindles")}
        >
          Spindles
        </button>
      </div>

      {/* Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Serial No</th>
              <th>Factory Name</th>
              <th>Channel Name</th>
              <th>Machine Name</th>
              <th>Spindle Type</th>   
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>




          <tbody>
            <tr>
             <td>1</td>
             <td>SKF</td>
             <td>Channel4</td>
             <td>SSB1080</td>
             <td>Running</td>
             <td>
               <span className="status healthy">Healthy</span>
             </td>
             <td className="actions">
               <i className="fas fa-pencil-alt"></i>
               <i className="fas fa-trash-alt"></i>
             </td>
           </tr>




           
          </tbody>
        </table>
      </div>
    </div>
  );
}
