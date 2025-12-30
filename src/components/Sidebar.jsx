import React from "react";
import { NavLink } from "react-router-dom";

export default function Sidebar() {
  const nav = [
    { name: "Dashboard", to: "/" },
    { name: "Machines", to: "/machines" },
    { name: "Predictions", to: "/predictions" },
    { name: "Analytics", to: "/analytics" },
    { name: "Alerts", to: "/alerts" },
    { name: "Data", to: "/data" },
    { name: "Users", to: "/users" },
    { name: "Settings", to: "/settings" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">SpindleTwin</div>
      <nav className="sidebar-nav">
        {nav.map((n) => (
          <NavLink
            key={n.name}
            to={n.to}
            className={({ isActive }) =>
              `nav-item ${isActive ? "active" : ""}`
            }
          >
            {n.name}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="profile-pic">MK</div>
        <div>
          <div className="profile-name">Mukul</div>
          <div className="profile-role">Maintenance Manager</div>
        </div>
      </div>
    </aside>
  );
}
