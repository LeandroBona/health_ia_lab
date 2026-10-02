import test from "node:test";
import assert from "node:assert/strict";
import { calculateAngle, anglesFromPose, compareSides, MovementCounter, isReliable } from "../src/vision/geometry.ts";
import { buildSession, readSessions, saveSession, sampleFromAngles } from "../src/vision/session.ts";

test("ângulos vetoriais cobrem 0–180 graus e vértice degenerado", () => {
  assert.equal(calculateAngle({x:0,y:1},{x:0,y:0},{x:1,y:0}),90);
  assert.equal(calculateAngle({x:-1,y:0},{x:0,y:0},{x:1,y:0}),180);
  assert.equal(calculateAngle({x:1,y:0},{x:0,y:0},{x:1,y:0}),0);
  assert.equal(calculateAngle({x:0,y:0},{x:0,y:0},{x:1,y:0}),null);
});

test("confiança insuficiente omite ângulos e os lados anatômicos não trocam no espelho", () => {
  const points=Array.from({length:33},()=>({x:0.5,y:0.5,visibility:1}));
  points[11]={x:0.2,y:0.2,visibility:1};points[13]={x:0.2,y:0.4,visibility:1};points[15]={x:0.4,y:0.4,visibility:1};
  points[12]={x:0.8,y:0.2,visibility:1};points[14]={x:0.8,y:0.4,visibility:1};points[16]={x:0.6,y:0.4,visibility:1};
  const angles=anglesFromPose(points,640,480);
  assert.equal(angles.leftElbow,90);
  assert.equal(angles.rightElbow,90);
  assert.equal(compareSides(angles).elbows,0);
  const mirrored=points.map(point=>({...point,x:1-point.x}));
  assert.equal(anglesFromPose(mirrored,640,480).leftElbow,90);
  points[15].visibility=0.1;
  assert.equal(anglesFromPose(points,640,480).leftElbow,null);
  assert.equal(isReliable(points[15]),false);
});

test("contagem com histerese exige flexão e retorno", () => {
  const counter=new MovementCounter();
  for(const angle of [170,130,90,95,110,145,151,null,140,80,160])counter.update(angle);
  assert.equal(counter.count,2);
  counter.reset();
  for(const angle of [90,null,170])counter.update(angle);
  assert.equal(counter.count,0);
  counter.reset();assert.equal(counter.count,0);
  assert.throws(()=>new MovementCounter(150,100));
});

test("sessão salva somente métricas numéricas após comando explícito", () => {
  const memory=new Map();
  globalThis.localStorage={getItem:key=>memory.get(key)??null,setItem:(key,value)=>memory.set(key,value)};
  const angles={leftElbow:90,rightElbow:100,leftKnee:null,rightKnee:null};
  const sample=sampleFromAngles(0.1,angles,1);
  const session=buildSession([sample],"leftElbow","2026-01-01T00:00:00.000Z");
  assert.equal(session.summary.leftElbow,90);
  assert.equal(session.summary.leftKnee,null);
  assert.equal(readSessions().length,0);
  saveSession(session);
  assert.equal(readSessions().length,1);
  const json=[...memory.values()][0];
  assert.ok(!json.includes("image")&&!json.includes("video")&&!json.includes("landmark"));
});
