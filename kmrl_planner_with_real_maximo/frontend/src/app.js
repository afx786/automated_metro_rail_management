// src/App.js
import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');

  // Listen for hash changes
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      setCurrentView(hash || 'dashboard');
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange(); // Initial check

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const switchView = (view) => {
    window.location.hash = view;
    setCurrentView(view);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      {/* Simple navigation */}
      <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f5f5f5' }}>
        <button 
          onClick={() => switchView('dashboard')}
          style={{ 
            marginRight: '10px', 
            padding: '8px 16px',
            backgroundColor: currentView === 'dashboard' ? '#007bff' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          🏠 Dashboard
        </button>
        <button 
          onClick={() => switchView('admin')}
          style={{ 
            padding: '8px 16px',
            backgroundColor: currentView === 'admin' ? '#007bff' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          ⚙️ Admin Panel
        </button>
      </div>

      {/* Render current view */}
      {currentView === 'dashboard' && <Dashboard />}
      {currentView === 'admin' && <AdminPanel />}
    </div>
  );
}

export default App;