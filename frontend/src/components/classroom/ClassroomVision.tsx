import { useCallback, useEffect, useRef, useState } from "react";
import { MediaPipePoseService } from "../../vision/poseService";
import { anglesFromPose, calculateAngle, compareSides, CONNECTIONS, isReliable, MovementCounter } from "../../vision/geometry";
import type { Angles, Point } from "../../vision/geometry";

const empty:Angles={leftElbow:null,rightElbow:null,leftKnee:null,rightKnee:null};
type Camera = {deviceId:string;label:string};
function deadline<T>(task:Promise<T>,ms:number,message:string):Promise<T>{let timer:number|undefined;return Promise.race([task,new Promise<T>((_,reject)=>{timer=window.setTimeout(()=>reject(new Error(message)),ms)})]).finally(()=>window.clearTimeout(timer))}
function draw(canvas:HTMLCanvasElement,points:Point[],width:number,height:number){
  if(canvas.width!==width)canvas.width=width;if(canvas.height!==height)canvas.height=height;
  const ctx=canvas.getContext("2d");if(!ctx)return;ctx.clearRect(0,0,width,height);
  ctx.strokeStyle="#22d3ee";ctx.lineWidth=5;ctx.lineCap="round";
  for(const [a,b] of CONNECTIONS){if(!isReliable(points[a])||!isReliable(points[b]))continue;ctx.beginPath();ctx.moveTo(points[a].x*width,points[a].y*height);ctx.lineTo(points[b].x*width,points[b].y*height);ctx.stroke()}
  ctx.fillStyle="#fbbf24";
  for(const index of [0,11,12,13,14,15,16,23,24,25,26,27,28]){const point=points[index];if(!isReliable(point))continue;ctx.beginPath();ctx.arc(point.x*width,point.y*height,6,0,2*Math.PI);ctx.fill()}
}
export function ClassroomVision(){
  const videoRef=useRef<HTMLVideoElement|null>(null),canvasRef=useRef<HTMLCanvasElement|null>(null),streamRef=useRef<MediaStream|null>(null),serviceRef=useRef<MediaPipePoseService|null>(null),frameRef=useRef<number|undefined>(undefined),counterRef=useRef(new MovementCounter()),generationRef=useRef(0);
  const [loading,setLoading]=useState(false),[active,setActive]=useState(false),[error,setError]=useState(""),[staticMode,setStaticMode]=useState(false),[angles,setAngles]=useState<Angles>(empty),[count,setCount]=useState(0),[shoulder,setShoulder]=useState<number|null>(null),[kneePoint,setKneePoint]=useState<Point|null>(null);
  const [devices,setDevices]=useState<Camera[]>([]),[deviceId,setDeviceId]=useState(""),[identifying,setIdentifying]=useState(false);
  const refreshDevices=useCallback(async()=>{
    if(!navigator.mediaDevices?.enumerateDevices)return;
    try{
      const cameras=(await navigator.mediaDevices.enumerateDevices()).filter(item=>item.kind==="videoinput"&&item.deviceId).map((item,index)=>({deviceId:item.deviceId,label:item.label||`Câmera ${index+1}`}));
      setDevices(cameras);
      setDeviceId(current=>current&&!cameras.some(camera=>camera.deviceId===current)?"":current);
    }catch{setError("Não foi possível listar as câmeras. Ainda é possível tentar a câmera padrão.")}
  },[]);
  useEffect(()=>{void refreshDevices();const update=()=>{void refreshDevices()};navigator.mediaDevices?.addEventListener?.("devicechange",update);return()=>navigator.mediaDevices?.removeEventListener?.("devicechange",update)},[refreshDevices]);
  async function identifyDevices(){
    if(!navigator.mediaDevices?.getUserMedia){setError("Câmera indisponível neste navegador.");return}
    setIdentifying(true);setError("");let temporary:MediaStream|null=null;
    try{
      if(!streamRef.current)temporary=await navigator.mediaDevices.getUserMedia({audio:false,video:true});
      await refreshDevices();
    }catch(exception){setError(exception instanceof DOMException&&exception.name==="NotAllowedError"?"Permissão da câmera negada. Verifique as permissões do navegador e tente novamente.":"Não foi possível identificar as câmeras disponíveis.")}
    finally{temporary?.getTracks().forEach(track=>track.stop());setIdentifying(false)}
  }
  const stop=useCallback(()=>{generationRef.current++;if(frameRef.current!==undefined)cancelAnimationFrame(frameRef.current);frameRef.current=undefined;streamRef.current?.getTracks().forEach(track=>track.stop());streamRef.current=null;serviceRef.current?.close();serviceRef.current=null;if(videoRef.current){videoRef.current.pause();videoRef.current.srcObject=null}setActive(false);setLoading(false);setAngles(empty);setShoulder(null);setKneePoint(null);canvasRef.current?.getContext("2d")?.clearRect(0,0,canvasRef.current.width,canvasRef.current.height)},[]);
  useEffect(()=>()=>stop(),[stop]);
  useEffect(()=>{const hide=()=>{if(document.hidden)stop()};document.addEventListener("visibilitychange",hide);return()=>document.removeEventListener("visibilitychange",hide)},[stop]);
  async function start(chosen=deviceId){stop();setStaticMode(false);setError("");setLoading(true);const generation=generationRef.current;try{
    if(!navigator.mediaDevices?.getUserMedia)throw new Error("Câmera indisponível neste navegador.");
    const mediaRequest=navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:960},height:{ideal:720},deviceId:chosen?{exact:chosen}:undefined,facingMode:chosen?undefined:"user"}});
    void mediaRequest.then(lateStream=>{if(generation!==generationRef.current)lateStream.getTracks().forEach(track=>track.stop())}).catch(()=>{});
    const stream=await deadline(mediaRequest,12000,"A câmera não respondeu. Use a demonstração visual ou tente novamente.");
    if(generation!==generationRef.current){stream.getTracks().forEach(track=>track.stop());return}streamRef.current=stream;
    const video=videoRef.current;if(!video)throw new Error("Prévia indisponível.");video.srcObject=stream;await deadline(video.play(),12000,"A prévia da câmera não iniciou.");
    void refreshDevices();
    const service=new MediaPipePoseService();serviceRef.current=service;const initializing=service.initialize();void initializing.then(()=>{if(generation!==generationRef.current)service.close()}).catch(()=>{});await deadline(initializing,20000,"O modelo local não carregou. Use a demonstração visual.");
    if(generation!==generationRef.current){service.close();stream.getTracks().forEach(track=>track.stop());return}
    setActive(true);setLoading(false);counterRef.current.reset();setCount(0);
    let last=0;const loop=(now:number)=>{if(generation!==generationRef.current)return;const video=videoRef.current,canvas=canvasRef.current;if(video&&canvas&&video.readyState>=2&&now-last>100){last=now;try{const points=service.estimate(video,now);const next=points.length?anglesFromPose(points,video.videoWidth,video.videoHeight):empty;draw(canvas,points,video.videoWidth,video.videoHeight);setAngles(next);setCount(counterRef.current.update(next.leftKnee));setKneePoint(isReliable(points[25])?points[25]:null);const [elbow,shoulderPoint,hip]=[points[13],points[11],points[23]];const scale=(point:Point)=>({x:point.x*video.videoWidth,y:point.y*video.videoHeight});setShoulder(isReliable(elbow)&&isReliable(shoulderPoint)&&isReliable(hip)?calculateAngle(scale(elbow),scale(shoulderPoint),scale(hip)):null)}catch{setError("A análise local foi interrompida.");stop();return}}frameRef.current=requestAnimationFrame(loop)};frameRef.current=requestAnimationFrame(loop);
  }catch(exception){if(generation!==generationRef.current)return;let message=exception instanceof Error?exception.message:"Câmera indisponível.";if(exception instanceof DOMException){if(exception.name==="NotAllowedError")message="Permissão da câmera negada. Use a demonstração visual ou pule esta etapa.";else if(exception.name==="NotFoundError"||exception.name==="OverconstrainedError")message="A câmera selecionada não foi encontrada. Escolha outra e tente novamente.";else if(exception.name==="NotReadableError")message="A câmera está ocupada por outro aplicativo ou indisponível."}setError(message);stop()}}
  const difference=compareSides(angles).knees;
  return <div className="classroom-vision"><div className="classroom-actions"><label className="classroom-camera-select">Câmera<select value={deviceId} disabled={loading||identifying} onChange={event=>{const next=event.target.value;setDeviceId(next);if(active)void start(next)}}><option value="">Padrão do navegador</option>{devices.map(camera=><option key={camera.deviceId} value={camera.deviceId}>{camera.label}</option>)}</select></label><button type="button" className="classroom-link" disabled={loading||identifying} onClick={()=>void identifyDevices()}>{identifying?"Identificando...":"Identificar câmeras"}</button><button type="button" className="classroom-button" disabled={loading||active||identifying} onClick={()=>void start()}>{loading?"Carregando modelo local...":"Abrir câmera"}</button><button type="button" className="classroom-link" disabled={!active} onClick={stop}>Fechar câmera</button><button type="button" className="classroom-link" onClick={()=>{stop();setStaticMode(true)}}>Usar demonstração visual</button></div><p className="classroom-small">“Identificar câmeras” pode solicitar permissão e ativa a câmera por um instante para listar as fontes. Notebook, USB e iPhone aparecem quando o navegador os disponibiliza. A câmera do iPhone requer a Câmera de Continuidade ativa no sistema. A troca de câmera interrompe a captura anterior.</p>{error&&<p className="classroom-error" role="alert">{error}</p>}<div className="classroom-grid-2"><div className="classroom-camera"><video ref={videoRef} muted playsInline autoPlay style={{display:active?"block":"none",transform:"scaleX(-1)"}}/><canvas ref={canvasRef} aria-label="Esqueleto estimado" style={{display:active?"block":"none",transform:"scaleX(-1)"}}/>{!active&&(staticMode?<div className="classroom-static-pose"><svg width="220" height="250" viewBox="0 0 220 250" role="img" aria-label="Esquema estático de pontos corporais"><g stroke="#22d3ee" strokeWidth="5" fill="none"><path d="M110 38 L70 70 L55 120 M110 38 L150 70 L165 120 M70 70 L80 145 L70 198 L52 232 M150 70 L140 145 L150 198 L168 232 M80 145 L140 145"/></g>{[[110,38],[70,70],[150,70],[55,120],[165,120],[80,145],[140,145],[70,198],[150,198],[52,232],[168,232]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r="6" fill="#fbbf24"/>)}</svg><p>Esquema estático · webcam desativada</p></div>:<p>Câmera desativada. Nenhuma imagem é enviada ao backend.</p>)}</div><div className="classroom-panel"><h3>Métricas derivadas</h3><p>Joelho esquerdo: <strong>{angles.leftKnee===null?"—":`${angles.leftKnee.toFixed(1)}°`}</strong></p><p>Joelho direito: <strong>{angles.rightKnee===null?"—":`${angles.rightKnee.toFixed(1)}°`}</strong></p><p>Diferença: <strong>{difference===null?"—":`${difference.toFixed(1)}°`}</strong></p><p>Ombro esquerdo: <strong>{shoulder===null?"—":`${shoulder.toFixed(1)}°`}</strong></p><p>Joelho esquerdo na imagem: <strong>{kneePoint?`X ${kneePoint.x.toFixed(2)} · Y ${kneePoint.y.toFixed(2)}`:"—"}</strong></p><p>Movimentos contados: <strong>{count}</strong></p><div className="classroom-tip"><strong>Desafio opcional:</strong> observe três ciclos de flexão e retorno do joelho. Levante um braço para observar o ângulo do ombro.</div>{count>=3&&<p className="classroom-statement">O sistema contou três ciclos de movimento.</p>}<small>Valores 2D aproximados e sem interpretação clínica.</small></div></div></div>;
}
