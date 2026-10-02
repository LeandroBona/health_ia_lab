export type GenerativeModule = "fisioterapia" | "enfermagem" | "farmacia" | "veterinaria" | "psicologia";
export type AnalysisType = "prediction" | "anomaly" | "demand" | "nlp";
export type ExplanationLevel = "Simples" | "Acadêmica" | "Técnica";
export type Creativity = "Baixa" | "Média" | "Alta";
export interface GenerativeStatus { provider: string; available: boolean; model: string | null; mode: "online" | "offline" }
export interface GeneratedText { provider: string; explanation: string; generated_at: string; mode: "online" | "offline"; fallback_reason: string | null }
export interface ExplainInput { module: GenerativeModule; analysis_type: AnalysisType; data: Record<string, unknown>; level?: ExplanationLevel; provider?: "auto" | "local"; record_reference?:string }
export interface PromptFields { context: string; role: string; objective: string; data: string; constraints: string; output_format: string; creativity: Creativity }
export interface ContentRequest { topic: string; level: "Básico" | "Intermediário" | "Avançado"; length: "Curto" | "Médio" | "Longo"; creativity: Creativity }
