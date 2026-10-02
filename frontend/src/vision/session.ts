import type { Angles, Joint } from "./geometry";

export type MetricSample = { t:number; leftElbow:number|null; rightElbow:number|null; leftKnee:number|null; rightKnee:number|null; movements:number };
export type MetricSession = { id:string; startedAt:string; endedAt:string; selectedJoint:Joint; samples:MetricSample[]; movements:number; summary:Record<Joint,number|null> };
const KEY = "healthai.vision.metricSessions.v1";
export const MAX_SAMPLES = 1200;
export const MAX_SESSIONS = 20;

export function readSessions(): MetricSession[] {
  try {
    const data: unknown = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(data) ? data.filter((item):item is MetricSession =>
      typeof item === "object" && item !== null && typeof item.id === "string" &&
      typeof item.endedAt === "string" && typeof item.selectedJoint === "string" &&
      ["leftElbow","rightElbow","leftKnee","rightKnee"].includes(item.selectedJoint) &&
      typeof item.summary === "object" && item.summary !== null && Array.isArray(item.samples)
    ).slice(0, MAX_SESSIONS) : [];
  } catch { return []; }
}

export function buildSession(samples: MetricSample[], selectedJoint: Joint, startedAt: string): MetricSession {
  const joints: Joint[] = ["leftElbow", "rightElbow", "leftKnee", "rightKnee"];
  const summary = {} as Record<Joint,number|null>;
  for (const joint of joints) {
    const values = samples.map(sample=>sample[joint]).filter((value):value is number=>value!==null);
    summary[joint] = values.length ? Math.round(values.reduce((a,b)=>a+b,0)/values.length*10)/10 : null;
  }
  return {id:crypto.randomUUID(),startedAt,endedAt:new Date().toISOString(),selectedJoint,samples:samples.slice(-MAX_SAMPLES),movements:samples.at(-1)?.movements??0,summary};
}

export function saveSession(session: MetricSession): MetricSession[] {
  const updated = [session, ...readSessions()].slice(0, MAX_SESSIONS);
  localStorage.setItem(KEY, JSON.stringify(updated));
  return updated;
}

export function sampleFromAngles(t:number, angles:Angles, movements:number): MetricSample {
  return {t, leftElbow:angles.leftElbow===null?null:Math.round(angles.leftElbow*10)/10, rightElbow:angles.rightElbow===null?null:Math.round(angles.rightElbow*10)/10, leftKnee:angles.leftKnee===null?null:Math.round(angles.leftKnee*10)/10, rightKnee:angles.rightKnee===null?null:Math.round(angles.rightKnee*10)/10, movements};
}
