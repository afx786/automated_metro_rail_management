// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';
import ConnectionTest from './components/ConnectionTest';

function App() {
  return (
    <Router>
      <div style={{ padding: '20px', fontFamily: 'Arial' }}>
        {/* Navigation */}
        <nav style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f5f5f5' }}>
          <Link to="/" style={{ marginRight: '15px', textDecoration: 'none', color: '#007bff' }}>
            🏠 Dashboard
          </Link>
          <Link to="/admin" style={{ marginRight: '15px', textDecoration: 'none', color: '#007bff' }}>
            ⚙️ Admin Panel
          </Link>
          <Link to="/test" style={{ textDecoration: 'none', color: '#007bff' }}>
            🔌 Connection Test
          </Link>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/test" element={<ConnectionTest />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;