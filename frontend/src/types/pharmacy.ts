export type AdherenceCategory = "alta" | "moderada" | "baixa";
export type PharmacyKind = "adesao" | "demanda";
export interface AdherenceFeatures {
  idade: number; quantidade_medicamentos: number; doses_diarias: number;
  tempo_tratamento_dias: number; esquecimentos_30_dias: number;
  retiradas_atrasadas: number; consultas_acompanhamento: number;
  usa_organizador: boolean; recebe_lembretes: boolean; complexidade_rotina: number;
}
export interface AdherencePatient extends AdherenceFeatures { patient_id: string; adesao_percentual: number; categoria_adesao: AdherenceCategory }
export interface AdherencePrediction { patient_id?: string; prediction: AdherenceCategory; probabilities: Record<AdherenceCategory, number>; model_version: string; educational_notice: string; actual_result?: AdherenceCategory; correct?: boolean }
export interface AdherenceStats { total_records: number; average_adherence: number; categories: Record<AdherenceCategory, number>; by_category: {category:AdherenceCategory;count:number;average_forgets:number;average_medicines:number}[]; adherence_distribution:{range:string;count:number}[] }
export interface ClassificationMetrics { accuracy:number; precision_macro:number; recall_macro:number; f1_macro:number; classes:AdherenceCategory[]; confusion_matrix:number[][]; per_class:Record<AdherenceCategory,{precision:number;recall:number;"f1-score":number;support:number}> }
export interface AdherenceModel { status:string; name:string; algorithm:string; version:string; trained_at:string; record_count:number; training_samples:number; test_samples:number; features:string[]; metrics:ClassificationMetrics; algorithms:Record<string,ClassificationMetrics>; educational_notice:string }
export interface DemandRecord { medication_id:string; month:number; year:number; period:string; stock_initial:number; quantity_received:number; quantity_used:number; stock_final:number; seasonality_index:number; trend_index:number; promotion_event:boolean; demand:number }
export interface DemandPrediction { medication_id:string; period:string; prediction:number; prediction_raw:number; features:Record<string,string|number>; algorithm:string; model_version:string; educational_notice:string }
export interface TestPrediction { medication_id:string; period:string; observed:number; predicted:number }
export interface MedicationDetail { medication_id:string; history:DemandRecord[]; prediction:DemandPrediction; test_predictions:TestPrediction[]; average_demand:number; last_demand:number }
export interface MedicationSummary { medication_id:string; average_demand:number; last_demand:number; next_prediction:number; trend:number; periods:number }
export interface DemandStats { medications:number; periods:number; records:number; total_consumption:number }
export interface RegressionMetrics { mae:number; rmse:number; r2:number }
export interface DemandModel { status:string; name:string; algorithm:string; version:string; trained_at:string; record_count:number; training_samples:number; test_samples:number; train_last_period:string; test_first_period:string; features:string[]; metrics:RegressionMetrics; algorithms:Record<string,RegressionMetrics>; evaluation_note:string }
export interface DemandEvaluation extends RegressionMetrics { algorithms:Record<string,RegressionMetrics>; selected_model:string; test_predictions:TestPrediction[]; train_last_period:string; test_first_period:string; note:string }
export interface PharmacyPage<T> { items:T[]; total:number; page:number; page_size:number; pages:number }
export interface PharmacyPreview { success:boolean; filename:string; record_count:number; column_count:number; columns:string[]; detected_types:Record<string,string>; missing_values:Record<string,number>; missing_total:number; preview:Record<string,string|number|boolean>[]; token:string; duplicates:number; importable:number }
export interface PharmacyImportResult { success:boolean; imported:number; ignored:number; total:number }
