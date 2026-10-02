export type Point = { x: number; y: number; visibility?: number; presence?: number };
export type Joint = "leftElbow" | "rightElbow" | "leftKnee" | "rightKnee";
export type Angles = Record<Joint, number | null>;
export const MIN_CONFIDENCE = 0.55;
export const JOINT_LABELS: Record<Joint, string> = {
  leftElbow: "Cotovelo esquerdo", rightElbow: "Cotovelo direito",
  leftKnee: "Joelho esquerdo", rightKnee: "Joelho direito",
};
export const LANDMARKS = [
  { index: 0, label: "Nariz" }, { index: 11, label: "Ombro esquerdo" }, { index: 12, label: "Ombro direito" },
  { index: 13, label: "Cotovelo esquerdo" }, { index: 14, label: "Cotovelo direito" },
  { index: 15, label: "Punho esquerdo" }, { index: 16, label: "Punho direito" },
  { index: 23, label: "Quadril esquerdo" }, { index: 24, label: "Quadril direito" },
  { index: 25, label: "Joelho esquerdo" }, { index: 26, label: "Joelho direito" },
  { index: 27, label: "Tornozelo esquerdo" }, { index: 28, label: "Tornozelo direito" },
] as const;
export const CONNECTIONS: [number, number][] = [[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],[23,25],[25,27],[24,26],[26,28]];
const TRIPLETS: Record<Joint, [number,number,number]> = {
  leftElbow:[11,13,15], rightElbow:[12,14,16], leftKnee:[23,25,27], rightKnee:[24,26,28],
};

export function calculateAngle(pointA: Point, vertex: Point, pointC: Point): number | null {
  const ax = pointA.x - vertex.x, ay = pointA.y - vertex.y;
  const cx = pointC.x - vertex.x, cy = pointC.y - vertex.y;
  const magnitude = Math.hypot(ax, ay) * Math.hypot(cx, cy);
  if (magnitude < 1e-8) return null;
  const cosine = Math.max(-1, Math.min(1, (ax * cx + ay * cy) / magnitude));
  return Math.acos(cosine) * 180 / Math.PI;
}

export function isReliable(point: Point | undefined, threshold = MIN_CONFIDENCE): boolean {
  return !!point && Number.isFinite(point.x) && Number.isFinite(point.y)
    && (point.visibility === undefined || point.visibility >= threshold)
    && (point.presence === undefined || point.presence >= threshold);
}

export function anglesFromPose(points: Point[], width: number, height: number, threshold = MIN_CONFIDENCE): Angles {
  const output = {} as Angles;
  for (const joint of Object.keys(TRIPLETS) as Joint[]) {
    const [a,b,c] = TRIPLETS[joint];
    if (![a,b,c].every(index => isReliable(points[index], threshold))) { output[joint] = null; continue; }
    const pixel = (point: Point): Point => ({x:point.x * width, y:point.y * height});
    output[joint] = calculateAngle(pixel(points[a]), pixel(points[b]), pixel(points[c]));
  }
  return output;
}

export function compareSides(angles: Angles): {elbows:number|null;knees:number|null} {
  return {
    elbows: angles.leftElbow === null || angles.rightElbow === null ? null : Math.abs(angles.leftElbow - angles.rightElbow),
    knees: angles.leftKnee === null || angles.rightKnee === null ? null : Math.abs(angles.leftKnee - angles.rightKnee),
  };
}

// Um ciclo conta somente ao voltar à extensão após passar pela flexão configurada.
export class MovementCounter {
  private phase: "ready" | "flexed" = "ready";
  count = 0;
  readonly flexedBelow: number;
  readonly extendedAbove: number;
  constructor(flexedBelow = 100, extendedAbove = 150) {
    if (flexedBelow >= extendedAbove) throw new Error("Os limites de contagem devem ter histerese.");
    this.flexedBelow = flexedBelow;
    this.extendedAbove = extendedAbove;
  }
  update(angle: number | null): number {
    if (angle === null || !Number.isFinite(angle)) { this.phase = "ready"; return this.count; }
    if (this.phase === "ready" && angle < this.flexedBelow) this.phase = "flexed";
    else if (this.phase === "flexed" && angle > this.extendedAbove) { this.phase = "ready"; this.count += 1; }
    return this.count;
  }
  reset() { this.phase = "ready"; this.count = 0; }
}
