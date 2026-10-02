import { analysisService } from "../services/analysisService";
import { useCallback, useEffect, useRef, useState } from "react";
import { Line, LineChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { VisionHeader, VisionNav, VisionNotice } from "../components/vision/Shared";
import { anglesFromPose, compareSides, CONNECTIONS, isReliable, JOINT_LABELS, LANDMARKS, MovementCounter } from "../vision/geometry";
import type { Angles, Joint, Point } from "../vision/geometry";
import { MediaPipePoseService } from "../vision/poseService";
import { buildSession, MAX_SAMPLES, readSessions, sampleFromAngles, saveSession } from "../vision/session";
import type { MetricSample } from "../vision/session";

const EMPTY_ANGLES: Angles = {leftElbow:null,rightElbow:null,leftKnee:null,rightKnee:null};
const JOINTS: Joint[] = ["leftElbow","rightElbow","leftKnee","rightKnee"];
type Camera = {deviceId:string;label:string};
function drawPose(canvas:HTMLCanvasElement, points:Point[], width:number, height:number, selected:Joint){
  if(canvas.width!==width)canvas.width=width;
  if(canvas.height!==height)canvas.height=height;
  const ctx=canvas.getContext("2d");if(!ctx)return;
  ctx.clearRect(0,0,width,height);
  ctx.lineCap="round";ctx.lineJoin="round";ctx.lineWidth=Math.max(3,width/180);ctx.strokeStyle="#2dd4bf";
  for(const [a,b] of CONNECTIONS){if(!isReliable(points[a])||!isReliable(points[b]))continue;ctx.beginPath();ctx.moveTo(points[a].x*width,points[a].y*height);ctx.lineTo(points[b].x*width,points[b].y*height);ctx.stroke()}
  for(const item of LANDMARKS){const point=points[item.index];if(!isReliable(point))continue;ctx.beginPath();ctx.arc(point.x*width,point.y*height,Math.max(4,width/170),0,Math.PI*2);ctx.fillStyle="#f97316";ctx.fill();ctx.strokeStyle="#0f172a";ctx.lineWidth=2;ctx.stroke()}
  const vertexIndex:Record<Joint,number>={leftElbow:13,rightElbow:14,leftKnee:25,rightKnee:26};
  const vertex=points[vertexIndex[selected]];
  const triplet:Record<Joint,[number,number,number]>={leftElbow:[11,13,15],rightElbow:[12,14,16],leftKnee:[23,25,27],rightKnee:[24,26,28]};
  const [a,b,c]=triplet[selected];
  if([a,b,c].every(index=>isReliable(points[index]))){
    const start=points[a],end=points[c],mid=points[b];
    ctx.strokeStyle="#facc15";ctx.lineWidth=Math.max(4,width/130);
    for(const point of [start,end]){ctx.beginPath();ctx.moveTo(mid.x*width,mid.y*height);ctx.lineTo(point.x*width,point.y*height);ctx.stroke()}
    ctx.beginPath();ctx.arc(vertex.x*width,vertex.y*height,Math.max(13,width/65),0,Math.PI*2);ctx.stroke();
  }
}

export function VisionLabPage(){
  const videoRef=useRef<HTMLVideoElement|null>(null),canvasRef=useRef<HTMLCanvasElement|null>(null),streamRef=useRef<MediaStream|null>(null),serviceRef=useRef<MediaPipePoseService|null>(null);
  const frameRef=useRef<number|undefined>(undefined),generationRef=useRef(0),lastFrameRef=useRef(0),lastVideoTimeRef=useRef(-1),startRef=useRef(""),counterRef=useRef(new MovementCounter()),selectedRef=useRef<Joint>("leftElbow"),samplesRef=useRef<MetricSample[]>([]);
  const [running,setRunning]=useState(false),[loading,setLoading]=useState(false),[hasStream,setHasStream]=useState(false),[error,setError]=useState(""),[status,setStatus]=useState("Câmera desativada");
  const [devices,setDevices]=useState<Camera[]>([]),[deviceId,setDeviceId]=useState(""),[identifying,setIdentifying]=useState(false),[points,setPoints]=useState<Point[]>([]),[angles,setAngles]=useState<Angles>(EMPTY_ANGLES),[selected,setSelected]=useState<Joint>("leftElbow"),[movements,setMovements]=useState(0),[samples,setSamples]=useState<MetricSample[]>([]),[savedCount,setSavedCount]=useState(0);

  const refreshDevices=useCallback(async()=>{
    if(!navigator.mediaDevices?.enumerateDevices)return;
    try{const found=(await navigator.mediaDevices.enumerateDevices()).filter(item=>item.kind==="videoinput"&&item.deviceId).map((item,index)=>({deviceId:item.deviceId,label:item.label||`Câmera ${index+1}`}));setDevices(found);setDeviceId(current=>current&&!found.some(camera=>camera.deviceId===current)?"":current)}catch{setError("Não foi possível listar as câmeras. Ainda é possível tentar a câmera padrão.")}
  },[]);
  useEffect(()=>{void refreshDevices();const handler=()=>{void refreshDevices()};navigator.mediaDevices?.addEventListener?.("devicechange",handler);return()=>navigator.mediaDevices?.removeEventListener?.("devicechange",handler)},[refreshDevices]);
  async function identifyDevices(){
    if(!navigator.mediaDevices?.getUserMedia){setError("Este navegador não oferece acesso à câmera. Abra o projeto em localhost ou HTTPS.");return}
    setIdentifying(true);setError("");let temporary:MediaStream|null=null;
    try{
      if(!streamRef.current)temporary=await navigator.mediaDevices.getUserMedia({audio:false,video:true});
      await refreshDevices();
    }catch(exception){setError(exception instanceof DOMException&&exception.name==="NotAllowedError"?"Permissão da câmera negada. Autorize o acesso no navegador e tente novamente.":"Não foi possível identificar as câmeras disponíveis.")}
    finally{temporary?.getTracks().forEach(track=>track.stop());setIdentifying(false)}
  }

  const stopCamera=useCallback(()=>{
    generationRef.current+=1;
    if(frameRef.current!==undefined)cancelAnimationFrame(frameRef.current);
    frameRef.current=undefined;
    streamRef.current?.getTracks().forEach(track=>track.stop());streamRef.current=null;
    if(videoRef.current){videoRef.current.pause();videoRef.current.srcObject=null}
    serviceRef.current?.close();serviceRef.current=null;
    const canvas=canvasRef.current;if(canvas)canvas.getContext("2d")?.clearRect(0,0,canvas.width,canvas.height);
    setRunning(false);setLoading(false);setHasStream(false);setStatus("Câmera desativada");setPoints([]);setAngles(EMPTY_ANGLES);
  },[]);
  useEffect(()=>()=>stopCamera(),[stopCamera]);
  useEffect(()=>{
    const hidden=()=>{if(document.hidden)stopCamera()};
    const leaving=()=>stopCamera();
    document.addEventListener("visibilitychange",hidden);
    window.addEventListener("pagehide",leaving);
    return()=>{document.removeEventListener("visibilitychange",hidden);window.removeEventListener("pagehide",leaving)};
  },[stopCamera]);

  async function startCamera(chosen=deviceId){
    stopCamera();setLoading(true);setError("");setStatus("Solicitando acesso à câmera...");
    const generation=generationRef.current;
    try{
      if(!navigator.mediaDevices?.getUserMedia)throw new Error("Este navegador não oferece acesso à câmera. Abra o projeto em localhost ou HTTPS.");
      const stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{deviceId:chosen?{exact:chosen}:undefined,width:{ideal:960},height:{ideal:720},facingMode:chosen?undefined:"user"}});
      if(generation!==generationRef.current){stream.getTracks().forEach(track=>track.stop());return}
      streamRef.current=stream;
      const video=videoRef.current;if(!video)throw new Error("Prévia da câmera indisponível.");
      video.srcObject=stream;setHasStream(true);await video.play();
      setStatus("Carregando modelo local de pose...");
      const service=new MediaPipePoseService();serviceRef.current=service;await service.initialize();
      if(generation!==generationRef.current){service.close();stream.getTracks().forEach(track=>track.stop());return}
      await refreshDevices();setRunning(true);setLoading(false);setStatus("Pose em processamento local");
      startRef.current=new Date().toISOString();lastFrameRef.current=0;lastVideoTimeRef.current=-1;counterRef.current.reset();setMovements(0);samplesRef.current=[];setSamples([]);
      const loop=(now:number)=>{
        if(generation!==generationRef.current)return;
        const activeVideo=videoRef.current,canvas=canvasRef.current;
        if(activeVideo&&canvas&&activeVideo.readyState>=2&&now-lastFrameRef.current>=100&&activeVideo.currentTime!==lastVideoTimeRef.current){
          lastFrameRef.current=now;lastVideoTimeRef.current=activeVideo.currentTime;
          try{
            const found=service.estimate(activeVideo,now);
            const width=activeVideo.videoWidth,height=activeVideo.videoHeight;
            const next=found.length?anglesFromPose(found,width,height):EMPTY_ANGLES;
            drawPose(canvas,found,width,height,selectedRef.current);
            setPoints(found);
            setAngles(next);
            const count=counterRef.current.update(next[selectedRef.current]);setMovements(count);
            if(found.length){
              const sample=sampleFromAngles(Math.round((Date.now()-Date.parse(startRef.current))/100)/10,next,count);
              samplesRef.current=[...samplesRef.current.slice(-(MAX_SAMPLES-1)),sample];
              setSamples(samplesRef.current.slice(-100));
            }
          }catch(e){setError(e instanceof Error?e.message:"Falha ao processar a pose.");stopCamera();return}
        }
        frameRef.current=requestAnimationFrame(loop);
      };
      frameRef.current=requestAnimationFrame(loop);
    }catch(e){
      if(generation!==generationRef.current)return;
      let reason=e instanceof Error?e.message:String(e);
      if(e instanceof DOMException){
        if(e.name==="NotAllowedError"||e.name==="PermissionDeniedError")reason="Permissão da câmera negada. Autorize o acesso nas configurações do navegador e tente novamente.";
        else if(e.name==="NotFoundError"||e.name==="OverconstrainedError")reason="A câmera selecionada não foi encontrada. Escolha outro dispositivo e tente novamente.";
        else if(e.name==="NotReadableError")reason="A câmera está ocupada por outro aplicativo ou indisponível no momento.";
      }
      setError(reason);
      stopCamera();
    }
  }

  function changeJoint(value:Joint){selectedRef.current=value;setSelected(value);counterRef.current.reset();setMovements(0);samplesRef.current=[];setSamples([]);startRef.current=new Date().toISOString()}
  function saveMetrics(){
    if(!samplesRef.current.length){setError("Capture ao menos uma amostra antes de registrar métricas.");return}
    try{const session=buildSession(samplesRef.current,selectedRef.current,startRef.current);saveSession(session);setSavedCount(readSessions().length);setError("");setStatus("Métricas numéricas salvas neste navegador. A câmera continua local.");void analysisService.recordVisionSession(session).catch(()=>setStatus("Métricas locais salvas. O histórico central está indisponível."))}
    catch{setError("Não foi possível salvar as métricas no armazenamento deste navegador.")}
  }
  const differences=compareSides(angles);
  const confidence=(point:Point|undefined)=>point?Math.round(Math.min(point.visibility??1,point.presence??1)*100):null;
  return <div className="space-y-6"><VisionHeader title="Laboratório de Visão Computacional" subtitle="Webcam, landmarks, ângulos e séries temporais calculados no seu navegador."/><VisionNav/><VisionNotice/>
    <section className="surface-card p-6"><h2 className="section-title">Controles da câmera</h2><p className="mt-2 text-sm text-slate-600">A câmera inicia apenas pelo botão abaixo. Vídeo e imagens não são salvos nem enviados ao servidor. A primeira ativação carrega arquivos do modelo servidos localmente pelo projeto.</p><p className="mt-2 text-xs text-slate-600">Segundo o aviso de privacidade do MediaPipe, a biblioteca pode transmitir ao Google métricas de uso e desempenho, sem enviar imagens ou vídeo.</p><div className="mt-4 flex flex-wrap items-end gap-3"><label className="text-sm font-semibold">Câmera<select className="field mt-1 block min-w-52" value={deviceId} disabled={loading||identifying} onChange={e=>{const next=e.target.value;setDeviceId(next);if(running)void startCamera(next)}}><option value="">Padrão do navegador</option>{devices.map(item=><option value={item.deviceId} key={item.deviceId}>{item.label}</option>)}</select></label><button className="btn-secondary" disabled={loading||identifying} onClick={()=>void identifyDevices()}>{identifying?"Identificando...":"Identificar câmeras"}</button><button className="btn-primary" disabled={loading||identifying} onClick={()=>void startCamera()}>{loading?"Ativando...":"Ativar câmera"}</button><button className="btn-secondary" disabled={!running&&!loading} onClick={stopCamera}>Desativar câmera</button></div><p className="mt-3 text-sm text-slate-600">“Identificar câmeras” pode solicitar permissão e ativa a câmera por um instante para listar as fontes. Notebook, USB e iPhone aparecem quando o navegador os disponibiliza. Para usar o iPhone, ative a Câmera de Continuidade no sistema.</p><p className="mt-3 text-sm font-semibold" role="status">{status}</p>{error&&<p className="mt-2 rounded-lg bg-rose-50 p-3 text-sm text-rose-700" role="alert">{error}</p>}</section>
    <section className="grid gap-5 xl:grid-cols-[1.45fr_0.55fr]"><div className="surface-card overflow-hidden p-4"><div className="relative mx-auto w-full max-w-4xl overflow-hidden rounded-xl bg-slate-950" style={{aspectRatio:"4 / 3"}}>{!hasStream&&<div className="absolute inset-0 grid place-items-center text-center text-sm text-slate-300">Câmera desativada. Clique em “Ativar câmera” para iniciar.</div>}<video ref={videoRef} muted playsInline autoPlay className="absolute inset-0 h-full w-full object-contain" style={{display:hasStream?"block":"none",transform:"scaleX(-1)"}}/><canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full object-contain" style={{display:hasStream?"block":"none",transform:"scaleX(-1)"}} aria-label="Sobreposição de landmarks e esqueleto"/>{hasStream&&<div className="pointer-events-none absolute left-3 top-3 rounded-lg bg-slate-950/80 px-3 py-2 text-sm font-bold text-white">{JOINT_LABELS[selected]} · {angles[selected]===null?"—":`${angles[selected]?.toFixed(1)}°`}</div>}</div><p className="mt-3 text-xs text-slate-600">Prévia espelhada. Esquerdo e direito referem-se aos lados anatômicos estimados pelo modelo, sem trocar os rótulos.</p></div><aside className="surface-card p-5"><h2 className="section-title">Landmarks</h2><p className="mt-2 text-xs text-slate-600">Confiança de visibilidade do ponto. Abaixo de 55%, o ângulo relacionado não é calculado.</p><div className="mt-4 max-h-96 space-y-2 overflow-y-auto text-sm">{LANDMARKS.map(item=><div className="flex justify-between gap-2 border-b border-slate-100 pb-1" key={item.index}><span>{item.label}</span><strong>{confidence(points[item.index])===null?"—":`${confidence(points[item.index])}%`}</strong></div>)}</div></aside></section>
    <section className="surface-card p-6"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="section-title">Ângulos articulares</h2><p className="mt-1 text-sm text-slate-600">Calculados em 2D pela geometria vetorial dos pontos visíveis. Uma perspectiva diferente da câmera altera os valores.</p></div><label className="text-sm font-semibold">Articulação para contagem<select className="field mt-1 block" value={selected} onChange={e=>changeJoint(e.target.value as Joint)}>{JOINTS.map(joint=><option value={joint} key={joint}>{JOINT_LABELS[joint]}</option>)}</select></label></div><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{JOINTS.map(joint=><div className="rounded-xl bg-sky-50 p-4" key={joint}><p className="text-sm font-bold">{JOINT_LABELS[joint]}</p><p className="mt-2 text-2xl font-extrabold">{angles[joint]===null?"—":`${angles[joint]?.toFixed(1)}°`}</p>{running&&angles[joint]===null&&<p className="mt-1 text-xs text-slate-600">Articulação não detectada com confiança suficiente.</p>}</div>)}</div><div className="mt-4 grid gap-3 text-sm sm:grid-cols-3"><p className="rounded-lg bg-slate-50 p-4">Diferença entre cotovelos: <strong>{differences.elbows===null?"—":`${differences.elbows.toFixed(1)}°`}</strong></p><p className="rounded-lg bg-slate-50 p-4">Diferença entre joelhos: <strong>{differences.knees===null?"—":`${differences.knees.toFixed(1)}°`}</strong></p><p className="rounded-lg bg-slate-50 p-4">Ciclos contados: <strong>{movements}</strong></p></div><p className="mt-3 text-xs text-slate-600">Contagem didática: um ciclo ocorre quando o ângulo selecionado passa abaixo de 100° e depois acima de 150°. Esses limites são apenas parâmetros do exemplo matemático.</p></section>
    <section className="surface-card p-6"><h2 className="section-title">Acompanhamento temporal</h2><p className="mt-2 text-sm text-slate-600">Últimas 100 amostras de ângulos em graus; até {MAX_SAMPLES} amostras numéricas ficam na sessão atual. Pontos com baixa confiança aparecem sem valor.</p><div className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={samples}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="t" unit=" s"/><YAxis domain={[0,180]} unit="°"/><Tooltip/><Legend/><Line type="monotone" dataKey="leftElbow" name="Cotovelo esquerdo" stroke="#0284c7" dot={false} connectNulls={false}/><Line type="monotone" dataKey="rightElbow" name="Cotovelo direito" stroke="#e11d48" dot={false} connectNulls={false}/><Line type="monotone" dataKey="leftKnee" name="Joelho esquerdo" stroke="#7c3aed" dot={false} connectNulls={false}/><Line type="monotone" dataKey="rightKnee" name="Joelho direito" stroke="#0f766e" dot={false} connectNulls={false}/></LineChart></ResponsiveContainer></div><div className="mt-4 flex flex-wrap items-center gap-3"><button className="btn-primary" disabled={!samplesRef.current.length} onClick={saveMetrics}>Registrar sessão numérica</button><span className="text-sm text-slate-600">{savedCount} sessão(ões) salva(s) nesta visita. Nenhum vídeo ou imagem é armazenado.</span></div></section>
  </div>;
}
