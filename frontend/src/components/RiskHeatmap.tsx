import React, { useState, useEffect, useMemo, useRef } from 'react';
// @ts-ignore
import Map, { Source, Layer, Marker, Popup, NavigationControl } from 'react-map-gl/maplibre';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { getHeatmapData, getCandidateExplanation } from '../api/client';
import { useAppStore } from '../store/appDataStore';
import { formatProbability } from '../utils/probability';
import { useNavigate } from 'react-router-dom';
import { Info, ChevronRight, Activity, MapPin } from 'lucide-react';

interface RiskHeatmapProps {
  mode: 'global' | 'complaint';
  complaintId?: string;
}

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_API_KEY;


export const RiskHeatmap: React.FC<RiskHeatmapProps> = ({ mode, complaintId }) => {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [explanation, setExplanation] = useState<any | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState<boolean>(false);

  const mapRef = useRef<any>(null);
  const navigate = useNavigate();
  const { globalHeatmap, modelInfo } = useAppStore();
  
  // Dynamic risk thresholds from backend
  const thresholds = useMemo(() => {
    return modelInfo?.risk_thresholds || {
      critical: 0.75,
      high: 0.50,
      medium: 0.25
    };
  }, [modelInfo]);

  // Filters
  const [minProbability, setMinProbability] = useState<number>(0);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');
  const [displayLimit, setDisplayLimit] = useState<number | 'ALL'>(10);

  // Fetch Complaint Data if in complaint mode
  useEffect(() => {
    if (mode === 'complaint' && complaintId) {
      const fetchHeatmapData = async () => {
        try {
          setLoading(true);
          const data = await getHeatmapData(complaintId);
          setCandidates(data.candidates || []);
          setError(null);
        } catch (err) {
          console.error(err);
          setError("Unable to connect to investigation server.");
        } finally {
          setLoading(false);
        }
      };
      fetchHeatmapData();
    }
  }, [mode, complaintId]);

  // Fetch Global Data if in global mode
  useEffect(() => {
    if (mode === 'global') {
      const { fetchGlobalHeatmap } = useAppStore.getState();
      fetchGlobalHeatmap();
    }
  }, [mode]);

  // Use store data for global mode
  const currentData = useMemo(() => {
    if (mode === 'global') {
      return globalHeatmap?.candidates || [];
    }
    return candidates;
  }, [mode, globalHeatmap, candidates]);

  const fetchExplanation = async (candidate: any) => {
    setSelectedItem(candidate);
    setExplanation(null);
    if (mode === 'global' || !complaintId) return; // Explanation requires a specific case context
    
    setLoadingExplanation(true);
    try {
      const res = await getCandidateExplanation(complaintId, candidate.withdrawal_location_id);
      setExplanation(res.candidate);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingExplanation(false);
    }
  };

  const filteredData = useMemo(() => {
    return currentData.filter((c: any) => {
      const prob = mode === 'global' ? c.average_probability : c.probability;
      return (
        prob >= minProbability && 
        (selectedDistrict === 'All' || c.district === selectedDistrict) &&
        c.latitude != null && !isNaN(c.latitude) &&
        c.longitude != null && !isNaN(c.longitude)
      );
    });
  }, [currentData, minProbability, selectedDistrict, mode]);

  const displayedData = useMemo(() => {
    if (mode === 'global') {
      // Global uses MapLibre layers, so we don't truncate DOM markers, pass all filtered data
      return filteredData;
    }
    // Complaint mode limits React DOM markers
    return displayLimit === 'ALL' ? filteredData : filteredData.slice(0, displayLimit);
  }, [filteredData, displayLimit, mode]);

  // Fit bounds dynamically for COMPLAINT mode. Global mode is fixed to Tamil Nadu.
  useEffect(() => {
    if (mode === 'complaint' && displayedData.length > 0 && mapRef.current) {
      const lats = displayedData.map((c: any) => c.latitude);
      const lngs = displayedData.map((c: any) => c.longitude);
      
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLng = Math.min(...lngs);
      const maxLng = Math.max(...lngs);
      
      if (maxLat - minLat < 0.01 && maxLng - minLng < 0.01) {
        mapRef.current.flyTo({ center: [minLng, minLat], zoom: 13, duration: 1000 });
      } else {
        const bounds: [[number, number], [number, number]] = [
          [minLng - 0.05, minLat - 0.05],
          [maxLng + 0.05, maxLat + 0.05]
        ];
        mapRef.current.fitBounds(bounds, { padding: 40, duration: 1000 });
      }
    } else if (mode === 'global' && mapRef.current) {
        // Reset to strict Tamil Nadu bounds if switching to global
        const tnBounds: [[number, number], [number, number]] = [
          [76.14, 8.07],
          [80.34, 13.50]
        ];
        mapRef.current.fitBounds(tnBounds, { padding: 40, duration: 1000 });
    }
  }, [displayedData, mode]);

  const uniqueDistricts = useMemo(() => {
    const dists = new Set<string>(currentData.map((c: any) => c.district));
    return ['All', ...Array.from(dists).sort()];
  }, [currentData]);

  // GeoJSON for Global Mode layers
  const globalGeojson = useMemo(() => {
    if (mode !== 'global') return { type: 'FeatureCollection', features: [] };
    
    // TN approximate bounding box to strictly filter out any outliers (e.g. Sri Lanka, far Kerala/Karnataka)
    const TN_BOUNDS = { minLat: 8.07, maxLat: 13.50, minLng: 76.14, maxLng: 80.34 };

    const validData = filteredData.filter((c: any) => 
      c.latitude >= TN_BOUNDS.minLat && c.latitude <= TN_BOUNDS.maxLat &&
      c.longitude >= TN_BOUNDS.minLng && c.longitude <= TN_BOUNDS.maxLng
    );

    return {
      type: 'FeatureCollection',
      features: validData.map((c: any) => ({
        type: 'Feature',
        properties: {
          location_id: c.location_id,
          district: c.district,
          prediction_count: c.prediction_count,
          complaint_count: c.complaint_count,
          average_probability: c.average_probability,
          maximum_probability: c.maximum_probability,
          risk_level: c.risk_level
        },
        geometry: {
          type: 'Point',
          coordinates: [c.longitude, c.latitude]
        }
      }))
    };
  }, [filteredData, mode]);

  if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Loading geographic intelligence...</div>;
  if (error) return <div className="p-8 text-center text-red-500 font-medium">{error}</div>;
  if (mode === 'complaint' && !complaintId) return <div className="p-8 text-center text-slate-500 font-medium bg-slate-50 border border-slate-200 rounded-lg m-4">Select a complaint to view the risk heatmap.</div>;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-lg shadow-sm relative overflow-hidden">
      <div className="bg-slate-50 p-4 flex flex-col md:flex-row justify-between items-center z-10 border-b border-slate-200">
        <div>
          <h2 className="text-sm font-bold text-slate-900">
             {mode === 'global' ? "Tamil Nadu Risk Radar" : "Complaint Withdrawal Risk"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {mode === 'global' 
              ? "Aggregated Predictive Risk across all monitored regions" 
              : `Predicted Withdrawal Candidates for Complaint #${complaintId?.substring(0,8)}`
            }
          </p>
        </div>
        <div className="flex flex-col md:flex-row gap-6 mt-4 md:mt-0">
          {mode === 'complaint' && (
            <div className="flex flex-col">
              <label className="text-xs font-semibold text-slate-600 mb-1">Show Candidates</label>
              <select 
                value={displayLimit === 'ALL' ? 'ALL' : displayLimit} 
                onChange={e => setDisplayLimit(e.target.value === 'ALL' ? 'ALL' : parseInt(e.target.value))}
                className="bg-white border border-slate-300 text-slate-700 py-1 px-2 rounded text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
                <option value="ALL">All Candidates</option>
              </select>
            </div>
          )}
          <div className="flex flex-col">
            <label className="text-xs font-semibold text-slate-600 mb-1">Min Probability: {(minProbability * 100).toFixed(0)}%</label>
            <input 
              type="range" 
              min="0" max="1" step="0.05" 
              value={minProbability} 
              onChange={e => setMinProbability(parseFloat(e.target.value))} 
              className="w-32 accent-blue-600"
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs font-semibold text-slate-600 mb-1">Filter District</label>
            <select 
              value={selectedDistrict} 
              onChange={e => setSelectedDistrict(e.target.value)}
              className="bg-white border border-slate-300 text-slate-700 py-1 px-2 rounded text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              {uniqueDistricts.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 relative">
        {mode === 'complaint' && candidates.length > 0 && (
          <div className="absolute top-28 left-4 z-10 bg-white border border-slate-200 rounded-lg p-4 w-64 shadow-lg pointer-events-auto">
            <h3 className="text-xs font-bold text-slate-800 mb-2 border-b border-slate-200 pb-2 flex items-center gap-2"><MapPin size={14}/> CASE-SPECIFIC PREDICTION</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Complaint:</span>
                <span className="font-semibold text-slate-800">{complaintId?.substring(0, 8)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Candidates Scored:</span>
                <span className="font-semibold text-slate-800">{candidates.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Displayed:</span>
                <span className="font-semibold text-slate-800">{displayedData.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Top Probability:</span>
                <span className="font-semibold text-slate-800">{formatProbability(candidates[0]?.probability)}</span>
              </div>
              <div className="flex justify-between mt-2 pt-2 border-t border-slate-100">
                <span className="text-slate-500">Status:</span>
                <span className={`font-bold ${
                  (candidates[0]?.probability || 0) >= 0.75 ? 'text-green-600' :
                  (candidates[0]?.probability || 0) >= 0.25 ? 'text-amber-600' : 'text-red-600'
                }`}>
                  {(candidates[0]?.probability || 0) >= 0.75 ? 'HIGH SIGNAL' :
                   (candidates[0]?.probability || 0) >= 0.25 ? 'MODERATE SIGNAL' : 'LOW SIGNAL'}
                </span>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 mt-3 italic leading-tight">
              Ranked candidates are investigative leads and do not confirm that a cash withdrawal occurred.
            </p>
          </div>
        )}
        
        {mode === 'global' && currentData.length > 0 && (
          <div className="absolute top-28 left-4 z-10 bg-white border border-slate-200 rounded-lg p-4 w-64 shadow-lg pointer-events-auto">
            <h3 className="text-xs font-bold text-slate-800 mb-2 border-b border-slate-200 pb-2 flex items-center gap-2"><Activity size={14}/> AGGREGATED INTELLIGENCE</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Unique ATM Zones:</span>
                <span className="font-semibold text-slate-800">{currentData.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Zones Displayed:</span>
                <span className="font-semibold text-slate-800">{displayedData.length}</span>
              </div>
            </div>
          </div>
        )}

        <Map
          ref={mapRef}
          initialViewState={{
            longitude: 78.6569, // Center of Tamil Nadu
            latitude: 11.1271,
            zoom: 6
          }}
          mapStyle={MAPTILER_KEY ? `https://api.maptiler.com/maps/basic-v2/style.json?key=${MAPTILER_KEY}` : undefined}
          mapLib={maplibregl}
          style={{ width: '100%', height: '100%' }}
          interactiveLayerIds={mode === 'global' ? ['global-clusters', 'global-unclustered'] : undefined}
          onClick={(e: any) => {
             if (mode === 'global' && e.features && e.features.length > 0) {
                const feature = e.features[0];
                setSelectedItem({
                   ...feature.properties,
                   longitude: e.lngLat.lng,
                   latitude: e.lngLat.lat
                });
             }
          }}
          cursor={mode === 'global' ? 'pointer' : 'grab'}
        >
          <NavigationControl position="bottom-right" />
          
          {/* Global Mode: Render MapLibre GeoJSON Source & Layers */}
          {mode === 'global' && (
            <Source 
              type="geojson" 
              data={globalGeojson as any}
              cluster={true}
              clusterMaxZoom={14}
              clusterRadius={50}
              clusterProperties={{
                max_prob: ['max', ['get', 'maximum_probability']],
                pred_count: ['+', ['get', 'prediction_count']]
              }}
            >
              <Layer
                id="global-heatmap"
                type="heatmap"
                paint={{
                  'heatmap-weight': ['interpolate', ['linear'], ['get', 'average_probability'], 0, 0, 1, 1],
                  'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 9, 3],
                  'heatmap-color': [
                    'interpolate', ['linear'], ['heatmap-density'],
                    0, 'rgba(37, 99, 235, 0)',
                    0.2, 'rgba(37, 99, 235, 0.2)',
                    0.4, 'rgba(37, 99, 235, 0.4)',
                    0.6, 'rgba(245, 158, 11, 0.6)',
                    0.8, 'rgba(220, 38, 38, 0.8)',
                    1, 'rgba(220, 38, 38, 1)'
                  ],
                  'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 10, 9, 30],
                  'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 6, 0.8, 11, 0]
                }}
              />
              <Layer
                id="global-clusters"
                type="circle"
                filter={['has', 'point_count']}
                paint={{
                  'circle-radius': [
                    'step',
                    ['get', 'point_count'],
                    16, // base radius
                    10, 22,
                    50, 30
                  ],
                  'circle-color': [
                    'step',
                    ['get', 'max_prob'],
                    '#2563eb', // LOW
                    thresholds.medium, '#f59e0b', // MEDIUM
                    thresholds.high, '#dc2626', // HIGH
                    thresholds.critical, '#9333ea' // CRITICAL
                  ],
                  'circle-opacity': 0.85,
                  'circle-stroke-width': 2,
                  'circle-stroke-color': '#ffffff'
                }}
              />
              <Layer
                id="global-cluster-count"
                type="symbol"
                filter={['has', 'point_count']}
                layout={{
                  'text-field': '{point_count_abbreviated}',
                  'text-size': 12,
                  'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold']
                }}
                paint={{
                  'text-color': '#ffffff'
                }}
              />
              <Layer
                id="global-unclustered"
                type="circle"
                filter={['!', ['has', 'point_count']]}
                paint={{
                  'circle-radius': [
                    'interpolate', ['linear'], ['get', 'complaint_count'],
                    1, 6,
                    50, 12,
                    200, 20
                  ],
                  'circle-color': [
                    'match',
                    ['get', 'risk_level'],
                    'CRITICAL', '#9333ea', // purple-600
                    'HIGH', '#dc2626',     // red-600
                    'MEDIUM', '#f59e0b',   // amber-500
                    '#2563eb'              // blue-600 (LOW)
                  ],
                  'circle-opacity': 0.8,
                  'circle-stroke-width': 1,
                  'circle-stroke-color': '#ffffff'
                }}
              />
            </Source>
          )}

          {/* Complaint Mode: Render React DOM Markers */}
          {mode === 'complaint' && [...displayedData].reverse().map((c: any) => (
            <Marker 
              key={c.prediction_id || `${c.latitude}-${c.longitude}`} 
              longitude={c.longitude} 
              latitude={c.latitude}
              onClick={(e: any) => {
                e.originalEvent.stopPropagation();
                fetchExplanation(c);
              }}
            >
              <div className={`cursor-pointer rounded-full border shadow-md flex items-center justify-center text-white font-bold hover:scale-110 transition-transform ${
                c.priority === 'CRITICAL' ? 'bg-purple-600 border-white text-xs w-8 h-8 relative z-[60]' :
                c.priority === 'HIGH' ? 'bg-red-600 border-white text-xs w-7 h-7 relative z-50' : 
                c.priority === 'MEDIUM' ? 'bg-amber-500 border-white text-[10px] w-6 h-6 relative z-40' : 
                'bg-blue-600 border-white text-[10px] w-5 h-5 relative z-30'
              } ${c.rank <= 3 ? 'ring-4 ring-slate-900/60 shadow-xl z-[70]' : ''}`}>
                {c.rank ? `#${c.rank}` : ''}
              </div>
            </Marker>
          ))}

          {/* Popup */}
          {selectedItem && (
            <Popup
              longitude={selectedItem.longitude}
              latitude={selectedItem.latitude}
              anchor="bottom"
              onClose={() => setSelectedItem(null)}
              closeOnClick={false}
              maxWidth="350px"
            >
              <div className="p-2 text-slate-800">
                {mode === 'global' ? (
                  <>
                    <div className="font-bold text-sm border-b border-slate-200 pb-2 mb-3">
                       {selectedItem.cluster ? 'Aggregated Risk Cluster' : `Zone: ${selectedItem.location_id}`}
                    </div>
                    <div className="mb-3 text-xs space-y-1.5">
                      {selectedItem.cluster ? (
                        <>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Locations:</span> {selectedItem.point_count}</p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Max Probability:</span> <span className="font-bold">{formatProbability(selectedItem.max_prob)}</span></p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Total Predictions:</span> {selectedItem.pred_count}</p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Peak Risk Level:</span> 
                             <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                               selectedItem.max_prob >= thresholds.critical ? 'bg-purple-100 text-purple-700' :
                               selectedItem.max_prob >= thresholds.high ? 'bg-red-100 text-red-700' :
                               selectedItem.max_prob >= thresholds.medium ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                             }`}>
                               {selectedItem.max_prob >= thresholds.critical ? 'CRITICAL' : selectedItem.max_prob >= thresholds.high ? 'HIGH' : selectedItem.max_prob >= thresholds.medium ? 'MEDIUM' : 'LOW'}
                             </span>
                          </p>
                        </>
                      ) : (
                        <>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">District:</span> {selectedItem.district}</p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Aggregated Risk:</span> 
                             <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${selectedItem.risk_level === 'CRITICAL' ? 'bg-purple-100 text-purple-700' : selectedItem.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' : selectedItem.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>{selectedItem.risk_level}</span>
                          </p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Evaluated Predictions:</span> {selectedItem.prediction_count}</p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Average Probability:</span> <span className="font-bold">{formatProbability(selectedItem.average_probability)}</span></p>
                          <p><span className="font-semibold text-slate-500 w-28 inline-block">Highest Probability:</span> <span className="font-bold">{formatProbability(selectedItem.maximum_probability)}</span></p>
                        </>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <div className="font-bold text-sm border-b border-slate-200 pb-2 mb-3 flex justify-between items-center">
                      <span>#{selectedItem.rank} {selectedItem.brand || selectedItem.operator || `Zone ${selectedItem.withdrawal_location_id}`}</span>
                      {complaintId && (
                        <button 
                          onClick={() => navigate(`/complaints/${complaintId}`)} 
                          className="flex items-center text-xs text-blue-600 hover:text-blue-800 transition-colors"
                        >
                          View details <ChevronRight size={14} />
                        </button>
                      )}
                    </div>
                    <div className="mb-3 text-xs space-y-1.5">
                      <p><span className="font-semibold text-slate-500 w-28 inline-block">Candidate ID:</span> {selectedItem.withdrawal_location_id}</p>
                      <p><span className="font-semibold text-slate-500 w-28 inline-block">District:</span> {selectedItem.district}</p>
                      <p><span className="font-semibold text-slate-500 w-28 inline-block">Model Prob:</span> <span className="font-bold">{formatProbability(selectedItem.probability)}</span></p>
                      <p className="flex items-center">
                        <span className="font-semibold text-slate-500 w-28 inline-block">Risk Level:</span> 
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${selectedItem.priority === 'CRITICAL' ? 'bg-purple-100 text-purple-700' : selectedItem.priority === 'HIGH' ? 'bg-red-100 text-red-700' : selectedItem.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>{selectedItem.priority}</span>
                      </p>
                      <p><span className="font-semibold text-slate-500 w-28 inline-block">Rank:</span> #{selectedItem.rank}</p>
                      <p><span className="font-semibold text-slate-500 w-28 inline-block">Model Version:</span> {selectedItem.model_version || 'v1'}</p>
                    </div>
                    
                    <div className="bg-slate-50 p-3 rounded border border-slate-200">
                      <h4 className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1"><Info size={12}/> Top Driving Factors</h4>
                      {loadingExplanation ? (
                        <p className="text-xs text-slate-500 animate-pulse">Running SHAP analysis...</p>
                      ) : explanation ? (
                        <div className="max-h-32 overflow-y-auto pr-1 custom-scrollbar">
                          {explanation.positive_factors.length > 0 ? (
                            <ul className="text-xs space-y-2 text-slate-700">
                              {explanation.positive_factors.slice(0, 3).map((f: any, i: number) => (
                                <li key={i} className="flex gap-2 items-start">
                                  <span className="text-red-500 font-bold mt-0.5">▲</span>
                                  <span>{f.explanation_text || f.factor_name}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-xs text-slate-500">No significant active signals.</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500">Analysis unavailable.</p>
                      )}
                    </div>
                  </>
                )}
              </div>
            </Popup>
          )}
        </Map>
      </div>
    </div>
  );
};
