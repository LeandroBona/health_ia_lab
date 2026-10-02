export type Evolution = "evolucao_esperada" | "acompanhamento_adicional" | "dados_insuficientes";
export type AnimalFeatures = {
  especie: string; idade_anos: number; peso_kg: number; sexo: string; procedimento: string;
  dias_pos_procedimento: number; temperatura: number; frequencia_cardiaca: number;
  atividade_percentual: number; alimentacao_percentual: number; hidratacao_percentual: number;
  medicacao_administrada_percentual: number; retornos_realizados: number; retornos_previstos: number;
  alteracoes_reportadas: number; indice_recuperacao: number;
};
export type Animal = AnimalFeatures & { animal_id: string; evolucao: Evolution };
export type FollowUp = { followup_id: string; animal_id: string; timestamp: string; temperatura: number; frequencia_cardiaca: number; atividade_percentual: number; alimentacao_percentual: number; hidratacao_percentual: number; alteracoes_reportadas: number; classification: "padrao" | "anomalia" | null; anomaly_score: number | null };
export type AnimalDetail = Animal & { followups: FollowUp[] };
export type VetStats = { animals: number; followups: number; analyzed: number; anomalies: number; species: Record<string, number>; procedures: Record<string, number>; evolution: Record<string, number>; averages: Record<string, number>; notice: string };
export type VetModel = { version: string; algorithm: string; date: string; features: string[]; dataset: string; records: number; seed: number; metrics: Record<string, number>; algorithms?: Record<string, Record<string, number>>; status: string; evaluation_note?: string };
export type VetPrediction = { animal_id: string | null; prediction: Evolution; probabilities: Record<Evolution, number>; actual_result: Evolution | null; correct: boolean | null };
export type VetPreview = { token: string; record_count: number; column_count: number; missing_total: number; duplicates: number; importable: number; columns: string[]; detected_types: Record<string, string>; missing_values: Record<string, number>; preview: Record<string, unknown>[] };
