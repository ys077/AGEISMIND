import { create } from 'zustand';
import { 
  getDashboardOverview, 
  getModelInfo, 
  getComplaints, 
  getAlerts,
  getAlertSummary,
  getGlobalHeatmapData
} from '../api/client';
import { apiClient } from '../api/client';

const COMPLAINTS_PAGE_SIZE = 50;

let complaintsRequest: Promise<any> | null = null;
let alertsRequest: Promise<any> | null = null;

const summarizeAlerts = (alerts: any[]) => {
  const list = alerts || [];
  return {
    total_alerts: list.length,
    new_alerts: list.filter((a) => a.status === 'NEW').length,
    in_review_alerts: list.filter((a) => a.status === 'IN_REVIEW').length,
    action_taken_alerts: list.filter((a) => a.status === 'ACTION_TAKEN').length,
    high_priority: list.filter((a) => a.priority === 'HIGH' || a.priority === 'CRITICAL').length,
  };
};

export interface AppState {
  dashboardData: any;
  modelInfo: any;
  complaintsList: any;
  alertsList: any;
  alertSummary: any;
  globalHeatmap: any;
  casesCache: Record<string, any>; // Cache for complete case data
  
  isPreloading: boolean;
  hasPreloaded: boolean;
  preloadError: string | null;
  
  preloadApp: (forceRefresh?: boolean) => Promise<void>;
  ensureComplaints: (forceRefresh?: boolean) => Promise<any>;
  ensureAlerts: (forceRefresh?: boolean) => Promise<any>;
  fetchCaseComplete: (complaintId: string) => Promise<any>;
  fetchGlobalHeatmap: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  dashboardData: {},
  modelInfo: {},
  complaintsList: null,
  alertsList: null,
  alertSummary: null,
  globalHeatmap: null,
  casesCache: {},
  
  isPreloading: false,
  hasPreloaded: false,
  preloadError: null,

  ensureComplaints: async (forceRefresh?: boolean) => {
    if (!forceRefresh && get().complaintsList?.items) return get().complaintsList;
    if (!forceRefresh && complaintsRequest) return complaintsRequest;

    complaintsRequest = getComplaints(1, COMPLAINTS_PAGE_SIZE)
      .then((data) => {
        if (data) set({ complaintsList: data });
        return data;
      })
      .catch((err) => {
        console.error(err);
        return get().complaintsList;
      })
      .finally(() => {
        complaintsRequest = null;
      });

    return complaintsRequest;
  },

  ensureAlerts: async (forceRefresh?: boolean) => {
    if (!forceRefresh && Array.isArray(get().alertsList) && get().alertsList.length) {
      return get().alertsList;
    }
    if (!forceRefresh && alertsRequest) return alertsRequest;

    alertsRequest = Promise.all([
      getAlerts().catch((err) => {
        console.error(err);
        return get().alertsList;
      }),
      getAlertSummary().catch((err) => {
        console.error(err);
        return get().alertSummary;
      }),
    ])
      .then(([alerts, summary]) => {
        const list = Array.isArray(alerts)
          ? [...alerts].sort((a: any, b: any) => (b.probability || 0) - (a.probability || 0))
          : [];
        set({
          alertsList: list,
          alertSummary: summary || summarizeAlerts(list),
        });
        return list;
      })
      .finally(() => {
        alertsRequest = null;
      });

    return alertsRequest;
  },

  preloadApp: async (forceRefresh?: boolean) => {
    const { hasPreloaded, isPreloading } = get();

    if (!forceRefresh && (hasPreloaded || isPreloading)) return;

    set({ isPreloading: true, preloadError: null });
    
    try {
      const { ensureComplaints, ensureAlerts } = get();

      const loadSecondary = () => {
        void ensureComplaints(forceRefresh);
        void ensureAlerts(forceRefresh);
      };

      const [dashboardData, modelInfo] = await Promise.all([
        getDashboardOverview().catch(err => {
          console.error("Failed to fetch dashboard overview:", err);
          return null;
        }),
        getModelInfo().catch(err => {
          console.error("Failed to fetch model info:", err);
          return null;
        })
      ]);

      set(state => ({
        dashboardData: dashboardData || state.dashboardData || {},
        modelInfo: modelInfo || state.modelInfo || {},
        isPreloading: false,
        hasPreloaded: true
      }));

      if (forceRefresh) {
        loadSecondary();
      } else {
        const idle = (window as any).requestIdleCallback as
          | ((cb: () => void, opts?: { timeout: number }) => void)
          | undefined;
        if (idle) idle(loadSecondary, { timeout: 1500 });
        else setTimeout(loadSecondary, 0);
      }
    } catch (err) {
      console.error("Preload error:", err);
      set({ preloadError: "Failed to load application data", isPreloading: false, hasPreloaded: true });
    } finally {
      set({ isPreloading: false, hasPreloaded: true });
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
