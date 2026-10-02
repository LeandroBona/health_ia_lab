import type { AnalysisType, GenerativeModule } from "../types/generative";

const KEY = "healthai-generative-history";
export interface HistoryItem { module: GenerativeModule | "laboratorio"; analysisType: AnalysisType | "content" | "question" | "prompt"; provider: string; generatedAt: string }
export function readHistory(): HistoryItem[] {
  try { return JSON.parse(sessionStorage.getItem(KEY) || "[]") as HistoryItem[]; } catch { return []; }
}
export function addHistory(item: HistoryItem): void {
  try { sessionStorage.setItem(KEY, JSON.stringify([item, ...readHistory()].slice(0, 20))); window.dispatchEvent(new Event("healthai-generative-history")); } catch { /* storage can be disabled */ }
}
export function clearHistory(): void {
  try { sessionStorage.removeItem(KEY); window.dispatchEvent(new Event("healthai-generative-history")); } catch { /* storage can be disabled */ }
}
