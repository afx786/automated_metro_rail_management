// components/AdminPanel.jsx - Using inline styles instead of Tailwind
import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';

const AdminPanel = () => {
  const [trainsets, setTrainsets] = useState([]);
  const [bays, setBays] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [apiKey, setApiKey] = useState(localStorage.getItem('kmrl_api_key') || '');
  const [authError, setAuthError] = useState('');

  const saveApiKey = () => {
    localStorage.setItem('kmrl_api_key', apiKey);
    setAuthError('');
    fetchTrainsets();
    fetchBays();
  };

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
    fetchHistory();
  }, []);

  const handleError = (error) => {
    if (error.response && error.response.status === 401) {
      setAuthError('Invalid API key. Check the key and try again.');
    } else {
      console.error('API request failed:', error);
    }
  };

  const fetchTrainsets = async () => {
    try {
      const response = await adminAPI.getTrainsets();
      setTrainsets(response.data);
    } catch (error) {
      handleError(error);
    }
  };

  const fetchBays = async () => {
    try {
      const response = await adminAPI.getBays();
      setBays(response.data);
    } catch (error) {
      handleError(error);
    }
  };

  const updateTrainset = async (code, field, value) => {
    try {
      await adminAPI.updateTrainset(code, { [field]: value });
      fetchTrainsets();
    } catch (error) {
      handleError(error);
    }
  };

  const updateBay = async (bayNumber, field, value) => {
    try {
      await adminAPI.updateBay(bayNumber, { [field]: value });
      fetchBays();
    } catch (error) {
      handleError(error);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await adminAPI.getPlanHistory();
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to load plan history:', error);
    }
  };

  const viewPlan = async (id) => {
    try {
      const { data } = await adminAPI.getPlan(id);
      setSelectedPlan(data);
    } catch (error) {
      console.error('Failed to load plan:', error);
      setSelectedPlan(null);
    }
  };

  return (
    <div style={containerStyle}>
      <h2 style={{color: '#333', marginBottom: '20px'}}>🚇 Database Administration</h2>

      {/* API key input */}
      <div style={sectionStyle}>
        <h3 style={{color: '#555', marginBottom: '10px'}}>Admin API Key</h3>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          style={{...inputStyle, marginLeft: '0px', minWidth: '260px'}}
          placeholder="Enter admin API key"
        />
        <button onClick={saveApiKey} style={buttonStyle}>
          Save Key
        </button>
        {authError && <p style={{color: '#d33', marginTop: '8px'}}>{authError}</p>}
      </div>
      
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

      {/* Plan History */}
      <div style={sectionStyle}>
        <h3 style={{color: '#555', marginBottom: '15px'}}>Plan History ({history.length})</h3>
        <button onClick={fetchHistory} style={buttonStyle}>
          🔄 Refresh
        </button>
        {history.length === 0 && (
          <p style={{color: '#888', marginTop: '10px'}}>
            No plans generated yet. Run the optimizer from the Dashboard first.
          </p>
        )}
        <div style={{marginTop: '10px'}}>
          {history.map(h => (
            <div key={h.id} style={{...cardStyle, display: 'flex', alignItems: 'center', flexWrap: 'wrap'}}>
              <button onClick={() => viewPlan(h.id)} style={{...buttonStyle, backgroundColor: '#6c757d', margin: '0'}}>
                View Plan #{h.id}
              </button>
              <span style={{marginLeft: '12px', color: '#555'}}>
                {new Date(h.created_at).toLocaleString()} — service {h.counts.service}, standby {h.counts.standby}, maintenance {h.counts.maintenance}
              </span>
            </div>
          ))}
        </div>

        {selectedPlan && (
          <div style={{marginTop: '15px', padding: '15px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e0e0e0'}}>
            <h4 style={{color: '#333', marginBottom: '8px'}}>Plan generated at {new Date(selectedPlan.generated_at).toLocaleString()}</h4>
            {[{key: 'service', label: 'Service'}, {key: 'standby', label: 'Standby'}, {key: 'maintenance', label: 'Maintenance'}].map(({key, label}) => (
              <div key={key} style={{marginBottom: '10px'}}>
                <strong>{label} ({(selectedPlan[key] || []).length})</strong>
                <div>
                  {(selectedPlan[key] || []).map(item => (
                    <div key={item.trainset} style={{fontSize: '13px', color: '#555'}}>
                      {item.trainset} — {item.reason || item.status}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
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