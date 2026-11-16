/* CERTARE | visualização estrutural conceitual. Sem escala, locação ou medição individual. */
(function(){'use strict';
const cfg=JSON.parse(document.getElementById('certare-config').textContent);
const AX=cfg.estacas.previstas_por_eixo,HIST=cfg.estacas.historicas_por_eixo;
let selected={kind:'eixo',index:7,service:null},layer='todos';
const pad=n=>String(n).padStart(2,'0');
const cv=document.getElementById('bridge4d');if(!cv)return;const ctx=cv.getContext('2d');if(!ctx)return;
let yaw=-.39,tilt=.39,scale=1,drag=null,hit=[],zoomFactor=1,focusX=0,currentView='perspectiva';
const VIEWS={perspectiva:[-.39,.39],lateral:[0,.13],superior:[0,1.48],frontal:[-Math.PI/2,.18]};
const geo={span:78,width:64,waterY:-17};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const axesX=Array.from({length:cfg.eixos},(_,i)=>(i-(cfg.eixos-1)/2)*geo.span);
function projection(pt,W,H){let [x,y,z]=pt;x-=focusX;let X=x*Math.cos(yaw)-z*Math.sin(yaw),Z=x*Math.sin(yaw)+z*Math.cos(yaw);return [W/2+X*scale*.88,H*.53+(-y*Math.cos(tilt)+Z*Math.sin(tilt))*scale*.88-Z*Math.cos(tilt)*scale*.15]}
function cylinder(axisX,z,base,top,r,faces=9){let verts=[];for(let i=0;i<faces;i++){let a=Math.PI*2*i/faces;verts.push([axisX+Math.cos(a)*r,base,z+Math.sin(a)*r])}for(let i=0;i<faces;i++){let a=Math.PI*2*i/faces;verts.push([axisX+Math.cos(a)*r,top,z+Math.sin(a)*r])}let f=[];for(let i=0;i<faces;i++)f.push([i,(i+1)%faces,(i+1)%faces+faces,i+faces]);f.push(Array.from({length:faces},(_,i)=>i+faces));return [verts,f]}
function boxGeom(x,y,z,dx,dy,dz){let a=x-dx/2,b=x+dx/2,c=z-dz/2,d=z+dz/2,e=y-dy/2,f=y+dy/2;return [[[a,e,c],[b,e,c],[b,e,d],[a,e,d],[a,f,c],[b,f,c],[b,f,d],[a,f,d]],[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[4,5,6,7],[0,1,2,3]]]}
function addMesh(scene,verts,faces,color,meta,opacity=1){for(let k=0;k<faces.length;k++){let poly=faces[k].map(i=>verts[i]);scene.push({poly,color,meta,opacity})}}
// Cores por sistema, nunca por estágio. Posições não são individualmente homologadas.
const NEUTRAL={estacas:'#8FA9A4',bloco:'#AABAB4',pilar:'#A3B7AE',travessa:'#789A91',longarina:'#688A86',tabuleiro:'#C6D8CE'};
function colorFor(service){return NEUTRAL[service]||'#AEBEB7'}
let showGround=true;
function buildScene(){
 let objects=[];
 let drawFoundation=layer==='todos'||layer==='fundacoes',drawMeso=layer==='todos'||layer==='meso',drawSuper=layer==='todos'||layer==='super';
 if(showGround){
   addMesh(objects,...boxGeom(0,-27,0,730,1.3,150),'#D5E3DA',null,.13);
   addMesh(objects,...boxGeom(0,-25,0,705,.8,102),'#A8CDCF',null,.14);
 }
 axesX.forEach((x,i)=>{
   let n=i+1,sel={kind:'eixo',index:n},t=AX[i],rows=Math.ceil(t/6);
   if(drawFoundation){
      // Status das estacas é somente agregado por eixo: nenhuma posição é presumida executada.
      let foundationCol=colorFor('estacas');
      for(let j=0;j<t;j++){
        let column=j%6,row=Math.floor(j/6),offset=(row-(rows-1)/2)*5.9,z=(column-2.5)*9;
        addMesh(objects,...cylinder(x+offset,z,-43,-6,1.55,7),foundationCol,{...sel,service:'estacas',individual:false},.88)
      }
      addMesh(objects,...boxGeom(x,-4,0,rows*6+12,6,61),colorFor('bloco'),{...sel,service:'bloco',individual:false},.90)
   }
   if(drawMeso){
      for(let j=0;j<4;j++){let z=-23+j*15.3;addMesh(objects,...boxGeom(x,10,z,4,28,4),colorFor('pilar'),{...sel,service:'pilar',individual:false},.97)}
      addMesh(objects,...boxGeom(x,25,0,8,5,76),colorFor('travessa'),{...sel,service:'travessa',individual:false},.95)
   }
 });
 if(drawSuper)for(let i=0;i<cfg.vaos;i++){
   let cx=(axesX[i]+axesX[i+1])/2,sel={kind:'vao',index:i+1};
   for(let j=0;j<8;j++){let z=-31+j*8.85;addMesh(objects,...boxGeom(cx,31,z,geo.span-2,5,3.0),colorFor('longarina'),{...sel,service:'longarina',individual:false},.95)}
   addMesh(objects,...boxGeom(cx,36,0,geo.span-3,2.5,71),colorFor('tabuleiro'),{...sel,service:'tabuleiro',individual:false},.49)
 }
 return objects
}

function hexToRGB(h){return [1,3,5].map(i=>parseInt(h.slice(i,i+2),16))}
function shadeColor(hex,light){return 'rgb('+hexToRGB(hex).map(v=>Math.round(clamp(v*light,0,255))).join(',')+')'}
function normal(poly){
 if(poly.length<3)return [0,1,0];
 const a=poly[0],b=poly[1],c=poly[2],u=b.map((v,i)=>v-a[i]),v=c.map((w,i)=>w-a[i]);
 const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
 const m=Math.hypot(...n)||1;return n.map(x=>x/m);
}
function pointInPoly(p,poly){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){let a=poly[i],b=poly[j];if(((a[1]>p[1])!==(b[1]>p[1]))&&(p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]))inside=!inside}return inside}
function roundedRect(x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r)}
function backdrop(W,H){
 const grad=ctx.createLinearGradient(0,0,0,H);grad.addColorStop(0,'#F8FBF9');grad.addColorStop(1,'#DDEBE5');ctx.fillStyle=grad;ctx.fillRect(0,0,W,H);
 ctx.save();ctx.strokeStyle='#8DAFA117';ctx.lineWidth=.7;
 const step=W<500?28:38;
 for(let x=(W%step)/2;x<W;x+=step){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke()}
 for(let y=(H%step)/2;y<H;y+=step){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke()}
 ctx.restore();
 const stamp=W<500?'ESTRUTURA / ESQUEMA':'CERTARE  |  VISUALIZAÇÃO ESTRUTURAL';
 ctx.font='700 10px system-ui,Arial';ctx.textAlign='left';ctx.fillStyle='#507568A8';ctx.fillText(stamp,17,25);
 ctx.font='600 10px system-ui,Arial';ctx.textAlign='right';ctx.fillStyle='#507568BB';ctx.fillText('SEM ESCALA',W-16,25);
 ctx.textAlign='left';
}
function labelAt(txt,pt,W,H,active){
 const [x,y]=projection(pt,W,H);if(x<-30||x>W+30||y<20||y>H-14)return;
 ctx.font='700 11px system-ui,Arial';
 const w=Math.max(34,ctx.measureText(txt).width+18),left=x-w/2,top=y-14;
 roundedRect(left,top,w,23,7);ctx.fillStyle=active?'#164D3E':'#FFFFFFE9';ctx.fill();ctx.lineWidth=active?1.4:1;ctx.strokeStyle=active?'#164D3E':'#B6C9BD';ctx.stroke();
 ctx.fillStyle=active?'#FFFFFF':'#355747';ctx.textAlign='center';ctx.fillText(txt,x,y+2);ctx.textAlign='left';
}
function paint(){
 const W=cv.clientWidth,H=cv.clientHeight;if(!W||!H)return;
 const ratio=Math.min(2,window.devicePixelRatio||1);
 if(cv.width!==Math.round(W*ratio)||cv.height!==Math.round(H*ratio)){cv.width=Math.round(W*ratio);cv.height=Math.round(H*ratio)}
 ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,W,H);backdrop(W,H);
 scale=Math.min(W/720,H/430)*1.03*zoomFactor;
 const scenes=buildScene().map(o=>{
  const avg=o.poly.reduce((acc,p)=>acc+( (p[0]-focusX)*Math.sin(yaw)+p[2]*Math.cos(yaw))*Math.cos(tilt)+p[1]*Math.sin(tilt),0)/o.poly.length;
  const n=normal(o.poly);
  const light=clamp(.84+.28*(n[0]*(-.40)+n[1]*.8+n[2]*.35),.57,1.16);
  return {...o,pts:o.poly.map(p=>projection(p,W,H)),depth:avg,light};
 });
 scenes.sort((a,b)=>a.depth-b.depth);
 hit=[];
 for(const o of scenes){
  const active=!!o.meta&&o.meta.kind===selected.kind&&o.meta.index===selected.index&&(!selected.service||o.meta.service===selected.service);
  ctx.beginPath();o.pts.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();
  ctx.globalAlpha=o.opacity;
  ctx.fillStyle=shadeColor(o.color,active?Math.min(1.2,o.light*1.09):o.light);ctx.fill();
  ctx.strokeStyle=active?'#17694D':'#526F6250';
  ctx.lineWidth=active?1.2:.48;ctx.stroke();ctx.globalAlpha=1;
  if(o.meta)hit.push(o);
 }
 if(focusX===0&&zoomFactor<=1.12){
  axesX.forEach((x,i)=>labelAt('E'+pad(i+1),[x,43,-37],W,H,selected.kind==='eixo'&&selected.index===i+1));
 }else if(selected.kind==='eixo'){
  labelAt('E'+pad(selected.index),[axesX[selected.index-1],43,-37],W,H,true);
 }
 ctx.fillStyle='#4D7061';ctx.font='600 10px system-ui,Arial';ctx.textAlign='right';
 ctx.fillText(currentView.toUpperCase()+'  •  MODELO CONCEITUAL',W-15,H-15);ctx.textAlign='left';
}

