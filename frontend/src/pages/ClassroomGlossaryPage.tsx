import { Link, useSearchParams } from "react-router-dom";
import { GlossaryList } from "../components/classroom/ClassroomUI";
import "../styles/classroom.css";

export function ClassroomGlossaryPage(){
  const [params]=useSearchParams();
  const step=params.get("step")??"before";
  return <main className="classroom-glossary-page"><header><p className="classroom-kicker">HEALTHAI LAB · MODO AULA</p><h1>Glossário de IA</h1><p>Definições simples para consultar durante a aula. Fórmulas ficam ocultas em “Ver explicação técnica”.</p><Link className="classroom-link" to={`/aula?step=${encodeURIComponent(step)}`}>← Voltar à aula</Link></header><GlossaryList/></main>;
}
