import type { DashboardMetrics, HealthStatus } from "../types/dashboard";
import type {
  DatasetInfo,
  DatasetSchema,
  Exploration,
  ImportResult,
  Patient,
  PatientsPage,
  PhysioStats,
  Preview,
  ValidationProblem,
} from "../types/physiotherapy";
import type {
  FeatureSweep,
  GlobalFeatureImportance,
  ModelEvaluation,
  ModelInfo,
  ModelMetadata,
  PatientFeatures,
  Prediction,
  PredictionExplanation,
  SimulationChanges,
  SimulationResult,
  SweepFeature,
} from "../types/physiotherapyMl";
import type { AnomalyPrediction, DatasetInfo as NursingDatasetInfo, Evaluation as NursingEvaluation, Explore as NursingExplore, ImportResult as NursingImportResult, Measurement, MeasurementDetail, NursingModel, NursingPatient, NursingPatientSummary, NursingPreview, NursingStats, Page, Signals } from "../types/nursing";
import type { AdherenceFeatures, AdherenceModel, AdherencePatient, AdherencePrediction, AdherenceStats, ClassificationMetrics, DemandEvaluation, DemandModel, DemandPrediction, DemandStats, MedicationDetail, MedicationSummary, PharmacyImportResult, PharmacyKind, PharmacyPage, PharmacyPreview } from "../types/pharmacy";
import type { Animal, AnimalDetail, AnimalFeatures, VetModel, VetPrediction, VetPreview, VetStats, FollowUp } from "../types/veterinary";
import type { PsychologyAnalysis, PsychologyCluster, PsychologyDetail, PsychologyModel, PsychologyPreview, PsychologyRecord, PsychologyStats, PsychologyTerms } from "../types/psychology";

// Request paths already include /api. The configured /api mount therefore
// resolves to the current origin, keeping all calls on the same domain.
const API_BASE = (import.meta.env.VITE_API_URL ?? "/api").replace(/\/+$/, "");
const API_URL = API_BASE.endsWith("/api") ? API_BASE.slice(0, -4) : API_BASE;

export class ApiError extends Error {
  constructor(public problem: ValidationProblem) {
    super(problem.message);
  }
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { Accept: "application/json", ...options.headers },
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    if (
      typeof body === "object" &&
      body !== null &&
      "message" in body &&
      typeof body.message === "string"
    ) {
      throw new ApiError(body as ValidationProblem);
    }
    throw new ApiError({
      message: `Não foi possível concluir a solicitação (status ${response.status}).`,
    });
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: () => apiRequest<HealthStatus>("/api/health"),
  getDashboard: () => apiRequest<DashboardMetrics>("/api/dashboard"),
};

const PHARMACY = "/api/farmacia";
export const pharmacyApi = {
  adherenceStats: () => apiRequest<AdherenceStats>(`${PHARMACY}/adesao/stats`),
  adherencePatients: (query = new URLSearchParams()) => apiRequest<PharmacyPage<AdherencePatient>>(`${PHARMACY}/adesao/patients?${query}`),
  adherencePatient: (id: string) => apiRequest<AdherencePatient>(`${PHARMACY}/adesao/patients/${encodeURIComponent(id)}`),
  adherenceModel: () => apiRequest<AdherenceModel>(`${PHARMACY}/adesao/model`),
  adherenceEvaluation: () => apiRequest<ClassificationMetrics & {algorithms:Record<string,ClassificationMetrics>;selected_model:string;note:string}>(`${PHARMACY}/adesao/model/evaluation`),
  trainAdherence: () => apiRequest<AdherenceModel>(`${PHARMACY}/adesao/model/train`, {method:"POST"}),
  predictAdherencePatient: (id: string) => apiRequest<AdherencePrediction>(`${PHARMACY}/adesao/predict/${encodeURIComponent(id)}`, {method:"POST"}),
  predictAdherence: (data: AdherenceFeatures) => apiRequest<AdherencePrediction>(`${PHARMACY}/adesao/predict`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}),
  demandStats: () => apiRequest<DemandStats>(`${PHARMACY}/demanda/stats`),
  medications: (query = new URLSearchParams()) => apiRequest<PharmacyPage<MedicationSummary>>(`${PHARMACY}/demanda/medications?${query}`),
  medication: (id: string) => apiRequest<MedicationDetail>(`${PHARMACY}/demanda/medications/${encodeURIComponent(id)}`),
  demandModel: () => apiRequest<DemandModel>(`${PHARMACY}/demanda/model`),
  demandEvaluation: () => apiRequest<DemandEvaluation>(`${PHARMACY}/demanda/model/evaluation`),
  trainDemand: () => apiRequest<DemandModel>(`${PHARMACY}/demanda/model/train`, {method:"POST"}),
  predictDemand: (id: string) => apiRequest<DemandPrediction>(`${PHARMACY}/demanda/predict/${encodeURIComponent(id)}`, {method:"POST"}),
  preview: (kind:PharmacyKind,file:File) => {const form=new FormData();form.append("file",file);return apiRequest<PharmacyPreview>(`${PHARMACY}/${kind}/upload/preview`,{method:"POST",body:form})},
  confirm: (kind:PharmacyKind,token:string) => apiRequest<PharmacyImportResult>(`${PHARMACY}/${kind}/upload/confirm`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})}),
  downloadUrl: (kind:PharmacyKind,format:"csv"|"xlsx") => `${API_URL}${PHARMACY}/${kind}/dataset/download/${format}`,
};

