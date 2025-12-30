import React, { useEffect, useState } from "react";
import "./users.css";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");

  // Fetch Users
  const fetchUsers = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/users");
      const data = await res.json();
      setUsers(data);
    } catch (e) {
      console.log("❌ Failed to load users:", e);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Add User
  const addUser = async () => {
    if (!name || !email || !role) return alert("⚠ Fill all fields");

    const res = await fetch("http://localhost:5000/api/users/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, role }),
    });

    if (res.ok) {
      alert("✅ User Added");
      setName(""); setEmail(""); setRole("");
      fetchUsers();
    }
  };

  // DELETE USER
  const deleteUser = async (id) => {
    if (!window.confirm("Delete this user?")) return;

    const res = await fetch(`http://localhost:5000/api/users/delete/${id}`, {
      method: "DELETE"
    });

    if (res.ok) {
      alert("🗑 User Deleted");
      fetchUsers();
    }
  };

  // Badge color
  const roleColor = (role) => {
    if (role.toLowerCase() === "admin") return "badge red";
    if (role.toLowerCase() === "tech") return "badge blue";
    return "badge green"; // User
  };

  return (
    <div className="users-page">

      <h2>👥 User Management</h2>
      <p>Manage user access for the spindle monitoring system.</p>

      {/* ADD USER FORM */}
      <div className="add-user-box">
        <input type="text" placeholder="Full Name" value={name} onChange={(e)=>setName(e.target.value)} />
        <input type="email" placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} />
        <input type="text" placeholder="Role (Admin/Tech/User)" value={role} onChange={(e)=>setRole(e.target.value)} />

        <button onClick={addUser}>➕ Add</button>
        <button className="refresh" onClick={fetchUsers}>⟳ Refresh</button>
      </div>

      {/* USER TABLE */}
      <table className="users-table">
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Role</th><th>Action</th>
          </tr>
        </thead>

        <tbody>
          {users.length < 1 ? (
            <tr><td colSpan={4} style={{textAlign:"center"}}>No users found</td></tr>
          ) : (
            users.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td><span className={roleColor(u.role)}>{u.role}</span></td>
                <td>
                  <button className="del-btn" onClick={() => deleteUser(u.id)}>🗑 Delete</button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

    </div>
  );
}


