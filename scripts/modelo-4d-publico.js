/* CERTARE | motor 4D público, isolado do ambiente operacional. Fonte geométrica: V5. */
(function(){'use strict';
const AX=[24,32,32,37,37,37,37,32,24],HIST=[24,32,32,0,0,0,4,11,8];
const records=[]; let selected={kind:'eixo',index:7},layer='todos';
const pad=n=>String(n).padStart(2,'0');
const totalFor=(s,sel)=>sel.kind==='eixo'?(s==='estacas'?AX[sel.index-1]:s==='pilar'?4:s==='bloco'||s==='travessa'?1:0):sel.kind==='vao'?(s==='longarina'?8:s==='tabuleiro'?1:0):0;
const historicFor=(s,sel)=>sel.kind==='eixo'?(s==='estacas'?HIST[sel.index-1]:s==='bloco'&&[2,3].includes(sel.index)?1:s==='pilar'&&sel.index===2?4:0):0;
const count=(s,sel)=>historicFor(s,sel);
const target=sel=>sel.kind==='eixo'?'E'+pad(sel.index):sel.kind==='vao'?'V'+pad(sel.index):'FAB';
const SERVICES={estacas:{final:'CON'},bloco:{final:'CON'},pilar:{final:'CON'},travessa:{final:'CON'},longarina:{final:'CON'},tabuleiro:{final:'LIB'}};
const cv=document.getElementById('bridge4d');if(!cv)return;const ctx=cv.getContext('2d');if(!ctx)return;
let yaw=-.39,tilt=.39,scale=1,drag=null,hit=[],zoomFactor=1;
const geo={span:78,width:64,waterY:-17};
function projection(pt,W,H){let [x,y,z]=pt;let X=x*Math.cos(yaw)-z*Math.sin(yaw),Z=x*Math.sin(yaw)+z*Math.cos(yaw);return [W/2+X*scale*.88,H*.54+(-y*Math.cos(tilt)+Z*Math.sin(tilt))*scale*.88-Z*Math.cos(tilt)*scale*.15]}
const POINTS={};function cylinder(axisX,z,base,top,r,faces=9){let verts=[];for(let i=0;i<faces;i++){let a=Math.PI*2*i/faces;verts.push([axisX+Math.cos(a)*r,base,z+Math.sin(a)*r])}for(let i=0;i<faces;i++){let a=Math.PI*2*i/faces;verts.push([axisX+Math.cos(a)*r,top,z+Math.sin(a)*r])}let f=[];for(let i=0;i<faces;i++)f.push([i,(i+1)%faces,(i+1)%faces+faces,i+faces]);f.push(Array.from({length:faces},(_,i)=>i+faces));return [verts,f]}
function boxGeom(x,y,z,dx,dy,dz){let a=x-dx/2,b=x+dx/2,c=z-dz/2,d=z+dz/2,e=y-dy/2,f=y+dy/2;return [[[a,e,c],[b,e,c],[b,e,d],[a,e,d],[a,f,c],[b,f,c],[b,f,d],[a,f,d]],[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[4,5,6,7],[0,1,2,3]]]}
function addMesh(scene,verts,faces,color,meta,opacity=1){for(let k=0;k<faces.length;k++){let poly=faces[k].map(i=>verts[i]);let avg=poly.reduce((a,p)=>a+p[1],0)/poly.length;scene.push({poly,color,meta,opacity,shade:k%3})}}
const STATUS_COLORS={nao_iniciado:'#a7b7ad',andamento:'#d3a04e',concluido:'#3c896d',liberado:'#4b82b7',parado:'#b9534f'};
function stateFor(s,sel){
 let t=totalFor(s,sel),d=count(s,sel),rel=records.filter(r=>r.target===target(sel)&&r.service===s).slice().sort((a,b)=>String(a.date).localeCompare(String(b.date)));
 let last=rel.at(-1),hasRelease=rel.some(r=>r.status==='produziu'&&r.phase==='LIB');
 if(last?.status==='parado')return 'parado';
 if(hasRelease&&t&&d>=t)return 'liberado';
 if(t&&d>=t)return 'concluido';
 if(d>0||last?.status==='andamento'||rel.some(r=>r.status==='produziu'))return 'andamento';
 return 'nao_iniciado';
}
function colorFor(s,sel){return STATUS_COLORS[stateFor(s,sel)]}
let showGround=true;
function buildScene(){
 let objects=[],axesX=Array.from({length:9},(_,i)=>(i-4)*geo.span);
 let drawFoundation=layer==='todos'||layer==='fundacoes',drawMeso=layer==='todos'||layer==='meso',drawSuper=layer==='todos'||layer==='super';
 if(showGround){
   addMesh(objects,...boxGeom(0,-26,0,730,2,156),'#dce5dc',null,.17);
   addMesh(objects,...boxGeom(0,-24,0,710,1,110),'#a2c8ca',null,.14);
 }
 axesX.forEach((x,i)=>{
   let n=i+1,sel={kind:'eixo',index:n},t=AX[i],rows=Math.ceil(t/6);
   if(drawFoundation){
      // Status das estacas é somente agregado por eixo: nenhuma posição é presumida executada.
      let foundationCol=colorFor('estacas',sel);
      for(let j=0;j<t;j++){
        let column=j%6,row=Math.floor(j/6),offset=(row-(rows-1)/2)*5.9,z=(column-2.5)*9;
        addMesh(objects,...cylinder(x+offset,z,-43,-6,1.55,7),foundationCol,sel,.88)
      }
      addMesh(objects,...boxGeom(x,-4,0,rows*6+12,6,61),colorFor('bloco',sel),sel,.90)
   }
   if(drawMeso){
      for(let j=0;j<4;j++){let z=-23+j*15.3;addMesh(objects,...boxGeom(x,10,z,4,28,4),colorFor('pilar',sel),sel,.97)}
      addMesh(objects,...boxGeom(x,25,0,8,5,76),colorFor('travessa',sel),sel,.95)
   }
 });
 if(drawSuper)for(let i=0;i<8;i++){
   let cx=(axesX[i]+axesX[i+1])/2,sel={kind:'vao',index:i+1};
   for(let j=0;j<8;j++){let z=-31+j*8.85;addMesh(objects,...boxGeom(cx,31,z,geo.span-2,5,3.0),colorFor('longarina',sel),sel,.95)}
   addMesh(objects,...boxGeom(cx,36,0,geo.span-3,2.5,71),colorFor('tabuleiro',sel),sel,.49)
 }
 return objects
}
function hexToRGB(h){return [1,3,5].map(i=>parseInt(h.slice(i,i+2),16))}function tint(col,k){let rgb=hexToRGB(col),delta=[6,-7,-16,0][k%4];return `rgb(${rgb.map(a=>Math.max(0,Math.min(255,a+delta))).join(',')})`}
function pointInPoly(p,poly){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){let a=poly[i],b=poly[j];if(((a[1]>p[1])!==(b[1]>p[1]))&&(p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]))inside=!inside}return inside}
function paint(){let W=cv.clientWidth,H=cv.clientHeight;if(!W||!H)return;let ratio=Math.min(2,window.devicePixelRatio||1);if(cv.width!==Math.round(W*ratio)||cv.height!==Math.round(H*ratio)){cv.width=W*ratio;cv.height=H*ratio}ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,W,H);let s=Math.min(W/720,H/420);let oldScale=scale;scale=s*1.05*zoomFactor;let scenes=buildScene().map(p=>({...p,pts:p.poly.map(a=>projection(a,W,H)),depth:p.poly.reduce((acc,a)=>acc+(a[0]*Math.sin(yaw)+a[2]*Math.cos(yaw)),0)/p.poly.length}));scenes.sort((a,b)=>((!a.meta?0:1)-(!b.meta?0:1)) || a.depth-b.depth);hit=[];for(const o of scenes){ctx.beginPath();o.pts.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();ctx.fillStyle=tint(o.color,o.shade);ctx.globalAlpha=o.opacity;ctx.fill();ctx.globalAlpha=1;ctx.strokeStyle='#46645621';ctx.stroke();if(o.meta)hit.push(o)}let ax=Array.from({length:9},(_,i)=>(i-4)*geo.span);ctx.fillStyle='#526b60';ctx.font='bold 12px Segoe UI,Arial';for(let i=0;i<9;i++){let [x,y]=projection([ax[i],40,-40],W,H);ctx.fillText('E'+(i+1),x-8,y)}scale=oldScale}

