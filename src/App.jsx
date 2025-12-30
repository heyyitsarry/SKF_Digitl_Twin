import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import AnalyticsPage from "./pages/Analytics";

// Pages
import Dashboard from "./pages/Dashboard";
import Machines from "./pages/Machines";
import Alerts from "./pages/Alerts";
import Predictions from "./pages/Predictions";
import DataPage from "./pages/Data";
import Users from "./pages/Users";
export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Sidebar />

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/data" element={<DataPage />} />
            <Route path="/machines" element={<Machines />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/users" element={<Users />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}