let onSelect=()=>{};
function applySelection(kind,index,service){selected={kind,index,service};paint();onSelect(kind,index);window.dispatchEvent(new CustomEvent('certare:select',{detail:{kind,index,service}}))}
function screenEvent(ev){let r=cv.getBoundingClientRect();return [ev.clientX-r.left,ev.clientY-r.top]}
cv.addEventListener('pointerdown',ev=>{drag={x:ev.clientX,y:ev.clientY,sx:ev.clientX,sy:ev.clientY};cv.setPointerCapture(ev.pointerId)});
cv.addEventListener('pointermove',ev=>{if(!drag)return;let dx=ev.clientX-drag.x,dy=ev.clientY-drag.y;yaw+=dx*.005;tilt=Math.max(.04,Math.min(1.55,tilt+dy*.003));drag.x=ev.clientX;drag.y=ev.clientY;paint()});
cv.addEventListener('pointercancel',()=>{drag=null});
cv.addEventListener('pointerup',ev=>{if(!drag)return;let d=Math.hypot(ev.clientX-drag.sx,ev.clientY-drag.sy);drag=null;if(d>6)return;let p=screenEvent(ev);for(let i=hit.length-1;i>=0;i--){if(pointInPoly(p,hit[i].pts)){let obj=hit[i].meta;applySelection(obj.kind,obj.index,obj.service);return}}});
cv.addEventListener('wheel',ev=>{ev.preventDefault();zoomFactor=Math.min(2.4,Math.max(.4,zoomFactor*(ev.deltaY>0?.91:1.09)));paint()},{passive:false});
function setView(name){if(!VIEWS[name])return;currentView=name;[yaw,tilt]=VIEWS[name];paint();document.querySelectorAll('[data-model-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.modelView===name)));}
cv.addEventListener('keydown',e=>{
 let ok=true;
 if(e.key==='ArrowLeft')yaw-=.12;
 else if(e.key==='ArrowRight')yaw+=.12;
 else if(e.key==='ArrowUp')tilt=Math.min(1.55,tilt+.10);
 else if(e.key==='ArrowDown')tilt=Math.max(.04,tilt-.10);
 else if(e.key==='+'||e.key==='=')zoomFactor=Math.min(2.4,zoomFactor*1.12);
 else if(e.key==='-')zoomFactor=Math.max(.4,zoomFactor/1.12);
 else if(e.key==='Home'){currentView='perspectiva';[yaw,tilt]=VIEWS.perspectiva;zoomFactor=1;focusX=0;}
 else ok=false;
 if(ok){e.preventDefault();if(e.key==='Home')document.querySelectorAll('[data-model-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.modelView==='perspectiva')));paint()}
});
document.querySelectorAll('[data-model-view]').forEach(el=>el.addEventListener('click',()=>setView(el.dataset.modelView)));
const modelContainer=document.querySelector('.card:has(#bridge4d)');
const presentationBtn=document.getElementById('modelPresentation');
function togglePresentation(force){
 const active=typeof force==='boolean'?force:!modelContainer?.classList.contains('model-presentation');
 if(!modelContainer)return;
 modelContainer.classList.toggle('model-presentation',active);
 document.body.classList.toggle('presentation-open',active);
 if(presentationBtn){presentationBtn.setAttribute('aria-pressed',String(active));presentationBtn.textContent=active?'Fechar apresentação':'Ampliar modelo'}
 requestAnimationFrame(paint);
}
presentationBtn?.addEventListener('click',()=>togglePresentation());
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&modelContainer?.classList.contains('model-presentation'))togglePresentation(false)});
const actions={zoomIn:()=>{zoomFactor=Math.min(2.4,zoomFactor*1.15);paint()},zoomOut:()=>{zoomFactor=Math.max(.4,zoomFactor/1.15);paint()},reset:()=>{focusX=0;zoomFactor=1;selected.service=null;setView('perspectiva')},layer:x=>{if(['todos','fundacoes','meso','super'].includes(x)){layer=x;paint()}},ground:()=>{showGround=!showGround;paint()}};
Object.entries({'modelZoomIn':'zoomIn','modelZoomOut':'zoomOut','modelReset':'reset','modelGround':'ground'}).forEach(([id,key])=>document.getElementById(id)?.addEventListener('click',actions[key]));
document.querySelectorAll('[data-model-layer]').forEach(el=>el.addEventListener('click',()=>{actions.layer(el.dataset.modelLayer);document.querySelectorAll('[data-model-layer]').forEach(item=>item.setAttribute('aria-pressed',String(item===el)))}));
window.Certare4D={init:fn=>{if(typeof fn==='function')onSelect=fn;paint()},setSelection:(index)=>{if(Number.isInteger(index)&&index>=1&&index<=9){selected={kind:'eixo',index,service:null};paint()}},resize:paint,setView,focusAxis:n=>{if(Number.isInteger(n)&&n>=1&&n<=AX.length){focusX=axesX[n-1];zoomFactor=clamp(zoomFactor,1.25,1.7);selected={kind:'eixo',index:n,service:null};paint()}},inspect:()=>({view:currentView,layer,zoom:zoomFactor,focusX,selected:{...selected},conceptual:true,axes:AX.length,piles:AX.reduce((a,b)=>a+b,0)})};
window.addEventListener('resize',paint);if(typeof ResizeObserver!=='undefined')new ResizeObserver(()=>requestAnimationFrame(paint)).observe(cv);requestAnimationFrame(paint);
})();