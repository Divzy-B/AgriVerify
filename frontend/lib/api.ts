export type Status = "WITHIN_TOLERANCE" | "REVIEW_REQUIRED" | "INSUFFICIENT_EVIDENCE" | "PENDING" | "HUMAN_REVIEW";
export type Summary = {
  total_registered_farms: number; total_submitted_claims: number; claims_within_review_tolerance: number;
  claims_requiring_investigation: number; claims_insufficient_satellite_evidence: number; pending_human_reviews: number;
  voice_interactions: number; status_distribution: Record<string, number>; recent_claims: Array<{id: string; field_id: string; status: Status; submitted_at: string}>;
};
export type FieldRecord = { id: string; farmer_id: string; name: string; crop_type: string; latitude: number; longitude: number; area_hectares: number; boundary_geojson: { type: string; coordinates: number[][][] } };
export type Claim = { id: string; farmer_id: string; field_id: string; reported_planting_date: string; status: Status; submitted_at: string; reviewer_notes?: string | null };
export type Observation = { acquisition_date: string; ndvi: number | null; cloud_coverage: number | null; additional_indices: Record<string, number>; is_demo_data: boolean };
export type SatelliteAnalysis = { field_id: string; satellite_data_source: string; analysis_mode: string; observations: Observation[]; estimated_planting_window: { start: string; end: string } | null; evidence_quality: string; limitations: string[]; processing_status: string; is_demo_data: boolean };

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
export const DEMO_MODE = "STATIC PREVIEW";

const staticSummary: Summary = { total_registered_farms: 3, total_submitted_claims: 3, claims_within_review_tolerance: 1, claims_requiring_investigation: 1, claims_insufficient_satellite_evidence: 1, pending_human_reviews: 1, voice_interactions: 0, status_distribution: { WITHIN_TOLERANCE: 1, REVIEW_REQUIRED: 1, INSUFFICIENT_EVIDENCE: 1, PENDING: 0, HUMAN_REVIEW: 0 }, recent_claims: [
  { id: "CLM-TX-001", field_id: "TX-001", status: "WITHIN_TOLERANCE", submitted_at: "2025-06-18T13:00:00Z" },
  { id: "CLM-TX-002", field_id: "TX-002", status: "REVIEW_REQUIRED", submitted_at: "2025-06-19T13:00:00Z" },
  { id: "CLM-TX-003", field_id: "TX-003", status: "INSUFFICIENT_EVIDENCE", submitted_at: "2025-06-20T13:00:00Z" },
]};

