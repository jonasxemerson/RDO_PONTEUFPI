/* CERTARE — Ponte UFPI / renderizador WebGL conceitual.
   Quantidades de peças são do JSON controlado. Coordenadas, cotas, dimensões e
   posição de cada peça são apenas esquemáticas, NÃO substituem pranchas oficiais.
   Não há inferência de execução individual nem apresentação como BIM homologado. */
(function(){
'use strict';
const cfg=JSON.parse(document.getElementById('certare-config').textContent);
const AX=cfg.estacas.previstas_por_eixo,HIST=cfg.estacas.historicas_por_eixo;
const pad=n=>String(n).padStart(2,'0');
const cv=document.getElementById('bridge4d');if(!cv)return;
const gl=cv.getContext('webgl',{alpha:true,antialias:true,premultipliedAlpha:false})||
         cv.getContext('experimental-webgl',{alpha:true,antialias:true,premultipliedAlpha:false});
const frame=cv.parentElement,markers=document.getElementById('modelMarkers');
const status=document.getElementById('modelRenderStatus');
if(!gl){
  if(status)status.textContent='WebGL indisponível neste navegador. Utilize os botões de eixo para consultar as quantidades.';
  const alt=cv.getContext('2d');if(alt){cv.width=1000;cv.height=440;alt.fillStyle='#eef4f0';alt.fillRect(0,0,1000,440);alt.font='bold 26px Arial';alt.fillStyle='#355747';alt.fillText('Visualização 3D indisponível',45,150);alt.font='18px Arial';alt.fillText('Dados e consulta por eixo permanecem acessíveis.',45,185);}
  window.Certare4D={init:()=>{},setSelection:()=>{},setView:()=>{},focusAxis:()=>{},resize:()=>{},inspect:()=>({conceptual:true,renderer:'unavailable',axes:cfg.eixos,piles:AX.reduce((a,b)=>a+b,0)})};
  return;
}
const VS='attribute vec3 aP;attribute vec3 aN;attribute vec4 aC;uniform vec3 uRight,uUp,uEye,uFocus;uniform float uScale;uniform vec2 uSize;varying vec3 vN;varying vec4 vC;varying float vDepth;void main(){vec3 p=aP-uFocus;vec2 screen=vec2(dot(p,uRight),dot(p,uUp))*uScale;float depth=dot(p,uEye);gl_Position=vec4(screen.x*2.0/uSize.x,screen.y*2.0/uSize.y,-depth/1100.0,1.0);vN=aN;vC=aC;vDepth=depth;}';
const FS='precision mediump float;varying vec3 vN;varying vec4 vC;varying float vDepth;void main(){vec3 n=normalize(vN);vec3 light=normalize(vec3(-0.48,0.88,0.49));float diff=max(dot(n,light),0.0);float ambient=0.70;float shade=ambient+0.30*diff;float rim=0.05*pow(1.0-abs(n.y),2.0);vec3 col=vC.rgb*(shade+rim);gl_FragColor=vec4(col,vC.a);}';
function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const prog=gl.createProgram();gl.attachShader(prog,shader(gl.VERTEX_SHADER,VS));gl.attachShader(prog,shader(gl.FRAGMENT_SHADER,FS));gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(prog));gl.useProgram(prog);
const aP=gl.getAttribLocation(prog,'aP'),aN=gl.getAttribLocation(prog,'aN'),aC=gl.getAttribLocation(prog,'aC');
const uRight=gl.getUniformLocation(prog,'uRight'),uUp=gl.getUniformLocation(prog,'uUp'),uEye=gl.getUniformLocation(prog,'uEye'),uFocus=gl.getUniformLocation(prog,'uFocus'),uScale=gl.getUniformLocation(prog,'uScale'),uSize=gl.getUniformLocation(prog,'uSize');
const vertexBuffer=gl.createBuffer();
gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LESS);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
const L=76; // unidades exclusivamente gráficas, sem equivalência métrica
const AXIS=Array.from({length:cfg.eixos},(_,i)=>(i-(cfg.eixos-1)/2)*L);
const CONST={ground:-42,pileBottom:-40,pileTop:-7,capY:-3,capHeight:5,pillarTop:25,beamY:29,deckY:36};
const COLORS={estacas:'#90A8AD',bloco:'#B9C7C4',pilar:'#9EAFAF',travessa:'#78959B',longarina:'#657E83',tabuleiro:'#CBD6D4',solo:'#DDE7E0',linha:'#A2BDB0'};
const parseHex=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255);
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=v=>{const d=Math.hypot(...v)||1;return v.map(x=>x/d)};
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
let selected={kind:'eixo',index:7,service:null};
let view='perspectiva',layer='todos',yaw=.42,pitch=.53,zoom=1,focusX=0,showGround=true;
let down=null,width=0,height=0,screenScale=1,refs=[],drawCalls=0,lastVertices=0,dragged=false;
const views={perspectiva:[.42,.53],lateral:[0,.10],superior:[.01,1.54],frontal:[Math.PI/2,.13]};
function camera(){
 const eye=[Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch)];
 const right=[Math.cos(yaw),0,-Math.sin(yaw)];
 const up=norm(cross(eye,right));
 return {eye,right,up};
}
function proj(p){
 const {eye,right,up}=camera();const d=sub(p,[focusX,0,0]);
 return [width/2+dot(d,right)*screenScale,height/2-dot(d,up)*screenScale,dot(d,eye)];
}
const objects=[];
function makeObj(service,kind,index,alpha=1){
 const obj={service,kind,index,alpha,vertices:[],center:[0,0,0],clickable:kind!=='cenario'};
 objects.push(obj);return obj;
}
function tri(o,a,b,c,normal){
 const n=normal||norm(cross(sub(b,a),sub(c,a)));
 for(const p of [a,b,c])o.vertices.push(...p,...n);
}
function quad(o,a,b,c,d,n){tri(o,a,b,c,n);tri(o,a,c,d,n)}
function box(o,c,w,h,d){
 const [x,y,z]=c,X=w/2,Y=h/2,Z=d/2;
 const p=[ [x-X,y-Y,z-Z],[x+X,y-Y,z-Z],[x+X,y-Y,z+Z],[x-X,y-Y,z+Z],
           [x-X,y+Y,z-Z],[x+X,y+Y,z-Z],[x+X,y+Y,z+Z],[x-X,y+Y,z+Z] ];
 quad(o,p[4],p[5],p[6],p[7],[0,1,0]);
 quad(o,p[3],p[2],p[1],p[0],[0,-1,0]);
 quad(o,p[0],p[1],p[5],p[4],[0,0,-1]);
 quad(o,p[2],p[3],p[7],p[6],[0,0,1]);
 quad(o,p[1],p[2],p[6],p[5],[1,0,0]);
 quad(o,p[3],p[0],p[4],p[7],[-1,0,0]);o.center=c;
}
function cylinder(o,x,z,y0,y1,r){
 const facets=9;for(let i=0;i<facets;i++){
  const a=i*2*Math.PI/facets,b=(i+1)*2*Math.PI/facets;
  const ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b);
  const p=[x+ca*r,y0,z+sa*r],q=[x+cb*r,y0,z+sb*r],u=[x+ca*r,y1,z+sa*r],v=[x+cb*r,y1,z+sb*r];
  quad(o,p,q,v,u,norm([ca+cb,0,sa+sb]));
  tri(o,[x,y1,z],u,v,[0,1,0]);
 }
 o.center=[x,(y0+y1)/2,z];
}
function scene(){
 objects.length=0;
 if(showGround){
  box(makeObj('solo','cenario',0,.25),[0,-43,0],690,1,126);
  for(let i=0;i<9;i++)box(makeObj('linha','cenario',0,.25),[AXIS[i],-41.9,0],.42,.25,115);
 }
 for(let i=0;i<cfg.eixos;i++){
  const x=AXIS[i],count=AX[i],rows=Math.ceil(count/6),zStep=9,spread=(rows-1)*4.1;
  for(let j=0;j<count;j++){
   const dz=(j%6-2.5)*zStep,dx=(Math.floor(j/6)-(rows-1)/2)*4.1;
   const o=makeObj('estacas','eixo',i+1,.92);cylinder(o,x+dx,dz,-42,-5,1.40);
  }
  const cap=makeObj('bloco','eixo',i+1,.96);box(cap,[x,-2,0],Math.max(17,spread+8),6,62);
  for(let p=0;p<4;p++){
    const z=-23+p*(46/3);const pier=makeObj('pilar','eixo',i+1,.98);
    box(pier,[x,11,z],4.4,27.5,4.4);
  }
  const trav=makeObj('travessa','eixo',i+1,1);box(trav,[x,27,0],8.0,5.6,70);
 }
 for(let i=0;i<cfg.vaos;i++){
  const x=(AXIS[i]+AXIS[i+1])/2;
  for(let g=0;g<8;g++){
    const z=-30+g*(60/7),girder=makeObj('longarina','vao',i+1,.99);
    box(girder,[x,32,z],L-1.3,5.2,2.85);
  }
  const slab=makeObj('tabuleiro','vao',i+1,.22);box(slab,[x,36.8,0],L-.7,2.0,70);
 }
}
scene();
function isVisible(o){
 if(o.kind==='cenario')return showGround;
 return layer==='todos'||
 (layer==='fundacoes'&&['estacas','bloco'].includes(o.service))||
 (layer==='meso'&&['pilar','travessa'].includes(o.service))||
 (layer==='super'&&['longarina','tabuleiro'].includes(o.service));
}
function pack(objectsList,select=false){
 const out=[];for(const o of objectsList){
  const v=o.vertices,active=o.kind===selected.kind&&o.index===selected.index&&(!selected.service||selected.service===o.service);
  const alpha=o.alpha,hex=COLORS[o.service],color=parseHex(active?'#4DAD84':hex);
  for(let i=0;i<v.length;i+=6)out.push(v[i],v[i+1],v[i+2],v[i+3],v[i+4],v[i+5],...color,alpha);
 }return new Float32Array(out);
}
function setUniforms(){
 const {right,up,eye}=camera();
 gl.uniform3fv(uRight,right);gl.uniform3fv(uUp,up);gl.uniform3fv(uEye,eye);gl.uniform3fv(uFocus,[focusX,0,0]);
 gl.uniform1f(uScale,screenScale);gl.uniform2f(uSize,width,height);
}
function drawSet(list,depthWrite){
 if(!list.length)return;
 const data=pack(list);if(!data.length)return;
 gl.depthMask(depthWrite);
 gl.bindBuffer(gl.ARRAY_BUFFER,vertexBuffer);gl.bufferData(gl.ARRAY_BUFFER,data,gl.DYNAMIC_DRAW);
 const stride=10*4;
 for(const [attr,n,off] of [[aP,3,0],[aN,3,12],[aC,4,24]]){gl.enableVertexAttribArray(attr);gl.vertexAttribPointer(attr,n,gl.FLOAT,false,stride,off)}
 gl.drawArrays(gl.TRIANGLES,0,data.length/10);drawCalls++;lastVertices+=data.length/10;
}
function fit(){
 const rect=cv.getBoundingClientRect();width=rect.width;height=rect.height;
 const dpr=Math.min(2,window.devicePixelRatio||1);
 const rw=Math.max(1,Math.round(width*dpr)),rh=Math.max(1,Math.round(height*dpr));
 if(cv.width!==rw||cv.height!==rh){cv.width=rw;cv.height=rh}
 gl.viewport(0,0,rw,rh);
 const fullWidth=L*(cfg.eixos-1)+64;
 const baseScale=Math.min(width/(fullWidth*1.22),height/280);
 screenScale=baseScale*zoom;
}
function axisMarkers(){
 if(!markers)return;
 markers.innerHTML='';
 const entries=AXIS.map((x,i)=>({txt:'E'+pad(i+1),p:[x,46,-37],i:i+1}));
 if(width<550&&zoom<1.35)entries.splice(0,entries.length,...entries.filter((_,i)=>i%2===0));
 for(const {txt,p,i} of entries){
  const [px,py]=proj(p);if(px<25||px>width-25||py<42||py>height-25)continue;
  const el=document.createElement('button');el.type='button';el.textContent=txt;el.className='axis-marker';
  el.setAttribute('aria-label','Selecionar eixo '+pad(i));
  if(selected.kind==='eixo'&&selected.index===i)el.classList.add('is-active');
  el.style.left=px+'px';el.style.top=py+'px';
  el.addEventListener('click',e=>{e.stopPropagation();select('eixo',i,'pilar')});
  markers.appendChild(el);
 }
}
function paint(){
 fit();if(!width||!height)return;
 gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(prog);setUniforms();
 drawCalls=0;lastVertices=0;
 const vis=objects.filter(isVisible);
 drawSet(vis.filter(o=>o.alpha>.30),true);
 drawSet(vis.filter(o=>o.alpha<=.30).sort((a,b)=>proj(a.center)[2]-proj(b.center)[2]),false);
 gl.depthMask(true);axisMarkers();
}
function select(kind,index,service){
 selected={kind,index,service:service||null};if(kind==='eixo')onSelect(kind,index);
 paint();window.dispatchEvent(new CustomEvent('certare:select',{detail:{kind,index,service}}));
}
function clickAt(x,y){
 const vis=objects.filter(o=>isVisible(o)&&o.clickable);
 let winner=null,best=Infinity;
 for(const o of vis){
  const p=proj(o.center),dx=p[0]-x,dy=p[1]-y;
  const tolerance=o.service==='estacas'?32:o.service==='longarina'?30:48;
  const score=Math.hypot(dx,dy);
  if(score<best&&score<tolerance){winner=o;best=score}
 }
 if(winner)select(winner.kind,winner.index,winner.service);
}
function setView(name){if(!views[name])return;view=name;[yaw,pitch]=views[name];document.querySelectorAll('[data-model-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.modelView===name)));paint()}
function reset(){zoom=1;focusX=0;selected.service=null;setView('perspectiva')}
cv.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY,sx:e.clientX,sy:e.clientY};dragged=false;cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!down)return;const dx=e.clientX-down.x,dy=e.clientY-down.y;if(Math.abs(dx)+Math.abs(dy)>0){if(Math.hypot(e.clientX-down.sx,e.clientY-down.sy)>4)dragged=true;yaw+=dx*.006;pitch=clamp(pitch+dy*.004,.04,1.56);down.x=e.clientX;down.y=e.clientY;paint()}});
cv.addEventListener('pointerup',e=>{if(!down)return;down=null;if(!dragged){const r=cv.getBoundingClientRect();clickAt(e.clientX-r.left,e.clientY-r.top)}});
cv.addEventListener('pointercancel',()=>{down=null});
cv.addEventListener('wheel',e=>{e.preventDefault();zoom=clamp(zoom*(e.deltaY>0?.89:1.12),.52,3.1);paint()},{passive:false});
cv.addEventListener('keydown',e=>{
 const key=e.key;let handled=true;
 if(key==='ArrowRight')yaw+=.13;else if(key==='ArrowLeft')yaw-=.13;
 else if(key==='ArrowUp')pitch=clamp(pitch+.13,.04,1.56);
 else if(key==='ArrowDown')pitch=clamp(pitch-.13,.04,1.56);
 else if(key==='+'||key==='=')zoom=clamp(zoom*1.15,.52,3.1);
 else if(key==='-')zoom=clamp(zoom/1.15,.52,3.1);
 else if(key==='Home'){reset();return}
 else handled=false;
 if(handled){e.preventDefault();paint()}
});
document.querySelectorAll('[data-model-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.modelView)));
document.querySelectorAll('[data-model-layer]').forEach(b=>b.addEventListener('click',()=>{layer=b.dataset.modelLayer;document.querySelectorAll('[data-model-layer]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));paint()}));
function wire(id,fn){document.getElementById(id)?.addEventListener('click',fn)}
wire('modelReset',reset);wire('modelZoomIn',()=>{zoom=clamp(zoom*1.18,.52,3.1);paint()});
wire('modelZoomOut',()=>{zoom=clamp(zoom/1.18,.52,3.1);paint()});
wire('modelGround',()=>{showGround=!showGround;paint()});
wire('modelFocusAxis',()=>{const n=selected.kind==='eixo'?selected.index:7;focusX=AXIS[n-1];zoom=clamp(zoom,1.35,1.8);selected={kind:'eixo',index:n,service:null};paint()});
const card=cv.closest('.card'),expand=document.getElementById('modelPresentation');
function presentation(force){
 if(!card)return;const active=typeof force==='boolean'?force:!card.classList.contains('model-presentation');
 card.classList.toggle('model-presentation',active);document.body.classList.toggle('presentation-open',active);
 expand?.setAttribute('aria-pressed',String(active));
 if(expand)expand.textContent=active?'Fechar apresentação':'Ampliar modelo';
 requestAnimationFrame(paint);
}
expand?.addEventListener('click',()=>presentation());
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&card?.classList.contains('model-presentation'))presentation(false)});
let onSelect=()=>{};
window.Certare4D={
 init:fn=>{if(typeof fn==='function')onSelect=fn;paint()},
 setSelection:n=>{if(Number.isInteger(n)&&n>=1&&n<=AX.length){selected={kind:'eixo',index:n,service:null};paint()}},
 setView,
 focusAxis:n=>{if(Number.isInteger(n)&&n>=1&&n<=AX.length){focusX=AXIS[n-1];zoom=clamp(zoom,1.35,1.8);selected={kind:'eixo',index:n,service:null};paint()}},
 resize:paint,
 inspect:()=>({renderer:'webgl',conceptual:true,axes:AX.length,piles:AX.reduce((a,b)=>a+b,0),view,layer,zoom,focusX,selected:{...selected},drawCalls,lastVertices})
};
gl.canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();if(status)status.textContent='Visualização WebGL interrompida; recarregue a página para reiniciá-la.'});
window.addEventListener('resize',paint);
if(typeof ResizeObserver!=='undefined')new ResizeObserver(()=>requestAnimationFrame(paint)).observe(cv);
requestAnimationFrame(paint);
})();