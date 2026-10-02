export interface DashboardMetrics {
  patients: number;
  datasets: number;
  analyses: number;
  models: number;
  anomalies: number;
}

export interface HealthStatus {
  status: "ok";
  application: string;
}
