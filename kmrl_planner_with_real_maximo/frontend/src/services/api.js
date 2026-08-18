// services/api.js - shared axios instance + admin endpoints
import axios from 'axios';

// Base URL for the backend API. Set VITE_API_BASE_URL in frontend/.env
// (or the process env) to point at a deployed backend.
export const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_URL });

// Attach the admin API key if the user has stored one (see AdminPanel login)
api.interceptors.request.use((config) => {
  const key = localStorage.getItem('kmrl_api_key');
  if (key) {
    config.headers['X-API-Key'] = key;
  }
  return config;
});

export const adminAPI = {
  // Trainsets (matches routers/admin.py)
  getTrainsets: () => api.get('/admin/trainsets'),
  getTrainset: (code) => api.get(`/admin/trainsets/${code}`),
  updateTrainset: (code, data) => api.put(`/admin/trainsets/${code}`, data),

  // Bays
  getBays: () => api.get('/admin/bays'),
  updateBay: (bayNumber, data) => api.put(`/admin/bays/${bayNumber}`, data),

  // Plan history / detail
  getPlanHistory: () => api.get('/plans/history'),
  getPlan: (id) => api.get(`/plans/${id}`),

  // System actions
  resetBays: () => api.post('/admin/config/reset-bays'),
  resetTeams: () => api.post('/admin/config/reset-teams'),
};

export default api;