let onSelect=()=>{};
function applySelection(kind,index){selected={kind,index};paint();onSelect(kind,index)}
function screenEvent(ev){let r=cv.getBoundingClientRect();return [ev.clientX-r.left,ev.clientY-r.top]}
cv.addEventListener('pointerdown',ev=>{drag={x:ev.clientX,y:ev.clientY,sx:ev.clientX,sy:ev.clientY};cv.setPointerCapture(ev.pointerId)});
cv.addEventListener('pointermove',ev=>{if(!drag)return;let dx=ev.clientX-drag.x,dy=ev.clientY-drag.y;yaw+=dx*.005;tilt=Math.max(.1,Math.min(.9,tilt+dy*.003));drag.x=ev.clientX;drag.y=ev.clientY;paint()});
cv.addEventListener('pointercancel',()=>{drag=null});
cv.addEventListener('pointerup',ev=>{if(!drag)return;let d=Math.hypot(ev.clientX-drag.sx,ev.clientY-drag.sy);drag=null;if(d>6)return;let p=screenEvent(ev);for(let i=hit.length-1;i>=0;i--){if(pointInPoly(p,hit[i].pts)){let obj=hit[i].meta;applySelection(obj.kind,obj.index);return}}});
cv.addEventListener('wheel',ev=>{ev.preventDefault();zoomFactor=Math.min(2.4,Math.max(.4,zoomFactor*(ev.deltaY>0?.91:1.09)));paint()},{passive:false});
const actions={zoomIn:()=>{zoomFactor=Math.min(2.4,zoomFactor*1.15);paint()},zoomOut:()=>{zoomFactor=Math.max(.4,zoomFactor/1.15);paint()},reset:()=>{yaw=-.39;tilt=.39;zoomFactor=1;paint()},layer:x=>{if(['todos','fundacoes','meso','super'].includes(x)){layer=x;paint()}},ground:()=>{showGround=!showGround;paint()}};
Object.entries({'modelZoomIn':'zoomIn','modelZoomOut':'zoomOut','modelReset':'reset','modelGround':'ground'}).forEach(([id,key])=>document.getElementById(id)?.addEventListener('click',actions[key]));
document.querySelectorAll('[data-model-layer]').forEach(el=>el.addEventListener('click',()=>{actions.layer(el.dataset.modelLayer);document.querySelectorAll('[data-model-layer]').forEach(item=>item.setAttribute('aria-pressed',String(item===el)))}));
window.Certare4D={init:fn=>{if(typeof fn==='function')onSelect=fn;paint()},setSelection:(index)=>{if(Number.isInteger(index)&&index>=1&&index<=9){selected={kind:'eixo',index};paint()}},resize:paint};
window.addEventListener('resize',paint);requestAnimationFrame(paint);
})();