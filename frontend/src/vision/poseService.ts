import { FilesetResolver, PoseLandmarker } from "@mediapipe/tasks-vision";
import type { Point } from "./geometry";

export interface PoseEstimationService {
  initialize(): Promise<void>;
  estimate(video: HTMLVideoElement, timestampMs: number): Point[];
  close(): void;
}

export class MediaPipePoseService implements PoseEstimationService {
  private detector: PoseLandmarker | null = null;
  async initialize(): Promise<void> {
    if (this.detector) return;
    const base = `${import.meta.env.BASE_URL}mediapipe`;
    const files = await FilesetResolver.forVisionTasks(base);
    const options = { baseOptions: {modelAssetPath: `${base}/pose_landmarker_lite.task`, delegate: "GPU" as const}, runningMode: "VIDEO" as const, numPoses: 1, minPoseDetectionConfidence: 0.5, minPosePresenceConfidence: 0.5, minTrackingConfidence: 0.5 };
    try { this.detector = await PoseLandmarker.createFromOptions(files, options); }
    catch { this.detector = await PoseLandmarker.createFromOptions(files, {...options, baseOptions:{...options.baseOptions, delegate:"CPU"}}); }
  }
  estimate(video: HTMLVideoElement, timestampMs: number): Point[] {
    if (!this.detector) return [];
    return this.detector.detectForVideo(video, timestampMs).landmarks[0] ?? [];
  }
  close(): void { this.detector?.close(); this.detector = null; }
}
