import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { classroomGlossary, glossaryByTerm } from "../../data/classroomGlossary";

export function ConceptFlow({items}:{items:string[]}){
  return <div className="classroom-flow" aria-label={items.join(" para ")}>{items.map((item,index)=><div className="classroom-flow-item" key={`${item}-${index}`}><span>{item}</span>{index<items.length-1&&<span aria-hidden="true" className="classroom-flow-arrow">→</span>}</div>)}</div>;
}
export function RevealAnswer({question,answer}:{question:string;answer:string}){
  return <details className="classroom-reveal"><summary><span>{question}</span><strong>Revelar resposta</strong></summary><p>{answer}</p></details>;
}
export function DemoButton({children,onClick,busy=false,disabled=false,busyText="Processando dados..."}:{children:ReactNode;onClick:()=>void;busy?:boolean;disabled?:boolean;busyText?:string}){
  return <button type="button" className="classroom-button" onClick={onClick} disabled={busy||disabled}>{busy?busyText:children}</button>;
}
export function ComparisonPanel({left,right}:{left:{title:string;body:ReactNode};right:{title:string;body:ReactNode}}){
  return <div className="classroom-grid-2"><article className="classroom-panel"><h3>{left.title}</h3>{left.body}</article><article className="classroom-panel"><h3>{right.title}</h3>{right.body}</article></div>;
}
export function DemoLink({to,children}:{to:string;children:ReactNode}){
  return <Link className="classroom-link" to={to}>{children} ↗</Link>;
}
export function ResultError({message,onRetry}:{message:string;onRetry?:()=>void}){return message?<div className="classroom-error" role="alert"><p>{message}</p>{onRetry&&<button type="button" onClick={onRetry}>Tentar novamente</button>}</div>:null}

export function ConceptExplanation({title,simple,everyday,health,term,more}:{title:string;simple:string;everyday?:string;health?:string;term?:string;more?:string}){
  return <article className="classroom-concept"><p className="classroom-kicker">O QUE É?</p><h3>{title}</h3><p>{simple}</p>{everyday&&<p><strong>Exemplo cotidiano: </strong>{everyday}</p>}{health&&<p><strong>Exemplo na saúde: </strong>{health}</p>}{term&&<p className="classroom-term">Nome usado em IA: <strong>{term}</strong> <TermHelp term={term}/></p>}{more&&<details><summary>Quero saber mais</summary><p>{more}</p></details>}</article>;
}
export function TermHelp({term}:{term:string}){
  const [open,setOpen]=useState(false);
  const [technical,setTechnical]=useState(false);
  const entry=glossaryByTerm.get(term.toLocaleLowerCase("pt-BR"));
  if(!entry)return null;
  return <span className="classroom-help"><button type="button" aria-label={`O que é ${term}?`} title={`O que é ${term}?`} aria-expanded={open} onClick={()=>setOpen(value=>!value)}>?</button>{open&&<span className="classroom-help-popover" role="note"><strong>{entry.term}</strong><span>{entry.simple}</span>{entry.technical&&<><button type="button" className="classroom-help-more" aria-expanded={technical} onClick={()=>setTechnical(value=>!value)}>Ver explicação técnica</button>{technical&&<span>{entry.technical}</span>}</>}</span>}</span>;
}
export function LearningSummary({items}:{items:string[]}){return <div className="classroom-summary"><strong>O que aprendemos?</strong><ul>{items.slice(0,3).map(item=><li key={item}>{item}</li>)}</ul></div>}
export function GuidedActivity({goal,action,observe,meaning,done}:{goal:string;action:string;observe:string;meaning:string;done?:boolean}){
  return <div className="classroom-guided"><div><b>O que vamos fazer?</b><span>{goal}</span></div><div><b>O que você precisa fazer?</b><span>{action}</span></div><div><b>O que observar?</b><span>{observe}</span></div><div><b>O que significa?</b><span>{meaning}</span></div><p>{done?"✓ Você executou esta demonstração. Pode avançar ou experimentar novamente.":"Experimente antes de continuar. Você também pode pular esta etapa."}</p></div>;
}
export function GlossaryList({compact=false}:{compact?:boolean}){
  const [search,setSearch]=useState("");
  const filtered=classroomGlossary.filter(entry=>entry.term.toLocaleLowerCase("pt-BR").includes(search.toLocaleLowerCase("pt-BR")));
  return <div className="classroom-glossary"><label>Buscar termo <input value={search} onChange={event=>setSearch(event.target.value)} placeholder="Ex.: probabilidade"/></label><div className="classroom-glossary-list">{filtered.map(entry=><details key={entry.term} open={!compact&&filtered.length===1}><summary>{entry.term}</summary><p>{entry.simple}</p>{entry.technical&&<details><summary>Ver explicação técnica</summary><p>{entry.technical}</p></details>}</details>)}</div>{!filtered.length&&<p>Nenhum termo encontrado.</p>}</div>;
}
