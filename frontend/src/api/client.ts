import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Typed Interfaces
export interface Complaint {
  complaint_id: string;
  crime_category: string;
  fraud_type: string;
  fraud_amount: number;
  report_date?: string;
  complaint_date?: string;
  complaint_time?: string;
  victim_city?: string;
  district_id?: string;
  source_channel?: string;
  status?: string;
  description?: string;
  victim_latitude?: number;
  victim_longitude?: number;
}

export interface Transaction {
  transaction_id: string;
  complaint_id: string;
  sender_account: string;
  receiver_account: string;
  amount: number;
  timestamp?: string;
  transaction_time?: string;
  transaction_type?: string;
  status?: string;
}

export interface Account {
  account_id: string;
  account_type: string;
  district_id?: string;
  latitude?: number;
  longitude?: number;
}

export interface WithdrawalCandidate {
  prediction_id?: string;
  withdrawal_location_id: string;
  location_id?: string;
  latitude: number;
  longitude: number;
  district: string;
  probability: number;
  priority: string;
  rank: number;
  model_version?: string;
  location_name?: string;
  source?: string;
  source_id?: string;
  operator?: string;
  brand?: string;
  address?: string;
  factors?: any[];
}

export interface PredictionResponse {
  complaint_id: string;
  model_version: string;
  prediction_timestamp: string;
  candidate_count: number;
  ranked_candidates: WithdrawalCandidate[];
}

export interface HeatmapResponse {
  complaint_id: string;
  candidates: WithdrawalCandidate[];
}

export interface GlobalHeatmapCandidate {
  location_id: string;
  latitude: number;
  longitude: number;
  district: string;
  complaint_count: number;
  prediction_count: number;
  average_probability: number;
  maximum_probability: number;
  risk_level: string;
}

export interface GlobalHeatmapResponse {
  map_type: string;
  candidates: GlobalHeatmapCandidate[];
}

export interface Alert {
  alert_id: string;
  prediction_id: string;
  complaint_id: string;
  location_id: string;
  district: string;
  probability: number;
  priority: string;
  status: string;
  created_at: string;
}

export interface AuditRecord {
  audit_id: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  actor_id?: string;
  complaint_id?: string;
  data_hash?: string;
  timestamp?: string;
  created_at?: string;
}

// Complaints APIs
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

export const getComplaintAccounts = async (complaintId: string) => {
  const response = await apiClient.get(`/api/complaints/${complaintId}/accounts`);
  return response.data;
};

export const getComplaintRelationships = async (complaintId: string) => {
  const response = await apiClient.get(`/api/complaints/${complaintId}/relationships`);
  return response.data;
};

export const getComplaintNetwork = async (complaintId: string) => {
  const response = await apiClient.get(`/api/complaints/${complaintId}/network`);
  return response.data;
};

// Analysis APIs
export const getCaseAnalysis = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}`);
  return response.data;
};

export const getMoneyFlow = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}/money-flow`);
  return response.data;
};

export const getNetworkAnalysis = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}/network-analysis`);
  return response.data;
};

export const getTimeGeography = async (complaintId: string) => {
  const response = await apiClient.get(`/api/analysis/${complaintId}/time-geography`);
  return response.data;
};

// Prediction APIs
export const getStoredPrediction = async (complaintId: string) => {
  const response = await apiClient.get(`/api/predictions/${complaintId}`);
  return response.data;
};

export const generatePrediction = async (complaintId: string) => {
  const response = await apiClient.post(`/api/predictions/${complaintId}`);
  return response.data;
};

export const runPredictionJob = async (complaintId: string) => {
  const response = await apiClient.post(`/api/predictions/${complaintId}/run`);
  return response.data;
};

export const getPredictionJobStatus = async (jobId: string) => {
  const response = await apiClient.get(`/api/predictions/jobs/${jobId}/status`);
  return response.data;
};

export const getModelInfo = async () => {
  const response = await apiClient.get('/api/ml/model-info');
  return response.data;
};

// Explainability APIs
export const getCandidateExplanation = async (complaintId: string, locationId: string) => {
  const response = await apiClient.get(`/api/explanations/${complaintId}/candidates/${locationId}`);
  return response.data;
};

// Risk Heatmap APIs
export const getHeatmapData = async (complaintId: string) => {
  const response = await apiClient.get(`/api/risk-heatmap/${complaintId}`);
  return response.data;
};

export const getGlobalHeatmapData = async () => {
  const response = await apiClient.get(`/api/risk-heatmap/global`);
  return response.data;
};

export const getHeatmapDistricts = async (complaintId: string) => {
  const response = await apiClient.get(`/api/risk-heatmap/${complaintId}/districts`);
  return response.data;
};

// Alerts & Audit APIs
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

export const getAuditTrail = async (): Promise<AuditRecord[]> => {
  const response = await apiClient.get('/api/audit');
  return response.data;
};

// Executive Dashboard
export const getDashboardOverview = async () => {
  const response = await apiClient.get('/api/dashboard/overview');
  return response.data;
};