const PHYSIO = "/api/fisioterapia";
export const physiotherapyApi = {
  model: () => apiRequest<ModelInfo>(`${PHYSIO}/model`),
  featureImportance: () =>
    apiRequest<GlobalFeatureImportance>(`${PHYSIO}/model/feature-importance`),
  explainPatient: (id: string) =>
    apiRequest<PredictionExplanation>(
      `${PHYSIO}/patients/${encodeURIComponent(id)}/explanation`,
    ),
  explainManual: (features: PatientFeatures) =>
    apiRequest<PredictionExplanation>(`${PHYSIO}/predict/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(features),
    }),
  simulate: (patientId: string, changes: SimulationChanges) =>
    apiRequest<SimulationResult>(`${PHYSIO}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patient_id: patientId, changes }),
    }),
  sweepFeature: (patientId: string, feature: SweepFeature, values: number[]) =>
    apiRequest<FeatureSweep>(`${PHYSIO}/simulate/feature`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patient_id: patientId, feature, values }),
    }),
  evaluation: () => apiRequest<ModelEvaluation>(`${PHYSIO}/model/evaluation`),
  train: () =>
    apiRequest<ModelMetadata>(`${PHYSIO}/model/train`, { method: "POST" }),
  predictPatient: (id: string) =>
    apiRequest<Prediction>(`${PHYSIO}/predict/${encodeURIComponent(id)}`, {
      method: "POST",
    }),
  predict: (features: PatientFeatures) =>
    apiRequest<Prediction>(`${PHYSIO}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(features),
    }),
  stats: () => apiRequest<PhysioStats>(`${PHYSIO}/stats`),
  schema: () => apiRequest<DatasetSchema>(`${PHYSIO}/schema`),
  dataset: () => apiRequest<DatasetInfo>(`${PHYSIO}/dataset`),
  patients: (query: URLSearchParams, signal?: AbortSignal) =>
    apiRequest<PatientsPage>(`${PHYSIO}/patients?${query}`, { signal }),
  patient: (id: string) =>
    apiRequest<Patient>(`${PHYSIO}/patients/${encodeURIComponent(id)}`),
  explore: (column: string) =>
    apiRequest<Exploration>(
      `${PHYSIO}/explore?column=${encodeURIComponent(column)}`,
    ),
  preview: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return apiRequest<Preview>(`${PHYSIO}/upload/preview`, {
      method: "POST",
      body,
    });
  },
  confirm: (token: string) =>
    apiRequest<ImportResult>(`${PHYSIO}/upload/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    }),
  regenerate: (size: number, seed: number) =>
    apiRequest<ImportResult>(`${PHYSIO}/dataset/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ size, seed, confirm: true }),
    }),
  downloadUrl: (format: "csv" | "xlsx") =>
    `${API_URL}${PHYSIO}/dataset/download/${format}`,
};

const NURSING = "/api/enfermagem";
const PSY = "/api/psicologia";
export const psychologyApi = {
  stats: () => apiRequest<PsychologyStats>(`${PSY}/stats`),
  records: (query = new URLSearchParams()) => apiRequest<{items:PsychologyRecord[];total:number;page:number;page_size:number}>(`${PSY}/records?${query}`),
  record: (id:string) => apiRequest<PsychologyDetail>(`${PSY}/records/${encodeURIComponent(id)}`),
  terms: (query = new URLSearchParams()) => apiRequest<PsychologyTerms>(`${PSY}/terms?${query}`),
  clusters: () => apiRequest<{algorithm:string;groups:PsychologyCluster[];explanation:string}>(`${PSY}/clusters`),
  model: () => apiRequest<PsychologyModel>(`${PSY}/model`),
  evaluation: () => apiRequest<{metrics:Record<string,number>;labels:string[];confusion_matrix:number[][];note:string}>(`${PSY}/model/evaluation`),
  train: () => apiRequest<PsychologyModel>(`${PSY}/model/train`,{method:"POST"}),
  analyze: (text:string) => apiRequest<PsychologyAnalysis>(`${PSY}/analyze`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})}),
  keywords: (text:string) => apiRequest<{keywords:{term:string;score:number}[]}>(`${PSY}/keywords`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})}),
  classify: (text:string) => apiRequest<PsychologyAnalysis["classification"]>(`${PSY}/classify`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})}),
  similarity: (text:string) => apiRequest<{results:PsychologyAnalysis["similar"]}>(`${PSY}/similarity`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})}),
  preview: (file:File) => {const body=new FormData();body.append("file",file);return apiRequest<PsychologyPreview>(`${PSY}/upload/preview`,{method:"POST",body})},
  confirm: (token:string) => apiRequest<{success:boolean;imported:number;ignored:number;total:number}>(`${PSY}/upload/confirm`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})}),
  downloadUrl: (format:"csv"|"xlsx") => `${API_URL}${PSY}/dataset/download/${format}`,
};
const VET = "/api/veterinaria";
export const veterinaryApi = {
  stats: () => apiRequest<VetStats>(`${VET}/stats`),
  animals: (query = new URLSearchParams()) => apiRequest<{items: Animal[];total:number;page:number;page_size:number}>(`${VET}/animals?${query}`),
  animal: (id: string) => apiRequest<AnimalDetail>(`${VET}/animals/${encodeURIComponent(id)}`),
  anomalies: (id: string) => apiRequest<{animal_id:string;items:FollowUp[];anomalies:number}>(`${VET}/animals/${encodeURIComponent(id)}/anomalies`),
  model: () => apiRequest<VetModel>(`${VET}/model`),
  anomalyModel: () => apiRequest<VetModel>(`${VET}/anomalies/model`),
  trainAnomaly: () => apiRequest<VetModel>(`${VET}/anomalies/model/train`, {method:"POST"}),
  evaluation: () => apiRequest<{metrics:Record<string,number>;algorithms:Record<string,Record<string,number>>;selected_model:string;note:string}>(`${VET}/model/evaluation`),
  train: () => apiRequest<VetModel>(`${VET}/model/train`, {method:"POST"}),
  predictAnimal: (id: string) => apiRequest<VetPrediction>(`${VET}/predict/${encodeURIComponent(id)}`, {method:"POST"}),
  predict: (data: AnimalFeatures) => apiRequest<VetPrediction>(`${VET}/predict`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}),
  analyze: () => apiRequest<{success:boolean;total:number;anomalies:number}>(`${VET}/anomalies/analyze`, {method:"POST"}),
  predictAnomaly: (data: Pick<FollowUp,"temperatura"|"frequencia_cardiaca"|"atividade_percentual"|"alimentacao_percentual"|"hidratacao_percentual"|"alteracoes_reportadas">) => apiRequest<{classification:string;anomaly_score:number;description:string}>(`${VET}/anomalies/predict`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}),
  preview: (kind:"animals"|"followups", file:File) => {const body=new FormData();body.append("file",file);return apiRequest<VetPreview>(`${VET}/${kind}/upload/preview`,{method:"POST",body})},
  confirm: (kind:"animals"|"followups", token:string) => apiRequest<{success:boolean;imported:number;ignored:number;total:number}>(`${VET}/${kind}/upload/confirm`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})}),
  downloadUrl: (kind:"animals"|"followups",format:"csv"|"xlsx") => `${API_URL}${VET}/${kind}/dataset/download/${format}`,
};
export const nursingApi = {
  stats: () => apiRequest<NursingStats>(`${NURSING}/stats`),
  patients: (query = new URLSearchParams()) => apiRequest<Page<NursingPatientSummary>>(`${NURSING}/patients?${query}`),
  patient: (id: string) => apiRequest<NursingPatient>(`${NURSING}/patients/${encodeURIComponent(id)}`),
  patientMeasurements: (id: string, page = 1, pageSize = 100) => apiRequest<Page<Measurement>>(`${NURSING}/patients/${encodeURIComponent(id)}/measurements?page=${page}&page_size=${pageSize}`),
  measurements: (query = new URLSearchParams()) => apiRequest<Page<Measurement>>(`${NURSING}/measurements?${query}`),
  measurement: (id: string) => apiRequest<MeasurementDetail>(`${NURSING}/measurements/${encodeURIComponent(id)}`),
  model: () => apiRequest<NursingModel>(`${NURSING}/model`),
  evaluation: () => apiRequest<NursingEvaluation>(`${NURSING}/model/evaluation`),
  train: () => apiRequest<NursingModel>(`${NURSING}/model/train`, { method: "POST" }),
  analyze: () => apiRequest<{success:boolean;total:number;anomalies:number}>(`${NURSING}/anomalies/analyze`, { method: "POST" }),
  predict: (signals: Signals) => apiRequest<AnomalyPrediction>(`${NURSING}/anomalies/predict`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(signals) }),
  dataset: () => apiRequest<NursingDatasetInfo>(`${NURSING}/dataset`),
  explore: (column: string) => apiRequest<NursingExplore>(`${NURSING}/dataset/explore?column=${encodeURIComponent(column)}`),
  timeline: () => apiRequest<{date:string;measurements:number;anomalies:number}[]>(`${NURSING}/dataset/timeline`),
  preview: (file: File) => { const body = new FormData(); body.append("file", file); return apiRequest<NursingPreview>(`${NURSING}/upload/preview`, { method: "POST", body }); },
  confirm: (token: string) => apiRequest<NursingImportResult>(`${NURSING}/upload/confirm`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({token}) }),
  downloadUrl: (format: "csv" | "xlsx") => `${API_URL}${NURSING}/dataset/download/${format}`,
};

import type { ContentRequest, ExplainInput, GeneratedText, GenerativeStatus, PromptFields } from "../types/generative";
export const generativeApi = {
  status: () => apiRequest<GenerativeStatus>("/api/generative/status"),
  explain: (input: ExplainInput) => apiRequest<GeneratedText>("/api/generative/explain", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)}),
  content: (input: ContentRequest) => apiRequest<GeneratedText>("/api/generative/content", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)}),
  question: (topic:string,result:string) => apiRequest<GeneratedText>("/api/generative/question", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic,result})}),
  execute: (input: PromptFields) => apiRequest<GeneratedText>("/api/generative/prompt/execute", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)}),
};

import type { AnalysisHistory, CatalogDataset, CatalogModel, DatasetDetail, HistoryPage, SystemStatus } from "../types/platform";
export const platformApi = {
  models: () => apiRequest<{items:CatalogModel[]}>("/api/models"),
  datasets: () => apiRequest<{items:CatalogDataset[]}>("/api/datasets"),
  dataset: (id:string) => apiRequest<DatasetDetail>(`/api/datasets/${encodeURIComponent(id)}`),
  status: () => apiRequest<SystemStatus>("/api/system/status"),
  history: (query:URLSearchParams) => apiRequest<HistoryPage>(`/api/history?${query}`),
  historyDetail: (id:string) => apiRequest<AnalysisHistory>(`/api/history/${encodeURIComponent(id)}`),
  recordVisionSession: (value:{reference:string;movements:number;samples:number;joint:string}) => apiRequest<AnalysisHistory>("/api/history/vision-session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(value)}),
};
export const backendUrl = API_URL;
