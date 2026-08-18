import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';
import './index.css';

function App() {
  const [view, setView] = useState('dashboard');
  const navStyle = { padding: '10px 20px', background: '#1e293b', textAlign: 'center' };
  const btnStyle = (active) => ({
    margin: '0 6px',
    padding: '8px 18px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 600,
    background: active ? '#0ea5e9' : '#334155',
    color: 'white',
  });
  return (
    <>
      <nav style={navStyle}>
        <button style={btnStyle(view === 'dashboard')} onClick={() => setView('dashboard')}>
          Dashboard
        </button>
        <button style={btnStyle(view === 'admin')} onClick={() => setView('admin')}>
          Admin Panel
        </button>
      </nav>
      {view === 'admin' ? <AdminPanel /> : <Dashboard />}
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
);