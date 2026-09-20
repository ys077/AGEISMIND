import { create } from 'zustand';
import { 
  getDashboardOverview, 
  getModelInfo, 
  getComplaints, 
  getAlerts,
  getGlobalHeatmapData
} from '../api/client';
import { apiClient } from '../api/client';

export interface AppState {
  dashboardData: any;
  modelInfo: any;
  complaintsList: any;
  alertsList: any;
  globalHeatmap: any;
  casesCache: Record<string, any>; // Cache for complete case data
  
  isPreloading: boolean;
  preloadError: string | null;
  
  preloadApp: (forceRefresh?: boolean) => Promise<void>;
  fetchCaseComplete: (complaintId: string) => Promise<any>;
  fetchGlobalHeatmap: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  dashboardData: null,
  modelInfo: null,
  complaintsList: null,
  alertsList: null,
  globalHeatmap: null,
  casesCache: {},
  
  isPreloading: true,
  preloadError: null,

  preloadApp: async (forceRefresh?: boolean) => {
    const currentData = get().dashboardData;
    if (!forceRefresh && currentData) return;
    
    const isInitial = !currentData;
    if (isInitial) {
      set({ isPreloading: true, preloadError: null });
    }
    
    try {
      // Safety timeout to guarantee UI unblocks even if network hangs
      const timeoutGuard = new Promise(resolve => setTimeout(resolve, 4000));
      
      const [dashboardData, modelInfo] = await Promise.race([
        Promise.all([
          getDashboardOverview().catch(() => null),
          getModelInfo().catch(() => null)
        ]),
        timeoutGuard.then(() => [null, null])
      ]) as [any, any];

      // Unblock the UI immediately after critical data is loaded or timeout reached
      set(state => ({
        dashboardData: dashboardData || state.dashboardData,
        modelInfo: modelInfo || state.modelInfo,
        isPreloading: false
      }));

      // 2. Fetch heavier data sets in the background
      // 2. Fetch heavier data sets in the background independently to prevent blocking
      getComplaints(1, 100)
        .then(data => data && set(state => ({ ...state, complaintsList: data })))
        .catch(console.error);

      getAlerts()
        .then(data => data && set(state => ({ ...state, alertsList: data })))
        .catch(console.error);

      getGlobalHeatmapData()
        .then(data => data && set(state => ({ ...state, globalHeatmap: data })))
        .catch(console.error);

    } catch (err) {
      console.error("Preload error:", err);
      set({ preloadError: "Failed to load application data", isPreloading: false });
    }
  },

  fetchCaseComplete: async (complaintId: string) => {
    const { casesCache } = get();
    if (casesCache[complaintId]) {
      return casesCache[complaintId];
    }
    
    try {
      const response = await apiClient.get(`/api/cases/${complaintId}/complete`);
      const caseData = response.data;
      
      // Additional data that might not be in the complete endpoint but is needed for tabs
      // For instance, the prediction result and SHAP explanation
      const basicCaseData = {
        ...caseData,
        prediction: null,
        topCandidateExplanation: null
      };

      set((state) => ({
        casesCache: {
          ...state.casesCache,
          [complaintId]: basicCaseData
        }
      }));
      
      // Fetch heavy ML data in background
      Promise.all([
        apiClient.get(`/api/predictions/${complaintId}`).catch(() => null),
        caseData.candidate_withdrawal_locations?.[0]?.withdrawal_location_id 
          ? apiClient.get(`/api/explanations/${complaintId}/candidates/${caseData.candidate_withdrawal_locations[0].withdrawal_location_id}`).catch(() => null) 
          : Promise.resolve(null)
      ]).then(([predictionRes, shapRes]) => {
        set((state) => {
          const currentCache = state.casesCache[complaintId] || basicCaseData;
          return {
            casesCache: {
              ...state.casesCache,
              [complaintId]: {
                ...currentCache,
                prediction: predictionRes?.data || null,
                topCandidateExplanation: shapRes?.data || null
              }
            }
          };
        });
      });
      
      return basicCaseData;
    } catch (error) {
      console.error(`Error fetching case ${complaintId}:`, error);
      throw error;
    }
  },

  fetchGlobalHeatmap: async () => {
    if (get().globalHeatmap) return;
    try {
      const data = await getGlobalHeatmapData();
      set({ globalHeatmap: data });
    } catch (err) {
      console.error("Error fetching global heatmap data:", err);
    }
  }
}));
