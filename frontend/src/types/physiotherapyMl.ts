import type { Patient, Result } from "./physiotherapy";

export type PatientFeatures = Omit<Patient, "patient_id" | "resultado">;
export interface ClassMetrics {
  precision: number;
  recall: number;
  f1: number;
  support: number;
}
export interface Evaluation {
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  f1_macro: number;
  classes: Result[];
  confusion_matrix: number[][];
  per_class: Record<Result, ClassMetrics>;
}
export interface ModelMetadata {
  status: "ready";
  name: string;
  algorithm: string;
  selected_model: string;
  version: string;
  trained_at: string;
  record_count: number;
  training_samples: number;
  test_samples: number;
  features: (keyof PatientFeatures)[];
  random_state: number;
  dataset_source: "default" | "database";
  metrics: Evaluation;
  algorithms: Record<string, Evaluation>;
  training_seconds: number;
  evaluation_note: string;
  educational_notice: string;
  dataset_changed: boolean;
  current_records: number;
}
export type ModelInfo =
  ModelMetadata | { status: "unavailable"; message: string };
export interface ModelEvaluation extends Evaluation {
  version: string;
  algorithms: Record<string, Evaluation>;
  selected_model: string;
  test_samples: number;
  evaluation_note: string;
}
export interface Prediction {
  prediction: Result;
  probabilities: Record<Result, number>;
  confidence: number;
  model_version: string;
  algorithm: string;
  educational_notice: string;
  patient_id?: string;
  actual_result?: Result;
  correct?: boolean;
  partition?: "train" | "test" | "unseen_or_changed";
}

export interface ExplanationFactor {
  feature: keyof PatientFeatures;
  label: string;
  value: number | string;
  impact: number;
  intensity: "Muito baixo" | "Baixo" | "Moderado" | "Alto" | "Muito alto";
}
export interface PredictionExplanation extends Prediction {
  patient_id?: string;
  probability: number;
  impact_unit: "probability_points" | "logit_units";
  positive_factors: ExplanationFactor[];
  negative_factors: ExplanationFactor[];
  factors: ExplanationFactor[];
  explanation_notice: string;
}
export interface GlobalFeatureImportance {
  features: {
    feature: keyof PatientFeatures;
    label: string;
    importance: number;
  }[];
  sample_size: number;
  sample_source: "test";
  model_version: string;
  method: "mean_absolute_shap";
  explanation_notice: string;
}
export type EditableFeature =
  | "adesao_exercicios"
  | "faltas"
  | "dor_atual"
  | "mobilidade_atual"
  | "forca_muscular"
  | "sessoes_realizadas"
  | "indice_funcional_atual";
export type SweepFeature = Exclude<EditableFeature, "forca_muscular">;
export type SimulationChanges = Partial<Pick<PatientFeatures, EditableFeature>>;
export interface Classification {
  prediction: Result;
  probabilities: Record<Result, number>;
  confidence: number;
}
export interface SimulationResult {
  patient_id: string;
  original: Classification;
  simulated: Classification;
  changes: SimulationChanges;
  model_version: string;
  class_changed: boolean;
  probability_deltas: Record<Result, number>;
}
export interface FeatureSweep {
  patient_id: string;
  feature: SweepFeature;
  original_value: number;
  original: Classification;
  points: (Classification & { value: number })[];
}
