import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { NursingError, NursingHeader, NursingLoading, NursingNav } from "../components/nursing/Shared";
import { nursingApi } from "../services/api";

interface Day { date: string; measurements: number; anomalies: number }

export function NursingTimelinePage() {
  const [days, setDays] = useState<Day[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    nursingApi.timeline().then(setDays).catch((issue: unknown) => setError(issue instanceof Error ? issue.message : "Falha ao carregar série temporal."));
  }, []);
  return <div className="space-y-6">
    <NursingHeader title="Distribuição temporal · Enfermagem" subtitle="Explore o volume de medições e classificações anômalas ao longo dos dias do dataset sintético." />
    <NursingNav />
    {error && <NursingError message={error} />}
    {!days ? <NursingLoading /> : <section className="surface-card p-6">
      <h2 className="section-title">Medições ao longo do tempo</h2>
      <p className="mt-2 text-sm text-slate-600">As contagens vêm do SQLite. A classificação de anomalia é calculada pelo Isolation Forest, não por limites clínicos.</p>
      <div className="mt-6 h-96"><ResponsiveContainer width="100%" height="100%"><LineChart data={days} margin={{left:0,right:15,bottom:20}}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date" tick={{fontSize:11}} minTickGap={30}/><YAxis/><Tooltip/><Legend/><Line type="monotone" dataKey="measurements" name="Medições" stroke="#0f766e" dot={false}/><Line type="monotone" dataKey="anomalies" name="Anomalias" stroke="#d97706" dot={false}/></LineChart></ResponsiveContainer></div>
    </section>}
  </div>;
}
