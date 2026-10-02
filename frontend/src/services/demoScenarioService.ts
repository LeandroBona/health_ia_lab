import { backendUrl } from "./api";

export interface ClassroomReadiness {
  backend:boolean;database:boolean;physiotherapy_model:boolean;nursing_model:boolean;
  pharmacy_models:boolean;veterinary_models:boolean;psychology_model:boolean;
  datasets:number;llm:{available:boolean;mode:string;provider:string};vision:string;
}
export interface DemoScenarios {
  physiotherapy_patient_id:string|null;
  nursing_pattern_id:string|null;nursing_anomaly_id:string|null;
  pharmacy_patient_id:string|null;pharmacy_medication_id:string|null;
  veterinary_animal_id:string|null;psychology_record_id:string|null;
}

async function get<T>(path:string):Promise<T>{
  let response:Response;
  try{response=await fetch(`${backendUrl}${path}`,{headers:{Accept:"application/json"}})}catch{throw new Error("Não foi possível conectar à API. Verifique se o backend está em execução.")}
  if(response.status===404)throw new Error("A API aberta nesta aba não possui as rotas atuais do Modo Aula. Reinicie o backend e tente novamente.");
  if(!response.ok)throw new Error("A preparação do Modo Aula está indisponível. Tente novamente.");
  return response.json() as Promise<T>;
}
export const demoScenarioService={
  readiness:()=>get<ClassroomReadiness>("/api/classroom/readiness"),
  scenarios:()=>get<DemoScenarios>("/api/classroom/scenarios"),
};
