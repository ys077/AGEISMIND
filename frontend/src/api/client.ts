import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Complaints
export const getComplaints = async (page: number = 1, pageSize: number = 50) => {
  const response = await apiClient.get(`/api/complaints?page=${page}&page_size=${pageSize}`);
  return response.data;
};

export const getComplaint = async (complaintId: string) => {
  const response = await apiClient.get(`/api/complaints/${complaintId}`);
  return response.data;
};

export const getComplaintTransactions = async (complaintId: string) => {
  const response = await apiClient.get(`/api/complaints/${complaintId}/transactions`);
  return response.data;
};

// Modules 5, 6, 7 (Analysis)
export const getMoneyFlow = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}/money-flow`);
  return response.data;
};

export const getNetworkAnalysis = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}/network`);
  return response.data;
};

export const getTimeGeography = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}/time-geography`);
  return response.data;
};

// Module 8 (Predictions)
export const getStoredPrediction = async (complaintId: string) => {
  const response = await apiClient.get(`/api/predictions/${complaintId}`);
  return response.data;
};

// Module 9 (Explainability)
export const getCandidateExplanation = async (complaintId: string, locationId: string) => {
  const response = await apiClient.get(`/api/explanations/${complaintId}/candidates/${locationId}`);
  return response.data;
};

// Module 10 (Heatmap)
export const getHeatmapData = async (complaintId: string) => {
  const response = await apiClient.get(`/api/risk-heatmap/${complaintId}`);
  return response.data;
};

// Module 11 (Alerts & Audit)
export const getAlertSummary = async () => {
  const response = await apiClient.get('/api/investigator/alerts/summary');
  return response.data;
};

export const getAlerts = async (params: any = {}) => {
  const response = await apiClient.get('/api/alerts', { params });
  return response.data;
};

export const getAlertDetail = async (alertId: string) => {
  const response = await apiClient.get(`/api/alerts/${alertId}`);
  return response.data;
};

export const updateAlertStatus = async (alertId: string, status: string) => {
  const response = await apiClient.patch(`/api/alerts/${alertId}/status`, { status });
  return response.data;
};

export const addInvestigatorAction = async (alertId: string, actionData: { action_type: string, notes?: string }) => {
  const response = await apiClient.post(`/api/alerts/${alertId}/actions`, actionData);
  return response.data;
};

// Executive Dashboard
export const getDashboardOverview = async () => {
  const response = await apiClient.get('/api/dashboard/overview');
  return response.data;
};
