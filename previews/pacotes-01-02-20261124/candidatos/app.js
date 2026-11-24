/* CERTARE / SDU Norte — cockpit de fiscalização, candidato não publicado.
 * Three.js r150 MIT. Quantidades somente dos JSONs versionados; malha 3D é esquemática.
 * Execução de campo, concretagem identificada e base histórica nunca são somadas
 * entre datas ou convertidas em aceite ou resistência estrutural. */
(()=>{
'use strict';
const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const axisId=n=>'E'+String(n).padStart(2,'0');
const dateBR=s=>/^\d{4}-\d\d-\d\d$/.test(s||'')?s.slice(8)+'/'+s.slice(5,7)+'/'+s.slice(0,4):'Sem data';
const approved=new Set(['homologado_responsavel','validado_campo']);
const banned=new Set(['seguranca','qualidade','equipamento','ambiental']);
const structuralLabels={todos:'Todos',estacas:'Estacas',bloco:'Blocos',pilar:'Pilares',longarina:'Longarinas',travessa:'Travessas',prelaje:'Pré-lajes',tabuleiro:'Tabuleiro',solo:'Terreno'};
const semantic={historico:'#94A3B8',execucao:'#D97706',concretagem:'#059669'};
const state={axis:7,hoverAxis:null,mode:'sistema',system:'todos',milestone:'atual',filter:'todos',eventId:null};
let bundle=null,viewer=null,events=[],inferences=[],cfg=null,planned=[],evolution=null;
const observedTargets=new Set();

function readLinkAxis(){
 try{const val=new URL(location.href).searchParams.get('eixo');const n=Number(val);return /^(0?[1-9])$/.test(val||'')&&n>=1&&n<=9?n:7}catch{return 7}
}
state.axis=readLinkAxis();

async function loadData(){
 const offline=$('offline-data');
 if(offline){
  $('offlineBanner').hidden=false;
  const payload=JSON.parse(offline.textContent);
  return {cfg:payload.cfg,docs:payload.docs||[],manifest:payload.manifest||{files:[]},offline:true};
 }
 // Fluxo de produção: preserva os JSONs gerados e versionados pelo pipeline atual.
 const [cr,mr]=await Promise.all([
  fetch('data/estado_consolidado.json',{cache:'no-store'}),
  fetch('data/manifest.json',{cache:'no-store'})
 ]);
 if(!cr.ok||!mr.ok)throw Error('JSON consolidado ou manifesto público indisponível');
 const conf=await cr.json(),manifest=await mr.json();
 const files=(manifest.files||[]).filter(name=>/^data\/observacoes-\d{4}-\d{2}\.json$/.test(name));
 const docs=await Promise.all(files.map(async file=>{
  const r=await fetch(file,{cache:'no-store'});if(!r.ok)throw Error('Documento indisponível: '+file);
  return {file,data:await r.json()};
 }));
 return {cfg:conf,manifest,docs,offline:false};
}
function normalizeLoaded(loaded){
 cfg=loaded.cfg;bundle=loaded;
 if(!cfg||cfg.eixos!==9||cfg.vaos!==8)throw Error('Modelo de projeto inesperado');
 planned=cfg.estacas.previstas_por_eixo;
 if(planned.reduce((a,b)=>a+b,0)!==292)throw Error('Previsto inconsistente com fonte versionada');
 evolution=cfg.consolidacao?.evolucao_fisica;
 if(!evolution||!Array.isArray(evolution.estacas_por_eixo)||evolution.estacas_por_eixo.length!==9)throw Error('Estado consolidado incompleto');
 const known=new Set(),out=[],inf=[];
 for(const doc of loaded.docs){
  if(!/^data\/observacoes-\d{4}-\d{2}\.json$/.test(doc.file))continue;
  for(const item of doc.data.events||[]){
   if(!item?.id||known.has(item.id)||banned.has(item.service))continue;
   if(item.validation && !approved.has(item.validation))continue;
   known.add(item.id);
   out.push({...item,sourceFile:doc.file,validation:'homologado_responsavel'});
  }
  for(const x of doc.data.inferences||[]){
   if(x.validation && x.validation!=='homologada_por_inferencia')continue;
   if(!x.id||x.exact_date)continue;
   inf.push({...x,sourceFile:doc.file,validation:'homologada_por_inferencia'});
  }
 }
 events=out.sort((a,b)=>(a.date+' '+(a.time||'')+' '+a.id).localeCompare(b.date+' '+(b.time||'')+' '+b.id));
 inferences=inf;
 for(const e of events) observedTargets.add(e.target);
 $('referenceLabel').textContent='Consolidação homologada: '+dateBR(evolution.data_referencia)+(loaded.offline?' · prévia offline':' · fonte GitHub');
 $('methodSource').textContent=loaded.offline?
  'Prévia offline: extrato público dos JSONs do repositório incorporado integralmente no arquivo HTML. A base histórica continua sem data individual determinada.':
  'Produção: consulta data/estado_consolidado.json, data/manifest.json e os JSONs mensais previstos no manifesto, sem modificar o pipeline de homologação.';
}
function dataAtAxis(n){
 if(state.milestone==='atual')return {...evolution.estacas_por_eixo[n-1],date:evolution.data_referencia};
 const limit=state.milestone;
 const matched=events.filter(e=>e.target===axisId(n)&&e.date<=limit&&e.state==='snapshot'&&e.quantity_kind==='total_reportado');
 const last=list=>list.length?list[list.length-1]:null;
 const datedConcrete=last(matched.filter(e=>e.metric==='estacas_concretadas'));
 const datedExec=last(matched.filter(e=>['estacas_executadas_etapa_a_verificar','estacas_finalizadas_etapa_a_verificar','estacas_feitas_etapa_indefinida'].includes(e.metric)));
 const concrete=datedConcrete?.quantity??null;
 const executed=datedExec?.quantity??concrete;
 const source=datedExec||datedConcrete;
 return {eixo:axisId(n),previstas_projeto:planned[n-1],
    executadas_registradas:executed,concretadas_identificadas:concrete,
    origem_execucao:source?'campo_homologado_datado':'sem_registro_datado',
    data_execucao_campo:source?.date||null,evento_origem:source?.id||null,
    excedente_executado:executed!=null?Math.max(0,executed-planned[n-1]):0,
    participacao_resistente:'nao_determinada',locacao_conforme_projeto:'nao_verificada',
    etapa_execucao:datedConcrete&&!datedExec?'concretagem_datada':datedExec?'etapa_nao_discriminada':'sem_etapa_datada'};
}
function axisSemantic(n){
 const p=dataAtAxis(n);
 if(p.origem_execucao!=='campo_homologado_datado'&&p.origem_execucao!=='campo_homologado')return 'historico';
 if(p.executadas_registradas!=null&&p.concretadas_identificadas===p.executadas_registradas&&p.etapa_execucao==='concretagem_datada')return 'concretagem';
 return 'execucao';
}
function setMilestone(date){
 state.milestone=date;
 state.eventId=null;
 renderAll();
}
function sumKnown(rows,k){const valid=rows.map(r=>r[k]).filter(Number.isFinite);return {value:valid.reduce((a,b)=>a+b,0),count:valid.length}}
function updateKpis(){
 const atCurrent=state.milestone==='atual';
 const rows=Array.from({length:9},(_,i)=>dataAtAxis(i+1));
 const write=(id,value)=>$(id).textContent=value;
 if(atCurrent){
  write('kpi-exec',evolution.total_estacas_execucao_registrada+' / 292');
  write('kpi-concrete',evolution.total_estacas_concretadas_identificadas+' / 292');
  write('kpi-blocks',evolution.total_blocos_concluidos_registrados+' / 9');
  write('kpi-pillars',evolution.total_pilares_integralmente_concretados_registrados+' / 36');
  write('kpi-girders',evolution.total_longarinas_concretadas_em_campo+' / 64');
 } else {
  const exec=sumKnown(rows,'executadas_registradas'),concrete=sumKnown(rows,'concretadas_identificadas');
  write('kpi-exec',exec.count?exec.value+'*':'—');
  write('kpi-concrete',concrete.count?concrete.value+'*':'—');
  write('kpi-blocks','—');write('kpi-pillars','—');
  const beams=events.filter(e=>e.date<=state.milestone&&e.metric==='longarinas_concretadas_total'&&e.state==='snapshot');
  write('kpi-girders',beams.length?beams[beams.length-1].quantity+'*':'—');
 }
 write('kpi-plan','292');
 const subtitle=atCurrent?'Visão consolidada (base histórica + homologação)':
  'Marco '+dateBR(state.milestone)+' · *somente eixos com snapshot datado, não total global';
 $('chartCaption').textContent=subtitle+'. Sem interpolar produção, sem desconsiderar o excedente E09 e sem atribuir locação individual.';
}
function setAxis(n,focus=false){
 if(!Number.isInteger(n)||n<1||n>9)return;
 state.axis=n;state.eventId=null;
 renderAxis();renderBars();renderEvidence();
 viewer?.select(n,focus);
}
function renderAxis(){
 const p=dataAtAxis(state.axis),n=state.axis;
 $('axisName').textContent=axisId(n);
 $('axisExecuted').textContent=p.executadas_registradas??'—';
 $('axisConcrete').textContent=p.concretadas_identificadas??'—';
 $('axisPlanned').textContent=p.previstas_projeto;
 const base=p.origem_execucao==='base_historica';
 const undated=p.origem_execucao==='sem_registro_datado';
 $('axisSource').textContent=base?'Base histórica':undated?'Sem registro datado':'Campo homologado';
 $('axisOrigin').textContent=base?'Histórico (sem data)':undated?'Não localizado':dateBR(p.data_execucao_campo);
 const excess=p.excedente_executado||0;
 $('axisCaveat').textContent=excess?
  '+'+excess+' estaca(s) executada(s) frente ao projeto. Locação e participação resistente indeterminadas.':
  'Dados agregados. Sem vínculo de execução à geometria individual.';
 $('axisPills').innerHTML=Array.from({length:9},(_,i)=>{
  const x=i+1;
  return '<button type="button" data-axis="'+x+'" aria-pressed="'+String(x===n)+'">'+axisId(x)+'</button>';
 }).join('');
 $('axisPills').querySelectorAll('[data-axis]').forEach(b=>b.addEventListener('click',()=>setAxis(Number(b.dataset.axis),true)));
 $('copyView').textContent='Copiar Link da Vista · ?eixo='+String(n).padStart(2,'0');
}
function renderBars(){
 const root=$('chartRows');const html=[];
 for(let n=1;n<=9;n++){
  const p=dataAtAxis(n),con=p.concretadas_identificadas??0,ex=p.executadas_registradas;
  const percent=ex==null?0:Math.min(100,ex/p.previstas_projeto*100);
  const cpct=Math.min(100,con/p.previstas_projeto*100);
  const source=p.origem_execucao==='base_historica'?'Base histórica':p.origem_execucao==='sem_registro_datado'?'Sem snapshot datado':'Relato homologado';
  const status=axisSemantic(n);
  const color=status==='historico'?semantic.historico:semantic.execucao;
  html.push('<button class="chart-row" data-axis="'+n+'" aria-pressed="'+String(state.axis===n)+'" '+
    'aria-label="'+axisId(n)+' · '+(ex??'sem quantitativo datado')+' executadas de '+p.previstas_projeto+' previstas · '+source+'">'+
    '<span class="chart-label">'+axisId(n)+'</span><span class="chart-track">'+
    '<span class="chart-fill" style="width:'+percent+'%;background:'+color+'"></span>'+
    '<span class="chart-concrete" style="width:'+cpct+'%;background:'+(status==='historico'?semantic.historico:semantic.concretagem)+'"></span></span>'+
    '<span class="chart-count">'+(ex??'—')+' / '+p.previstas_projeto+
      (p.excedente_executado>0?'<small>+'+p.excedente_executado+' excedente</small>':'')+'</span></button>');
 }
 root.innerHTML=html.join('');
 root.querySelectorAll('button').forEach(b=>{
  const n=Number(b.dataset.axis);
  b.addEventListener('mouseenter',()=>{state.hoverAxis=n;viewer?.highlight(n)});
  b.addEventListener('mouseleave',()=>{state.hoverAxis=null;viewer?.highlight(null)});
  b.addEventListener('focus',()=>viewer?.highlight(n));
  b.addEventListener('blur',()=>viewer?.highlight(null));
  b.addEventListener('click',()=>setAxis(n,true));
 });
}
function renderTimeline(){
 const dates=[...new Set(events.map(e=>e.date).filter(x=>/^\d{4}-\d\d-\d\d$/.test(x)))].sort();
 const root=$('timelineList');
 root.innerHTML='<button type="button" data-date="atual" aria-pressed="'+String(state.milestone==='atual')+'">Consolidado atual</button>'+
  dates.map(d=>'<button type="button" data-date="'+d+'" aria-pressed="'+String(state.milestone===d)+'">'+dateBR(d)+'</button>').join('');
 root.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>setMilestone(b.dataset.date)));
 const date=state.milestone;
 const selected=date==='atual'?(dates[dates.length-1]||''):date;
 const relevant=events.filter(e=>e.date===selected);
 const box=$('bulletin');
 if(!dates.length){
  box.innerHTML='<b>Sem marcos datados homologados</b><p>Não é possível criar uma cronologia sem novas evidências.</p>';
  $('milestoneEvents').innerHTML='';
  return;
 }
 box.innerHTML='<b>'+(date==='atual'?'Consolidado atual · último marco '+dateBR(selected):'Marco documental · '+dateBR(selected))+'</b>'+
  '<p>'+relevant.length+' apontamento(s) publicável(is) nesta data. A ausência de mensagem em outra data não indica paralisação.</p>'+
  '<small>Fonte: '+safe([...new Set(relevant.map(e=>e.sourceFile))].join(' · ')||'Não localizado')+'</small>';
 $('milestoneEvents').innerHTML=relevant.map(e=>'<button type="button" data-id="'+safe(e.id)+'" aria-pressed="'+String(state.eventId===e.id)+'">'+
   '<small>'+safe(e.time||'Sem horário')+' · '+safe(e.target)+' · '+safe(e.service)+'</small>'+safe(e.activity)+'</button>').join('')||
   '<div class="empty">Sem eventos publicáveis nesse marco.</div>';
 $('milestoneEvents').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
   const e=events.find(e=>e.id===b.dataset.id);if(!e)return;
   state.eventId=e.id;
   if(/^E\d\d$/.test(e.target))setAxis(Number(e.target.slice(1)),true);
   state.eventId=e.id;
   renderEvidence();renderTimeline();
 }));
}
function renderEvidence(){
 const labels=['todos','estacas','bloco','pilar','longarina'];
 document.querySelectorAll('#evidenceFilters button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.service===state.filter)));
 const axis=axisId(state.axis);
 const filtered=events.filter(e=>(e.target===axis||(state.filter==='longarina'&&e.target==='FAB'))&&
   (state.filter==='todos'||e.service===state.filter)&&
   (state.milestone==='atual'||e.date<=state.milestone));
 const inferred=inferences.filter(e=>(e.target===axis||(state.filter==='longarina'&&e.target==='FAB'))&&
   (state.filter==='todos'||e.service===state.filter)&&
   (state.milestone==='atual'||e.completed_no_later_than<=state.milestone));
 $('evidenceCount').textContent=filtered.length+' homologado(s) · '+inferred.length+' inferido(s) · eixo '+axis;
 const rows=[];
 if(state.milestone==='atual'){
  rows.push('<div class="evidence-entry"><div class="entry-head"><b>Base histórica do '+axis+'</b><span class="doc-badge historico">Histórico</span></div>'+
   '<p>'+cfg.estacas.historicas_por_eixo[state.axis-1]+' estacas com concretagem identificada na referência histórica. A origem não permite datar a execução por peça.</p>'+
   '<small>Origem: data/indicadores-historicos.json · sem data individual</small></div>');
 }
 for(const e of filtered.slice().reverse().slice(0,40)){
  rows.push('<article class="evidence-entry"><div class="entry-head"><b>'+safe(dateBR(e.date))+' · '+safe(e.target)+'</b>'+
   '<span class="doc-badge">Homologado</span></div><p>'+safe(e.activity)+'</p>'+
   '<small>Serviço: '+safe(structuralLabels[e.service]||e.service)+' · Estado: '+safe(e.state||'Não especificado')+
   (e.quantity!=null?' · Quantidade/ordinal: '+safe(e.quantity)+' ('+safe(e.quantity_kind||'sem tipo')+')':'')+'</small>'+
   '<small>Origem JSON: '+safe(e.sourceFile)+' · ID '+safe(e.id)+'</small>'+
   '<div class="photo-slot">Fotografia de campo: nenhuma imagem vinculada ao JSON público. Não inferir evidência visual.</div></article>');
 }
 for(const x of inferred){
  rows.push('<article class="evidence-entry"><div class="entry-head"><b>'+safe(x.element||x.target)+'</b><span class="doc-badge inferido">Inferido</span></div>'+
   '<p>'+safe(x.activity)+' · concluída por inferência, sem data exata comprovada.</p><small>Concluída até '+dateBR(x.completed_no_later_than)+
   ' · Origem: '+safe(x.sourceFile)+' · '+safe(x.id)+'</small></article>');
 }
 $('evidenceList').innerHTML=rows.join('')||'<div class="empty">Nenhum registro publicável deste serviço para o eixo e marco selecionados. Sem evidência não significa frente paralisada.</div>';
}
function renderAll(){
 updateKpis();renderAxis();renderBars();renderTimeline();renderEvidence();viewer?.update();
}
async function copyView(){
 let link;
 try{
  const url=new URL(location.href);
  url.searchParams.set('eixo',String(state.axis).padStart(2,'0'));
  link=url.toString();
  history.replaceState(null,'',link);
 }catch{link=location.href+(location.search?'&':'?')+'eixo='+String(state.axis).padStart(2,'0')}
 try{
  if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(link);
  else throw Error('clipboard indisponível');
 }catch{
  const t=document.createElement('textarea');t.value=link;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();
 }
 const b=$('copyView'),previous=b.textContent;b.textContent='Link copiado ✓';
 setTimeout(()=>{b.textContent=previous},1600);
}
function bindUI(){
 $('copyView').addEventListener('click',copyView);
 $('evidenceFilters').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
  state.filter=b.dataset.service;renderEvidence();
 }));
 document.querySelectorAll('[data-viewer-mode]').forEach(b=>b.addEventListener('click',()=>{
  state.mode=b.dataset.viewerMode;viewer?.update();
  document.querySelectorAll('[data-viewer-mode]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
 }));
 document.querySelectorAll('[data-viewer-system]').forEach(b=>b.addEventListener('click',()=>{
  state.system=b.dataset.viewerSystem;viewer?.update();
  document.querySelectorAll('[data-viewer-system]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
 }));
 $('zoomIn').addEventListener('click',()=>viewer?.zoom(1.2));
 $('zoomOut').addEventListener('click',()=>viewer?.zoom(1/1.2));
 $('focusSelected').addEventListener('click',()=>viewer?.focus(state.axis));
 $('resetView').addEventListener('click',()=>viewer?.reset());
 const drawer=$('methodDrawer'),back=$('drawerBackdrop');
 const close=()=>{drawer.classList.remove('open');back.classList.remove('open');$('openMethod').focus()};
 $('openMethod').addEventListener('click',()=>{drawer.classList.add('open');back.classList.add('open');drawer.focus()});
 $('closeMethod').addEventListener('click',close);back.addEventListener('click',close);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&drawer.classList.contains('open'))close()});
}
function buildViewer(){
 if(typeof THREE==='undefined')throw Error('Biblioteca Three.js não incorporada');
 const canvas=$('viewerCanvas'),surface=$('viewerSurface');
 const scene=new THREE.Scene();
 const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'});
 renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
 renderer.setClearColor('#ffffff',0);
 renderer.shadowMap.enabled=true;
 renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 if('outputColorSpace' in renderer)renderer.outputColorSpace=THREE.SRGBColorSpace;
 const camera=new THREE.OrthographicCamera(-180,180,100,-100,.1,1200);
 scene.add(new THREE.HemisphereLight('#f8fafc','#94a3b8',1.65));
 const sun=new THREE.DirectionalLight('#ffffff',2.1);sun.position.set(-70,105,85);sun.castShadow=true;
 sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-220;sun.shadow.camera.right=220;sun.shadow.camera.top=180;sun.shadow.camera.bottom=-180;
 sun.shadow.bias=-.00025;sun.shadow.radius=4;scene.add(sun);
 const ambient=new THREE.AmbientLight('#e2e8f0',.45);scene.add(ambient);
 const grid=new THREE.GridHelper(322,32,'#94A3B8','#CBD5E1');grid.position.y=-6.3;grid.material.transparent=true;grid.material.opacity=.22;scene.add(grid);
 const water=new THREE.Mesh(new THREE.PlaneGeometry(315,72),new THREE.MeshStandardMaterial({color:'#BAE6FD',transparent:true,opacity:.24,roughness:.97,metalness:0,depthWrite:false,side:THREE.DoubleSide}));
 water.rotation.x=-Math.PI/2;water.position.y=-6.6;water.receiveShadow=true;scene.add(water);
 const axes=Array.from({length:9},(_,i)=>(i-4)*35);
 const pickables=[],parts=[],rings=[],labels=[];
 const material=(color,opacity=1)=>new THREE.MeshStandardMaterial({color,roughness:.82,metalness:.06,transparent:opacity<1,opacity,depthWrite:opacity>=1});
 function addBox(x,y,z,w,h,d,sys,svc,axis,color,span=false){
  const geo=new THREE.BoxGeometry(w,h,d);
  const m=new THREE.Mesh(geo,material(color));m.position.set(x,y,z);
  m.castShadow=true;m.receiveShadow=true;
  m.userData={axis,system:sys,service:svc,span,base:color};
  scene.add(m);pickables.push(m);parts.push(m);
  if(['bloco','pilar','travessa','longarina'].includes(svc)){
   const edge=new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#334155',transparent:true,opacity:.32,depthWrite:false}));
   edge.position.copy(m.position);scene.add(edge);m.userData.edge=edge;
  }
  return m;
 }
 function addCylinder(x,y,z,r,h,sys,svc,axis,color){
  const geo=new THREE.CylinderGeometry(r,r,h,12);
  const m=new THREE.Mesh(geo,material(color));m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;
  m.userData={axis,system:sys,service:svc,base:color};scene.add(m);pickables.push(m);parts.push(m);return m;
 }
 axes.forEach((x,i)=>{
  const axis=i+1;
  for(const z of [-7.5,-2.5,2.5,7.5])addCylinder(x,-10,z,.76,21,'fundacoes','estacas',axis,'#CBD5E1');
  addBox(x,-.35,0,9.5,2.8,20,'fundacoes','bloco',axis,'#C9D5DF');
  for(const z of [-7.5,-2.5,2.5,7.5])addBox(x,8.3,z,1.65,14.5,1.8,'apoios','pilar',axis,'#D7E1E8');
  addBox(x,16,0,11,2.1,20,'apoios','travessa',axis,'#C9D5DF');
  const ring=new THREE.Mesh(new THREE.RingGeometry(10.5,12.9,48),
     new THREE.MeshBasicMaterial({color:'#94A3B8',transparent:true,opacity:.17,side:THREE.DoubleSide,depthWrite:false}));
  ring.rotation.x=-Math.PI/2;ring.position.set(x,-5.9,0);ring.userData.axis=axis;scene.add(ring);rings.push(ring);
  const label=document.createElement('span');label.className='axis-label';label.textContent=axisId(axis);$('axisLabels').appendChild(label);labels.push({axis,label,x});
 });
 for(let i=0;i<8;i++){
  const center=(axes[i]+axes[i+1])/2;
  const axis=i+1;
  const zvals=[-8.5,-6,-3.5,-1,1,3.5,6,8.5];
  for(const z of zvals)addBox(center,19.3,z,33.7,1.8,1.12,'superestrutura','longarina',axis,'#C8D4DD',true);
  addBox(center,21,0,35,.9,20,'superestrutura','tabuleiro',axis,'#E0E8EF',true);
 }
 let yaw=-.7,pitch=.57,zoomLevel=1,focusX=0,focusEnabled=false;
 let moved=false,pointStart=null,hoverMesh=null,hoverAxis=null;
 const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
 let sizeW=1,sizeH=1;
 function viewCamera(){
  const dist=380;
  camera.position.set(focusX+dist*Math.sin(yaw)*Math.cos(pitch),dist*Math.sin(pitch)+34,dist*Math.cos(yaw)*Math.cos(pitch));
  camera.lookAt(focusX,6,0);camera.updateProjectionMatrix();
 }
 function setSize(){
  const r=surface.getBoundingClientRect();sizeW=Math.max(1,r.width);sizeH=Math.max(1,r.height);
  renderer.setSize(sizeW,sizeH,false);
  const spanX=focusEnabled?96:334;const spanY=spanX*sizeH/sizeW;
  camera.left=-spanX/2;camera.right=spanX/2;camera.top=spanY/2;camera.bottom=-spanY/2;
  camera.zoom=zoomLevel;camera.updateProjectionMatrix();viewCamera();draw();
 }
 function draw(){
  viewCamera();renderer.render(scene,camera);
  for(const a of labels){
   const p=new THREE.Vector3(a.x,24,0).project(camera);
   a.label.style.left=((p.x+1)*sizeW/2)+'px';a.label.style.top=((-p.y+1)*sizeH/2)+'px';
   a.label.style.display=(p.z>1||p.z< -1)?'none':'';
   a.label.classList.toggle('selected',a.axis===state.axis);
  }
 }
 function selectedAxisNow(){return state.hoverAxis||state.axis}
 function applyAppearance(){
  const selected=selectedAxisNow(),isolating=focusEnabled||state.hoverAxis!=null;
  for(const m of parts){
   const axis=m.userData.axis;
   const systemMatches=state.system==='todos'||m.userData.system===state.system;
   const axisMatches=axis===selected;
   const offAxis=isolating&&!axisMatches;
   const fade=systemMatches?(offAxis?.15:1):.15;
   m.material.opacity=fade;m.material.transparent=fade<1;m.material.depthWrite=fade>=1;
   m.material.color.set(m.userData.base);
   if(m.userData.edge){m.userData.edge.material.opacity=.32*fade;m.userData.edge.visible=true;}
  }
  for(const ring of rings){
   const code=axisSemantic(ring.userData.axis);
   const c=semantic[code];
   ring.material.color.set(c);
   ring.material.opacity=state.mode==='heatmap'?(ring.userData.axis===selected?.82:.54):(ring.userData.axis===selected?.35:.12);
  }
  water.material.opacity=focusEnabled?.07:.24;
  grid.material.opacity=focusEnabled?.10:.22;
  $('scenePill').textContent=state.mode==='heatmap'?
    'Heatmap agregado · '+(state.milestone==='atual'?'consolidado atual':dateBR(state.milestone))+
    ' · sem individualizar peças':'Sistema estrutural · '+axisId(selected)+' · visualização esquemática';
  draw();
 }
 function intersect(e){
  const rect=canvas.getBoundingClientRect();
  mouse.x=((e.clientX-rect.left)/rect.width)*2-1;mouse.y=-((e.clientY-rect.top)/rect.height)*2+1;
  ray.setFromCamera(mouse,camera);
  return ray.intersectObjects(pickables,false).find(x=>x.object.material.opacity>.12)||null;
 }
 function tooltipAt(e,hit){
  const tip=$('sceneTooltip');
  if(!hit){tip.hidden=true;return;}
  const m=hit.object,{axis,service}=m.userData,p=dataAtAxis(axis);
  tip.hidden=false;tip.innerHTML='<b>'+axisId(axis)+' · '+safe(structuralLabels[service]||service)+'</b>'+
   '<span>'+(p.executadas_registradas??'—')+' execução registrada · '+(p.concretadas_identificadas??'—')+
   ' concretagem identificada · '+p.previstas_projeto+' previstas.<br>Geometria ilustrativa; não representa peça atestada.</span>';
  const r=surface.getBoundingClientRect();
  tip.style.left=Math.min(e.clientX-r.left+13,r.width-200)+'px';
  tip.style.top=Math.max(13,Math.min(e.clientY-r.top+13,r.height-100))+'px';
 }
 canvas.addEventListener('pointerdown',e=>{pointStart=[e.clientX,e.clientY,yaw,pitch];moved=false;canvas.setPointerCapture(e.pointerId)});
 canvas.addEventListener('pointermove',e=>{
  if(pointStart){
   const dx=e.clientX-pointStart[0],dy=e.clientY-pointStart[1];
   if(Math.hypot(dx,dy)>4)moved=true;
   if(moved){yaw=pointStart[2]-dx*.0055;pitch=Math.max(.12,Math.min(1.42,pointStart[3]+dy*.004));draw();$('sceneTooltip').hidden=true;}
  }else{
   const hit=intersect(e);hoverMesh=hit?.object||null;
   tooltipAt(e,hit);
   if(hit){state.hoverAxis=hit.object.userData.axis;applyAppearance();}
   else if(state.hoverAxis!=null){state.hoverAxis=null;applyAppearance();}
  }
 });
 canvas.addEventListener('pointerup',e=>{
  const click=!moved&&!pointStart?.length?false:!moved;
  pointStart=null;
  if(click){const hit=intersect(e);if(hit)setAxis(hit.object.userData.axis,true);}
 });
 canvas.addEventListener('pointerleave',()=>{if(!pointStart){state.hoverAxis=null;applyAppearance();$('sceneTooltip').hidden=true}});
 canvas.addEventListener('pointercancel',()=>{pointStart=null});
 canvas.addEventListener('wheel',e=>{e.preventDefault();zoomLevel=Math.max(.65,Math.min(4,zoomLevel*(e.deltaY<0?1.12:.88)));camera.zoom=zoomLevel;camera.updateProjectionMatrix();draw()},{passive:false});
 canvas.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft')yaw-=.15;else if(e.key==='ArrowRight')yaw+=.15;
  else if(e.key==='ArrowUp')pitch=Math.min(1.42,pitch+.12);
  else if(e.key==='ArrowDown')pitch=Math.max(.12,pitch-.12);
  else return;
  e.preventDefault();draw();
 });
 const obs=typeof ResizeObserver!=='undefined'?new ResizeObserver(setSize):null;
 obs?.observe(surface);window.addEventListener('resize',setSize);
 setSize();applyAppearance();
 return {
  update:applyAppearance,
  select(n,focus){if(focus){focusEnabled=true;focusX=axes[n-1];zoomLevel=1.05;setSize()}applyAppearance()},
  focus(n){focusEnabled=true;focusX=axes[n-1];zoomLevel=1.05;setSize();applyAppearance()},
  highlight(n){state.hoverAxis=n;applyAppearance()},
  zoom(f){zoomLevel=Math.max(.65,Math.min(4,zoomLevel*f));camera.zoom=zoomLevel;camera.updateProjectionMatrix();draw()},
  reset(){focusEnabled=false;focusX=0;yaw=-.7;pitch=.57;zoomLevel=1;setSize();applyAppearance()}
 };
}
async function run(){
 try{
  const loaded=await loadData();normalizeLoaded(loaded);
  bindUI();renderAll();
  viewer=buildViewer();viewer.select(state.axis,false);
 }catch(err){
  console.error('Erro ao iniciar cockpit:',err);
  $('referenceLabel').textContent='Dados públicos não carregados: '+err.message;
  $('chartRows').innerHTML='<div class="empty">Não foi possível carregar dados ou Three.js. Confira arquivos locais ou conexão de produção. Nenhum indicador será inventado.</div>';
 }
}
run();
})();