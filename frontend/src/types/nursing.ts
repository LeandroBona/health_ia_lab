export type Classification = "padrao" | "anomalia";
export type SignalKey = "frequencia_cardiaca" | "frequencia_respiratoria" | "temperatura" | "pressao_sistolica" | "pressao_diastolica" | "saturacao" | "nivel_dor";
export type Signals = Record<SignalKey, number>;
export interface NursingStats { total_patients: number; total_measurements: number; average_measurements_per_patient: number; anomalies: number; anomaly_percentage: number; last_analysis: string | null }
export interface NursingPatient { patient_id: string; idade: number; measurements: number; anomalies: number; anomaly_percentage: number; averages: Signals }
export interface NursingPatientSummary { patient_id: string; idade: number; measurements: number; anomalies: number }
export interface Page<T> { items: T[]; page: number; page_size: number; total: number; pages: number }
export interface Measurement extends Signals { measurement_id: string; patient_id: string; timestamp: string; idade: number; estado: "padrao" | "alterado"; classification: Classification | null; score: number | null; anomaly_index: number | null }
export interface Comparison { value: number; patient_average: number; dataset_average: number; patient_difference: number; dataset_difference: number }
export interface MeasurementDetail extends Measurement { comparisons: Record<SignalKey, Comparison> }
export interface NursingModel { status: string; name?: string; algorithm?: string; version?: string; trained_at?: string; training_records?: number; current_anomalies?: number; features?: SignalKey[]; contamination?: number; seed?: number; statistics?: { artificial_anomalies: number; detected_anomalies: number }; evaluation?: Evaluation; message?: string }
export interface Evaluation { precision: number; recall: number; f1: number; confusion_matrix: number[][]; labels: string[]; artificial_anomalies: number; detected_anomalies: number }
export interface AnomalyPrediction { classification: Classification; score: number; anomaly_index: number; model_version: string; explanation: string }
export interface DatasetInfo { name: string; patient_count: number; measurement_count: number; seed: number | null; created_at: string; format: string; area: string; columns: string[] }
export interface NursingPreview { success: boolean; filename: string; record_count: number; column_count: number; columns: string[]; detected_types: Record<string,string>; missing_values: Record<string,number>; missing_total: number; preview: Record<string,string | number>[]; token: string; duplicates: number; importable: number }
export interface ImportResult { success: boolean; imported: number; ignored: number; total: number }
export interface Explore { column: string; type: "numeric" | "categorical"; count: number; missing: number; mean?: number; minimum?: number; maximum?: number; median?: number; std?: number; distribution: { range: string; count: number }[] | Record<string,number> }

export const signalLabels: Record<SignalKey, string> = {
  frequencia_cardiaca: "Frequência cardíaca", frequencia_respiratoria: "Frequência respiratória",
  temperatura: "Temperatura", pressao_sistolica: "Pressão sistólica", pressao_diastolica: "Pressão diastólica",
  saturacao: "Saturação", nivel_dor: "Nível de dor",
};
export const signalKeys = Object.keys(signalLabels) as SignalKey[];
