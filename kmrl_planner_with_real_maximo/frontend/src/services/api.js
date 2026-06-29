// services/api.js - Add admin endpoints
export const adminAPI = {
  // Trainsets
  getTrainsets: () => api.get('/admin/trainsets'),
  getTrainset: (code) => api.get(`/admin/trainsets/${code}`),
  createTrainset: (data) => api.post('/admin/trainsets', data),
  updateTrainset: (code, data) => api.put(`/admin/trainsets/${code}`, data),
  deleteTrainset: (code) => api.delete(`/admin/trainsets/${code}`),
  
  // Bays
  getBays: () => api.get('/admin/bays'),
  createBay: (data) => api.post('/admin/bays', data),
  updateBay: (bayNumber, data) => api.put(`/admin/bays/${bayNumber}`, data),
  
  // System actions
  resetBays: () => api.post('/admin/config/reset-bays'),
  resetTeams: () => api.post('/admin/config/reset-teams'),
  updatePlanParams: (params) => api.post('/admin/config/plan-params', params),
  
  // Plans
  getRecentPlans: (limit = 10) => api.get(`/admin/plans/recent?limit=${limit}`),
  deletePlan: (planId) => api.delete(`/admin/plans/${planId}`)
};