const staticFields: FieldRecord[] = [
  { id: "TX-001", farmer_id: "F-ALMA", name: "Torres Cotton South", crop_type: "Cotton", latitude: 33.5779, longitude: -101.8552, area_hectares: 42.6, boundary_geojson: {type:"Polygon",coordinates:[[[-101.861,33.572],[-101.849,33.572],[-101.849,33.584],[-101.861,33.584],[-101.861,33.572]]]} },
  { id: "TX-002", farmer_id: "F-NORA", name: "Bennett Cotton East", crop_type: "Cotton", latitude: 32.7767, longitude: -96.797, area_hectares: 31.2, boundary_geojson: {type:"Polygon",coordinates:[[[-96.803,32.771],[-96.791,32.771],[-96.791,32.783],[-96.803,32.783],[-96.803,32.771]]]} },
  { id: "TX-003", farmer_id: "F-DEV", name: "Shah Cotton North", crop_type: "Cotton", latitude: 35.222, longitude: -101.8313, area_hectares: 18.5, boundary_geojson: {type:"Polygon",coordinates:[[[-101.837,35.216],[-101.825,35.216],[-101.825,35.228],[-101.837,35.228],[-101.837,35.216]]]} },
];
const staticClaims: Claim[] = [
  { id: "CLM-TX-001", farmer_id: "F-ALMA", field_id: "TX-001", reported_planting_date: "2025-05-25", status: "WITHIN_TOLERANCE", submitted_at: "2025-06-18T13:00:00Z" },
  { id: "CLM-TX-002", farmer_id: "F-NORA", field_id: "TX-002", reported_planting_date: "2025-07-04", status: "REVIEW_REQUIRED", submitted_at: "2025-06-19T13:00:00Z" },
  { id: "CLM-TX-003", farmer_id: "F-DEV", field_id: "TX-003", reported_planting_date: "2025-05-31", status: "INSUFFICIENT_EVIDENCE", submitted_at: "2025-06-20T13:00:00Z" },
];
const analyses: Record<string, SatelliteAnalysis> = {
  "TX-001": {field_id:"TX-001",satellite_data_source:"SYNTHETIC_DEMO_SERIES",analysis_mode:"DEMO",estimated_planting_window:{start:"2025-05-19",end:"2025-05-29"},evidence_quality:"STRONG_EVIDENCE",processing_status:"COMPLETE",is_demo_data:true,limitations:["Synthetic demonstration series; not satellite-derived evidence."],observations:[
    ["2025-05-01",.12,9],["2025-05-08",.13,12],["2025-05-16",.15,8],["2025-05-23",.18,11],["2025-06-02",.24,10],["2025-06-10",.31,7],["2025-06-18",.42,6]].map(([acquisition_date,ndvi,cloud_coverage])=>({acquisition_date:acquisition_date as string,ndvi:ndvi as number,cloud_coverage:cloud_coverage as number,additional_indices:{savi:Number(ndvi)*.92},is_demo_data:true}))},
  "TX-002": {field_id:"TX-002",satellite_data_source:"SYNTHETIC_DEMO_SERIES",analysis_mode:"DEMO",estimated_planting_window:{start:"2025-05-20",end:"2025-05-30"},evidence_quality:"STRONG_EVIDENCE",processing_status:"COMPLETE",is_demo_data:true,limitations:["Synthetic demonstration series; not satellite-derived evidence."],observations:[
    ["2025-05-01",.11,7],["2025-05-09",.12,10],["2025-05-17",.14,9],["2025-05-25",.17,12],["2025-06-03",.26,10],["2025-06-11",.34,9],["2025-06-19",.43,8]].map(([acquisition_date,ndvi,cloud_coverage])=>({acquisition_date:acquisition_date as string,ndvi:ndvi as number,cloud_coverage:cloud_coverage as number,additional_indices:{savi:Number(ndvi)*.92},is_demo_data:true}))},
  "TX-003": {field_id:"TX-003",satellite_data_source:"SYNTHETIC_DEMO_SERIES",analysis_mode:"DEMO",estimated_planting_window:null,evidence_quality:"INSUFFICIENT_EVIDENCE",processing_status:"INSUFFICIENT_EVIDENCE",is_demo_data:true,limitations:["Fewer than four usable cloud-screened observations are available.","Synthetic demonstration series; not satellite-derived evidence."],observations:[{acquisition_date:"2025-06-04",ndvi:.17,cloud_coverage:58,additional_indices:{savi:.156},is_demo_data:true}]}
};

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, { headers: { "Content-Type": "application/json" }, cache: "no-store" });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
}
export async function getSummary(): Promise<{data: Summary; source: "live"|"preview"}> { try { return {data:await request<Summary>("/dashboard/summary"),source:"live"}; } catch { return {data:staticSummary,source:"preview"}; } }
export async function getFields(): Promise<{data: FieldRecord[]; source: "live"|"preview"}> { try { return {data:await request<FieldRecord[]>("/fields"),source:"live"}; } catch { return {data:staticFields,source:"preview"}; } }
export async function getClaims(): Promise<{data: Claim[]; source: "live"|"preview"}> { try { return {data:await request<Claim[]>("/claims"),source:"live"}; } catch { return {data:staticClaims,source:"preview"}; } }
export async function getAnalysis(id: string): Promise<{data: SatelliteAnalysis; source: "live"|"preview"}> { try { return {data:await request<SatelliteAnalysis>(`/fields/${id}/satellite-analysis`),source:"live"}; } catch { return {data:analyses[id] || analyses["TX-001"],source:"preview"}; } }
export async function simulateVoice(payload: {farm_id:string; crop_type:string; planting_date:string; language:string}) { const response = await fetch(`${baseUrl}/voice/simulator`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); if (!response.ok) throw new Error("Local API unavailable. Start the backend to run a simulation."); return response.json(); }
export { staticFields, staticClaims };

