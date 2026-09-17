import React, { useState, useEffect, useMemo, useRef } from 'react';
// @ts-ignore
import Map, { Source, Layer, Marker, Popup, NavigationControl } from 'react-map-gl/maplibre';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { getHeatmapData, getCandidateExplanation } from '../api/client';
import { formatProbability } from '../utils/probability';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Info, ChevronRight } from 'lucide-react';

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_API_KEY;

export const RiskHeatmap: React.FC<{ complaintId?: string }> = ({ complaintId }) => {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);
  const [explanation, setExplanation] = useState<any | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState<boolean>(false);

  const mapRef = useRef<any>(null);
  const navigate = useNavigate();

  // Filters
  const [minProbability, setMinProbability] = useState<number>(0);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');

  useEffect(() => {
    if (!complaintId) return;
    const fetchHeatmapData = async () => {
      try {
        setLoading(true);
        const data = await getHeatmapData(complaintId);
        setCandidates(data.candidates);
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Unable to connect to investigation server.");
      } finally {
        setLoading(false);
      }
    };
    fetchHeatmapData();
  }, [complaintId]);

  const fetchExplanation = async (candidate: any) => {
    setSelectedCandidate(candidate);
    setExplanation(null);
    if (!complaintId || complaintId === "ALL_COMPLAINTS") return; // Explanation requires a specific case context
    
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

  const filteredCandidates = useMemo(() => {
    return candidates.filter(c => 
      c.probability >= minProbability && 
      (selectedDistrict === 'All' || c.district === selectedDistrict) &&
      c.latitude != null && !isNaN(c.latitude) &&
      c.longitude != null && !isNaN(c.longitude) &&
      // Ensure coordinates fall within approximate Tamil Nadu boundaries
      c.latitude >= 8.0 && c.latitude <= 14.0 &&
      c.longitude >= 76.0 && c.longitude <= 81.0
    );
  }, [candidates, minProbability, selectedDistrict]);

  // Fit bounds dynamically whenever filtered candidates change
  useEffect(() => {
    if (filteredCandidates.length > 0 && mapRef.current) {
      let targetCandidates = filteredCandidates;
      
      // If we are looking at a specific complaint, we want to zoom into the hotspot (top predictions)
      // rather than zooming out to fit all 1500 candidates across the entire state.
      if (complaintId !== "ALL_COMPLAINTS") {
        // Since candidates are returned sorted by rank, take the top 10
        targetCandidates = filteredCandidates.slice(0, 10);
      }
      
      const lats = targetCandidates.map(c => c.latitude);
      const lngs = targetCandidates.map(c => c.longitude);
      
      const bounds: [[number, number], [number, number]] = [
        [Math.min(...lngs) - 0.05, Math.min(...lats) - 0.05], // Southwest coordinates
        [Math.max(...lngs) + 0.05, Math.max(...lats) + 0.05]  // Northeast coordinates
      ];
      
      mapRef.current.fitBounds(bounds, { padding: 40, duration: 1000 });
    }
  }, [filteredCandidates, complaintId]);

  const uniqueDistricts = useMemo(() => {
    const dists = new Set(candidates.map(c => c.district));
    return ['All', ...Array.from(dists).sort()];
  }, [candidates]);

  const geojson = useMemo(() => {
    return {
      type: 'FeatureCollection',
      features: filteredCandidates.map(c => ({
        type: 'Feature',
        properties: {
          probability: c.probability,
          priority: c.priority
        },
        geometry: {
          type: 'Point',
          coordinates: [c.longitude, c.latitude]
        }
      }))
    };
  }, [filteredCandidates]);

  if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Loading geographic intelligence...</div>;
  if (error) return <div className="p-8 text-center text-red-500 font-medium">{error}</div>;
  if (!complaintId) return <div className="p-8 text-center text-slate-500 font-medium bg-slate-50 border border-slate-200 rounded-lg m-4">Select a complaint to view the risk heatmap.</div>;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-lg shadow-sm relative overflow-hidden">
      <div className="bg-slate-50 p-4 flex flex-col md:flex-row justify-between items-center z-10 border-b border-slate-200">
        <div>
          <h2 className="text-sm font-bold text-slate-900">Geographic Risk Map</h2>
          <p className="text-xs text-slate-500 mt-1">
            {complaintId === "ALL_COMPLAINTS" 
              ? "Global Threat Map showing aggregated intelligence" 
              : `Showing prediction candidates for Complaint #${complaintId.substring(0,8)}`
            }
          </p>
        </div>
        <div className="flex flex-col md:flex-row gap-6 mt-4 md:mt-0">
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
        <div className="absolute top-4 left-4 z-10 bg-amber-50 border border-amber-200 rounded-lg p-3 max-w-sm shadow-md pointer-events-none">
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert size={14} className="text-amber-600" />
            <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">Synthetic Prototype Data</p>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">Map locations represent synthetic withdrawal candidate zones and are not confirmed crime hotspots.</p>
        </div>

        {MAPTILER_KEY ? (
          <Map
            ref={mapRef}
            initialViewState={{
              longitude: 78.6569, // Center of Tamil Nadu
              latitude: 11.1271,
              zoom: 6
            }}
            mapStyle={`https://api.maptiler.com/maps/basic-v2/style.json?key=${MAPTILER_KEY}`}
            mapLib={maplibregl}
            style={{ width: '100%', height: '100%' }}
          >
            <NavigationControl position="bottom-right" />
            <Source type="geojson" data={geojson as any}>
              <Layer
                id="heatmap-layer"
                type="heatmap"
                paint={{
                  'heatmap-weight': ['interpolate', ['linear'], ['get', 'probability'], 0, 0, 1, 1],
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
                  'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 4, 9, 25],
                  'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 7, 0.8, 11, 0]
                }}
              />
            </Source>

            {[...filteredCandidates.slice(0, 150)].filter(c => c.probability >= 0.01).reverse().map(c => (
              <Marker 
                key={c.prediction_id} 
                longitude={c.longitude} 
                latitude={c.latitude}
                onClick={(e: any) => {
                  e.originalEvent.stopPropagation();
                  fetchExplanation(c);
                }}
              >
                <div className={`cursor-pointer rounded-full border shadow-md flex items-center justify-center text-white font-bold hover:scale-110 transition-transform ${
                  c.priority === 'CRITICAL' ? 'bg-purple-600 border-white text-xs w-10 h-10 relative z-[60]' :
                  c.priority === 'HIGH' ? 'bg-red-600 border-white text-xs w-9 h-9 relative z-50' : 
                  c.priority === 'MEDIUM' ? 'bg-amber-500 border-white text-[10px] w-8 h-8 relative z-40' : 
                  'bg-blue-600 border-white text-[10px] w-7 h-7 relative z-30'
                }`}>
                  {formatProbability(c.probability)}
                </div>
              </Marker>
            ))}

            {selectedCandidate && (
              <Popup
                longitude={selectedCandidate.longitude}
                latitude={selectedCandidate.latitude}
                anchor="bottom"
                onClose={() => setSelectedCandidate(null)}
                closeOnClick={false}
                maxWidth="350px"
              >
                <div className="p-2 text-slate-800">
                  <div className="font-bold text-sm border-b border-slate-200 pb-2 mb-3 flex justify-between items-center">
                    <span>{complaintId === "ALL_COMPLAINTS" ? "Candidate Withdrawal Zone" : `Candidate Zone #${selectedCandidate.rank}`}</span>
                    {complaintId !== "ALL_COMPLAINTS" && (
                      <button 
                        onClick={() => navigate(`/complaints/${complaintId}`)} 
                        className="flex items-center text-xs text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        View details <ChevronRight size={14} />
                      </button>
                    )}
                  </div>
                  <div className="mb-3 text-xs space-y-1.5">
                    <p><span className="font-semibold text-slate-500 w-28 inline-block">Candidate ID:</span> {selectedCandidate.withdrawal_location_id || selectedCandidate.location_id}</p>
                    <p><span className="font-semibold text-slate-500 w-28 inline-block">District:</span> {selectedCandidate.district}</p>
                    <p><span className="font-semibold text-slate-500 w-28 inline-block">Probability:</span> <span className="font-bold">{formatProbability(selectedCandidate.probability)}</span></p>
                    <p className="flex items-center">
                      <span className="font-semibold text-slate-500 w-28 inline-block">Priority:</span> 
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${selectedCandidate.priority === 'CRITICAL' ? 'bg-purple-100 text-purple-700' : selectedCandidate.priority === 'HIGH' ? 'bg-red-100 text-red-700' : selectedCandidate.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>{selectedCandidate.priority}</span>
                    </p>
                    <p><span className="font-semibold text-slate-500 w-28 inline-block">Rank:</span> #{selectedCandidate.rank}</p>
                    <p><span className="font-semibold text-slate-500 w-28 inline-block">Model Version:</span> {selectedCandidate.model_version || 'withdrawal_model_v1'}</p>
                    <p className="mt-2 text-[10px] text-amber-700 bg-amber-50 border border-amber-200 p-1.5 rounded font-medium">
                      Synthetic candidate withdrawal zone
                    </p>
                  </div>
                  
                  {complaintId !== "ALL_COMPLAINTS" && (
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
                  )}
                  {complaintId === "ALL_COMPLAINTS" && (
                    <div className="bg-slate-50 p-2 rounded border border-slate-200 text-xs text-slate-500 text-center">
                      Detailed SHAP analysis requires a specific case context.
                    </div>
                  )}
                </div>
              </Popup>
            )}
          </Map>
        ) : (
          <div className="flex items-center justify-center h-full bg-slate-50">
            <div className="bg-white border border-red-200 p-8 rounded-lg max-w-md text-center shadow-sm">
              <ShieldAlert className="text-red-500 mx-auto mb-4" size={32} />
              <h2 className="text-sm font-bold text-slate-900 mb-2 uppercase">MapTiler API Key Required</h2>
              <p className="text-sm text-slate-500">Provide VITE_MAPTILER_API_KEY in frontend/.env to initialize the map view.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
