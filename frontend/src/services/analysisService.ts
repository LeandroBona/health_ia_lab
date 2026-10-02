import type { AnalysisHistory, HistoryPage } from "../types/platform";
import { platformApi } from "./api";

/** High-level cross-module result metadata; specialized model payloads stay in their own APIs. */
export interface AnalysisResult {
  module:string; type:string; model:string; prediction?:string|number; probabilities?:Record<string,number>;
  metadata?:Record<string,unknown>; explanation_available:boolean;
}

export const analysisService = {
  list: (filters:URLSearchParams) => platformApi.history(filters),
  detail: (id:string):Promise<AnalysisHistory> => platformApi.historyDetail(id),
  count: async ():Promise<number> => (await platformApi.history(new URLSearchParams({page_size:"1"}))).total,
  recordVisionSession: (session:{id:string;movements:number;samples:unknown[];selectedJoint:string}) => platformApi.recordVisionSession({reference:session.id,movements:session.movements,samples:session.samples.length,joint:session.selectedJoint}),
  linkedRecordPath: (item:AnalysisHistory):string|null => {
    const ref=item.record_reference;
    if(!ref)return null;
    if(item.module==="fisioterapia"||item.module==="ia-generativa"&&ref.startsWith("PAC-"))return `/fisioterapia/pacientes/${encodeURIComponent(ref)}`;
    if(item.module==="enfermagem"||item.module==="ia-generativa"&&/^MED-\d{6}$/.test(ref))return ref.startsWith("ENF-")?`/enfermagem/paciente/${encodeURIComponent(ref)}`:`/enfermagem/medicao/${encodeURIComponent(ref)}`;
    if(item.module==="farmacia"&&ref.startsWith("FAR-")||item.module==="ia-generativa"&&ref.startsWith("FAR-"))return `/farmacia/adesao/paciente/${encodeURIComponent(ref)}`;
    if(item.module==="farmacia"&&ref.startsWith("MED-")||item.module==="ia-generativa"&&/^MED-\d{3}$/.test(ref))return `/farmacia/demanda/${encodeURIComponent(ref)}`;
    if(item.module==="veterinaria"||item.module==="ia-generativa"&&ref.startsWith("VET-"))return `/veterinaria/animal/${encodeURIComponent(ref)}`;
    if(item.module==="psicologia"||item.module==="ia-generativa"&&ref.startsWith("PSI-"))return `/psicologia/relato/${encodeURIComponent(ref)}`;
    if(item.module==="visao-computacional")return "/visao-computacional";
    return null;
  },
};
export type { HistoryPage };
