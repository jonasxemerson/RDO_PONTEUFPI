/* CERTARE V2: interface documental sem criar datas, quantidades ou aceites. */
(function(){
'use strict';
const CFG=JSON.parse(document.getElementById('certare-config').textContent);
const AX=CFG.estacas.previstas_por_eixo,HIST=CFG.estacas.historicas_por_eixo;
const $=id=>document.getElementById(id);
let currentAxis=7, currentService='estacas', progressMode='execucao';
const EVOLUTION=CFG.consolidacao?.evolucao_fisica||{};
const progressAxes=Array.isArray(EVOLUTION.estacas_por_eixo)?EVOLUTION.estacas_por_eixo:[];
const currentProgress=n=>progressAxes[n-1]||null;
const label={estacas:'Estacas',bloco:'Blocos',pilar:'Pilares',travessa:'Travessas',longarina:'Longarinas',tabuleiro:'Tabuleiro'};
function escapeHTML(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function dateBR(v){let p=String(v||'').split('-');return p.length===3?p.reverse().join('/'):'Sem data';}
function currentEvents(){return Array.isArray(window.CertarePublicEvents)?window.CertarePublicEvents:[]}
function axisCode(n){return 'E'+String(n).padStart(2,'0')}
function syncAxis(n,fromModel=false){
 if(!Number.isInteger(n)||n<1||n>9)return;
 currentAxis=n;
 if(!fromModel){window.Certare4D?.setSelection(n); if(typeof window.selectAxis==='function')window.selectAxis(n);}
 document.querySelectorAll('.axis-chooser button, .axis-progress button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.axis)===n)));
 drawEvidence();
}
function renderSummary(){
 const sum=a=>a.reduce((x,y)=>x+y,0);
 const expected=sum(AX);
 const concrete=EVOLUTION.total_estacas_concretadas_identificadas??sum(HIST);
 const executed=EVOLUTION.total_estacas_execucao_registrada??concrete;
 const values=[
  ['kpiEixos',String(CFG.eixos)+' eixos'],
  ['metaVaos',String(CFG.vaos)+' vãos no modelo'],
  ['kpiEstacas',executed+' / '+expected],
  ['kpiConcretadas',concrete+' / '+expected],
  ['kpiBlocos',String(EVOLUTION.total_blocos_concluidos_registrados??sum(CFG.blocos.historicos_por_eixo))+' / '+CFG.blocos.previstos_total],
  ['kpiPilares',String(EVOLUTION.total_pilares_integralmente_concretados_registrados??sum(CFG.pilares.historicos_por_eixo))+' / '+CFG.eixos*CFG.pilares.previstos_por_eixo],
  ['kpiLongarinas',EVOLUTION.total_longarinas_concretadas_em_campo==null?'—':EVOLUTION.total_longarinas_concretadas_em_campo+' / '+(CFG.vaos*8)],
 ];
 for(const [id,value] of values){let el=$(id);if(el)el.textContent=value}
 const date=$('progressDate');if(date)date.textContent='Consolidação: '+dateBR(EVOLUTION.data_referencia);
 const fieldDate=$('fieldDate');if(fieldDate)fieldDate.textContent='Campo: '+dateBR(EVOLUTION.data_referencia);
}

function renderFieldProgress(){
 const root=$('fieldProgress'),caveat=$('fieldCaveat');
 if(!root||!caveat)return;
 const field=CFG.consolidacao?.execucao_em_campo||{};
 const piles=field.estacas_por_eixo||{};
 const axes=['E07','E08','E09'];
 const cards=axes.map(code=>{
   const x=piles[code];if(!x)return '';
   const delta=x.diferenca_executado_menos_previsto;
   const note=delta>0?('Excedente quantitativo de '+delta+' unidade(s); locação e resistência não determinadas') :
       'Situação executada de campo; etapa final não especificada';
   return '<div class="card progress-card"><div class="eyebrow">'+escapeHTML('Eixo '+Number(code.slice(1)))+'</div>'+
     '<div class="progress-value">'+escapeHTML(x.executadas_em_campo)+' / '+escapeHTML(x.previstas_projeto)+'</div>'+
     '<div class="progress-note">Executadas em campo / previstas no projeto</div>'+
     '<p class="small-note">'+escapeHTML(note)+'</p>'+
     '<p class="small-note">Concretadas na base histórica: '+escapeHTML(x.concretadas_na_base_anterior)+' (indicador independente)</p></div>';
 });
 const beams=field.longarinas;
 if(beams)cards.push('<div class="card progress-card"><div class="eyebrow">Longarinas no pátio</div>'+
   '<div class="progress-value">'+escapeHTML(beams.concretadas_em_campo)+'</div>'+
   '<div class="progress-note">Vigas concretadas · total de campo em '+escapeHTML(dateBR(beams.data))+'</div>'+
   '<p class="small-note">Não somar com as longarinas concretadas anteriormente. Não comprova protensão nem lançamento.</p></div>');
 const partial=EVOLUTION.pilares_E03_concretagem_parcial;
 if(partial)cards.push('<div class="card progress-card"><div class="eyebrow">Pilares E03-P03/P04</div>'+
   '<div class="progress-value">'+escapeHTML(partial.metades_inferiores_concretadas)+' parciais</div>'+
   '<div class="progress-note">Metades inferiores concretadas · partes superiores não confirmadas</div>'+
   '<p class="small-note">Não acrescentar aos seis pilares integralmente concretados da consolidação.</p></div>');
 if(EVOLUTION.prelajes_acrescimos_reportados_novembro!=null)cards.push(
   '<div class="card progress-card"><div class="eyebrow">Pré-lajes · produção adicional</div>'+
   '<div class="progress-value">+'+escapeHTML(EVOLUTION.prelajes_acrescimos_reportados_novembro)+'</div>'+
   '<div class="progress-note">Acréscimos relatados e homologados em novembro</div>'+
   '<p class="small-note">Não representa estoque total. Base histórica ainda não conciliada por peça.</p></div>');
 root.innerHTML=cards.join('');
 const e9=piles.E09;
 caveat.innerHTML='<b>Leitura técnica:</b> executado em campo e projetado são duas referências verdadeiras com funções diferentes. '+
   (e9 ? 'No E09: '+escapeHTML(e9.executadas_em_campo)+' estacas finalizadas em campo versus '+
    escapeHTML(e9.previstas_projeto)+' previstas em projeto. A diferença não prova erro de locação; ' : '')+
   'a identificação de elementos efetivamente aproveitados na resistência depende de conferência de locação, documentação de execução e validação estrutural. '+
   'A concretagem parcial dos pilares E03-P03/P04 também não equivale à conclusão integral dos pilares.';
}
function makeBars(){
 const root=$('axisProgress');if(!root)return;
 const concreteMode=progressMode==='concretagem';
 root.innerHTML=AX.map((planned,i)=>{
   const e=currentProgress(i+1);
   const historic=HIST[i], concrete=e?.concretadas_identificadas??historic;
   const executed=e?.executadas_registradas??concrete;
   const observed=concreteMode?concrete:executed;
   const excess=!concreteMode&&executed>planned;
   const field=e?.origem_execucao==='campo_homologado';
   const fill=Math.min(100,100*observed/planned).toFixed(2);
   const confirmed=Math.min(100,100*concrete/planned).toFixed(2);
   const source=field?('Campo homologado · '+dateBR(e.data_execucao_campo)):'Base histórica · data de referência não identificada';
   const descriptor=concreteMode?'Concretagem identificada':(field?'Execução homologada, etapa final não discriminada':'Concretagem da base histórica');
   const more=excess?'<small>+'+(executed-planned)+' além do previsto</small>':'';
   return '<button type="button" data-axis="'+(i+1)+'" data-source="'+(field?'campo_homologado':'base_historica')+
      '" data-excess="'+String(excess)+'" aria-pressed="'+String(i+1===currentAxis)+'" '+
      'aria-label="Eixo '+(i+1)+': '+observed+' de '+planned+' estacas, '+descriptor+'. '+source+
      (excess?'. '+(executed-planned)+' além do projeto':'')+'">'+
      '<span class="axis-progress-label">E'+String(i+1).padStart(2,'0')+'</span>'+
      '<span class="axis-progress-middle"><span class="axis-progress-track" aria-hidden="true">'+
      '<span class="axis-progress-fill" style="width:'+fill+'%;'+(concreteMode?'background:#43876d':'')+'"></span>'+
      (concreteMode?'':'<span class="axis-progress-concrete" style="width:'+confirmed+'%"></span>')+
      '</span><span class="axis-progress-origin">'+source+'</span></span>'+
      '<span class="axis-progress-count">'+observed+' / '+planned+more+'</span></button>';
 }).join('');
 root.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>syncAxis(Number(b.dataset.axis))));
 document.querySelectorAll('[data-progress-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.progressMode===progressMode)));
 const text=$('progressContext'), legend=$('progressLegend');
 if(concreteMode){
   if(text)text.textContent='Concretagem identificada: '+(EVOLUTION.total_estacas_concretadas_identificadas??'—')+
     ' estacas de '+AX.reduce((a,b)=>a+b,0)+' previstas. Contagens das etapas posteriores sem indicação expressa de concretagem não alteram esta série.';
   if(legend)legend.textContent='Verde: concretagem identificada na base histórica ou em snapshot da mesma etapa. Zero indica ausência de concretagem registrada neste recorte, não paralisação da frente.';
 }else{
   if(text)text.textContent='Execução registrada: '+(EVOLUTION.total_estacas_execucao_registrada??'—')+
     ' estacas contabilizadas por eixo, frente às '+AX.reduce((a,b)=>a+b,0)+
     ' previstas. Inclui base histórica e totais homologados de etapas diferentes; não corresponde a avanço físico-contratual homogêneo.';
   if(legend)legend.textContent='Verde: concretagem identificada; bege: execução homologada cujo estágio final não foi detalhado. E09: 25 executadas versus 24 projetadas (+1), sem classificação de locação ou resistência.';
 }
}

function makeChooser(){
 const root=$('axisChooser');if(!root)return;
 root.innerHTML=AX.map((_,i)=>'<button type="button" data-axis="'+(i+1)+'" aria-pressed="'+String(i+1===currentAxis)+'">E'+String(i+1).padStart(2,'0')+'</button>').join('');
 root.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>syncAxis(Number(b.dataset.axis))));
}
function drawEvidence(){
 const root=$('evidenceRows');if(!root)return;
 const n=currentAxis, code=axisCode(n), published=currentEvents().filter(e=>e.target===code);
 const p=currentProgress(n);
 const field=p?.origem_execucao==='campo_homologado';
 const origin=field?'Homologado em '+dateBR(p.data_execucao_campo):'Base histórica, sem identificação individual das estacas';
 const systemRows=[
   ['Estacas previstas em projeto',p?.previstas_projeto??AX[n-1]],
   ['Estacas com execução registrada',p?.executadas_registradas??HIST[n-1]],
   ['Estacas com concretagem identificada',p?.concretadas_identificadas??HIST[n-1]],
   ['Origem da execução acumulada',origin],
   ['Blocos (base histórica)',CFG.blocos.historicos_por_eixo[n-1]+' / 1'],
   ['Pilares integralmente concretados',CFG.pilares.historicos_por_eixo[n-1]+' / '+CFG.pilares.previstos_por_eixo],
   ['Apontamentos homologados nesta frente',String(published.length)]
 ];
 if((p?.excedente_executado??0)>0)systemRows.splice(3,0,['Diferença de execução frente ao projeto','+'+p.excedente_executado+' · locação e resistência não determinadas']);
 if(n===3&&EVOLUTION.pilares_E03_concretagem_parcial)
   systemRows.push(['Pilares P03/P04','Metades inferiores concretadas; topo não confirmado']);
 root.innerHTML='<p class="small-note">Eixo '+String(n).padStart(2,'0')+' · quantidades agregadas por eixo. Nenhum elemento individual é colorido como concluído sem locação associada.</p>'+
   systemRows.map(([a,b])=>'<div class="evidence-item"><span>'+escapeHTML(a)+'</span><strong>'+escapeHTML(b)+'</strong></div>').join('')+
   (published.length?published.map(e=>'<div class="evidence-item"><span>'+escapeHTML(dateBR(e.date))+' · '+escapeHTML(e.activity)+'</span><strong>Homologado</strong></div>').join(''):
   '<p class="small-note">Nenhum evento homologado publicado para esta frente. A ausência de observação não indica paralisação.</p>');
}

function redrawTimeline(){
 const sel=$('timelineSelect'), root=$('timelineContent'), count=$('timelineCount');if(!sel||!root||!count)return;
 const events=currentEvents().filter(e=>/^\d{4}-\d{2}-\d{2}$/.test(e.date));
 const dates=[...new Set(events.map(e=>e.date))].sort();
 const previous=sel.value;
 sel.innerHTML=dates.length?dates.map(d=>'<option value="'+d+'">'+dateBR(d)+'</option>').join(''):'<option value="">Sem datas de registros homologados</option>';
 sel.disabled=!dates.length;
 if(previous&&dates.includes(previous))sel.value=previous;
 else if(dates.length)sel.value=dates[dates.length-1];
 const chosen=sel.value, listed=events.filter(e=>e.date===chosen);
 count.textContent=dates.length?listed.length+' registros nesta data':'Nenhum evento homologado';
 root.className=dates.length?'timeline-items':'timeline-empty';
 root.innerHTML=dates.length?(listed.length?listed.map(e=>'<div class="timeline-event"><time>'+escapeHTML(e.time||'Data confirmada')+'</time><span>'+escapeHTML(e.target)+' · '+escapeHTML(e.service)+' · '+escapeHTML(e.activity)+'</span></div>').join(''):'<p>Sem eventos homologados para esta data.</p>'):'Não há registros homologados suficientes para reconstruir a obra em datas anteriores. O painel não interpola visitas ausentes e não apresenta uma animação 4D fictícia.';
}
function onSelection(e){
 let d=e.detail||{};if(d.kind==='eixo'&&Number.isInteger(d.index))syncAxis(d.index,true);
 currentService=d.service||'estacas';
 const inspector=$('elementInspector');
 if(inspector){
   const area=d.kind==='vao'?'Vão '+d.index:'Eixo '+String(d.index||currentAxis).padStart(2,'0');
   inspector.textContent=area+' · '+(label[currentService]||'Sistema estrutural')+'. Seleção geométrica ilustrativa: não há identificação individual nem atesto da peça representada.';
 }
}
renderSummary();renderFieldProgress();makeBars();makeChooser();
document.querySelectorAll('[data-progress-mode]').forEach(button=>button.addEventListener('click',()=>{
 const next=button.dataset.progressMode;
 if(next!=='execucao'&&next!=='concretagem')return;
 progressMode=next;makeBars();
}));
const sel=$('timelineSelect');if(sel)sel.addEventListener('change',redrawTimeline);
window.addEventListener('certare:select',onSelection);
window.addEventListener('certare:public-data',()=>{redrawTimeline();drawEvidence()});
redrawTimeline();drawEvidence();
})();
