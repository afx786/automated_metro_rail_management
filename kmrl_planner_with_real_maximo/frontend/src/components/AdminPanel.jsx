// components/AdminPanel.jsx - Using inline styles instead of Tailwind
import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';

const AdminPanel = () => {
  const [trainsets, setTrainsets] = useState([]);
  const [bays, setBays] = useState([]);

  // Container styles
  const containerStyle = {
    padding: '20px',
    fontFamily: 'Arial, sans-serif'
  };

  const sectionStyle = {
    marginBottom: '30px',
    padding: '20px',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px'
  };

  const cardStyle = {
    padding: '15px',
    margin: '10px',
    backgroundColor: 'white',
    borderRadius: '6px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    border: '1px solid #e0e0e0'
  };

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '15px'
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '8px',
    fontWeight: 'bold'
  };

  const inputStyle = {
    marginLeft: '8px',
    padding: '4px',
    border: '1px solid #ccc',
    borderRadius: '4px'
  };

  const buttonStyle = {
    padding: '10px 15px',
    margin: '5px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  };

  useEffect(() => {
    fetchTrainsets();
    fetchBays();
  }, []);

  const fetchTrainsets = async () => {
    try {
      const response = await adminAPI.getTrainsets();
      setTrainsets(response.data);
    } catch (error) {
      console.error('Failed to fetch trainsets:', error);
    }
  };

  const fetchBays = async () => {
    try {
      const response = await adminAPI.getBays();
      setBays(response.data);
    } catch (error) {
      console.error('Failed to fetch bays:', error);
    }
  };

  const updateTrainset = async (code, field, value) => {
    try {
      await adminAPI.updateTrainset(code, { [field]: value });
      fetchTrainsets();
    } catch (error) {
      console.error('Failed to update trainset:', error);
    }
  };

  const updateBay = async (bayNumber, field, value) => {
    try {
      await adminAPI.updateBay(bayNumber, { [field]: value });
      fetchBays();
    } catch (error) {
      console.error('Failed to update bay:', error);
    }
  };

  return (
    <div style={containerStyle}>
      <h2 style={{color: '#333', marginBottom: '20px'}}>🚇 Database Administration</h2>
      
      {/* Trainset Management */}
      <div style={sectionStyle}>
        <h3 style={{color: '#555', marginBottom: '15px'}}>Trainsets ({trainsets.length})</h3>
        <div style={gridStyle}>
          {trainsets.map(trainset => (
            <div key={trainset.code} style={cardStyle}>
              <h4 style={{color: '#333', marginBottom: '12px'}}>{trainset.code}</h4>
              <div>
                <label style={labelStyle}>
                  Fitness Valid:
                  <input
                    type="checkbox"
                    checked={trainset.fitness_valid || false}
                    onChange={(e) => updateTrainset(trainset.code, 'fitness_valid', e.target.checked)}
                    style={inputStyle}
                  />
                </label>
                <label style={labelStyle}>
                  Job Card Open:
                  <input
                    type="checkbox"
                    checked={trainset.job_card_open || false}
                    onChange={(e) => updateTrainset(trainset.code, 'job_card_open', e.target.checked)}
                    style={inputStyle}
                  />
                </label>
                <label style={labelStyle}>
                  Mileage:
                  <input
                    type="number"
                    value={trainset.mileage || 0}
                    onChange={(e) => updateTrainset(trainset.code, 'mileage', parseFloat(e.target.value))}
                    style={inputStyle}
                  />
                </label>
                <label style={labelStyle}>
                  Needs Deep Clean:
                  <input
                    type="checkbox"
                    checked={trainset.needs_deep_clean || false}
                    onChange={(e) => updateTrainset(trainset.code, 'needs_deep_clean', e.target.checked)}
                    style={inputStyle}
                  />
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bay Management */}
      <div style={sectionStyle}>
        <h3 style={{color: '#555', marginBottom: '15px'}}>Cleaning Bays ({bays.length})</h3>
        <div style={gridStyle}>
          {bays.map(bay => (
            <div key={bay.bay_number} style={cardStyle}>
              <h4 style={{color: '#333', marginBottom: '12px'}}>{bay.bay_number}</h4>
              <div>
                <label style={labelStyle}>
                  Occupied:
                  <input
                    type="checkbox"
                    checked={bay.is_occupied || false}
                    onChange={(e) => updateBay(bay.bay_number, 'is_occupied', e.target.checked)}
                    style={inputStyle}
                  />
                </label>
                <label style={labelStyle}>
                  Current Trainset:
                  <input
                    type="text"
                    value={bay.current_trainset || ''}
                    onChange={(e) => updateBay(bay.bay_number, 'current_trainset', e.target.value)}
                    placeholder="KM01"
                    style={inputStyle}
                  />
                </label>
                <label style={labelStyle}>
                  Available Manpower:
                  <input
                    type="number"
                    value={bay.available_manpower || 0}
                    onChange={(e) => updateBay(bay.bay_number, 'available_manpower', parseInt(e.target.value))}
                    style={inputStyle}
                  />
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Actions */}
      <div style={sectionStyle}>
        <h3 style={{color: '#555', marginBottom: '15px'}}>System Actions</h3>
        <div>
          <button onClick={() => adminAPI.resetBays()} style={buttonStyle}>
            🔄 Reset All Bays
          </button>
          <button onClick={() => adminAPI.resetTeams()} style={buttonStyle}>
            🔄 Reset All Teams
          </button>
          <button onClick={fetchTrainsets} style={buttonStyle}>
            📊 Refresh Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;