export type Result = "recuperacao_adequada" | "recuperacao_lenta" | "abandono";

export interface Patient {
  patient_id: string;
  idade: number;
  sexo: string;
  tipo_lesao: string;
  tempo_lesao_dias: number;
  dor_inicial: number;
  dor_atual: number;
  mobilidade_inicial: number;
  mobilidade_atual: number;
  forca_muscular: number;
  sessoes_previstas: number;
  sessoes_realizadas: number;
  faltas: number;
  adesao_exercicios: number;
  comorbidades: number;
  indice_funcional_inicial: number;
  indice_funcional_atual: number;
  resultado: Result;
}
export interface Distribution {
  name: string;
  count: number;
}
export interface PhysioStats {
  total_patients: number;
  average_age: number;
  average_pain_initial: number;
  average_pain_current: number;
  average_adherence: number;
  registered_results: number;
  results: Record<Result, number>;
  injuries: Distribution[];
  adherence_distribution: Distribution[];
}
export interface PatientsPage {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
export interface DatasetInfo {
  name: string;
  size: number;
  seed: number | null;
  created_at: string;
  format: string;
  area: string;
}
export interface DatasetSchema {
  columns: (keyof Patient)[];
  numeric_columns: (keyof Patient)[];
  sexes: string[];
  injuries: string[];
  results: Result[];
}
export interface Preview {
  success: boolean;
  token: string;
  filename: string;
  record_count: number;
  column_count: number;
  columns: (keyof Patient)[];
  detected_types: Record<string, string>;
  missing_total: number;
  missing_values: Record<string, number>;
  preview: Patient[];
  duplicates: number;
  importable: number;
  expires_at: number;
}
export interface ImportResult {
  success: boolean;
  imported: number;
  ignored: number;
  total: number;
}
export interface ValidationProblem {
  message: string;
  missing_columns?: string[];
  extra_columns?: string[];
  errors?: { row: number; message: string }[];
  invalid_rows?: number;
  missing_total?: number;
}
export interface Exploration {
  column: keyof Patient;
  kind: "numeric" | "categorical";
  count: number;
  missing: number;
  unique: number;
  mean?: number | null;
  min?: number | null;
  max?: number | null;
  median?: number | null;
  std?: number | null;
  distribution: Distribution[];
  truncated: boolean;
}
