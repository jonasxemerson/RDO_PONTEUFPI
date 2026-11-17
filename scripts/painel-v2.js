/* CERTARE V2: interface documental sem criar datas, quantidades ou aceites. */
(function(){
'use strict';
const CFG=JSON.parse(document.getElementById('certare-config').textContent);
const AX=CFG.estacas.previstas_por_eixo,HIST=CFG.estacas.historicas_por_eixo;
const $=id=>document.getElementById(id);
let currentAxis=7, currentService='estacas';
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
 const values=[
 ['kpiEixos',String(CFG.eixos)+' eixos'],
 ['metaVaos',String(CFG.vaos)+' vãos no modelo'],
 ['kpiEstacas',sum(HIST)+' / '+sum(AX)],
 ['kpiBlocos',sum(CFG.blocos.historicos_por_eixo)+' / '+CFG.blocos.previstos_total],
 ['kpiPilares',sum(CFG.pilares.historicos_por_eixo)+' / '+CFG.eixos*CFG.pilares.previstos_por_eixo],
 ['progressContext','Base parcialmente conciliada: '+sum(HIST)+' estacas concretadas registradas de '+sum(AX)+' previstas no modelo. Não equivale a medição nem curva de avanço contratual.']
 ];
 for(const [id,value] of values){let el=$(id);if(el)el.textContent=value}
}
function makeBars(){
 const root=$('axisProgress');if(!root)return;
 root.innerHTML=AX.map((planned,i)=>{
  const hist=HIST[i], n=i+1, pct=Math.max(0,Math.min(100,hist/planned*100));
  return '<button type="button" data-axis="'+n+'" aria-pressed="'+String(n===currentAxis)+'" aria-label="Eixo '+n+', '+hist+' de '+planned+' estacas na base histórica"><span class="axis-progress-label">E'+String(n).padStart(2,'0')+'</span><span class="axis-progress-track"><span class="axis-progress-fill" style="width:'+pct.toFixed(2)+'%"></span></span><span class="axis-progress-count">'+hist+' / '+planned+'</span></button>';
 }).join('');
 root.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>syncAxis(Number(b.dataset.axis))));
}
function makeChooser(){
 const root=$('axisChooser');if(!root)return;
 root.innerHTML=AX.map((_,i)=>'<button type="button" data-axis="'+(i+1)+'" aria-pressed="'+String(i+1===currentAxis)+'">E'+String(i+1).padStart(2,'0')+'</button>').join('');
 root.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>syncAxis(Number(b.dataset.axis))));
}
function drawEvidence(){
 const root=$('evidenceRows');if(!root)return;
 const n=currentAxis, code=axisCode(n), published=currentEvents().filter(e=>e.target===code);
 const systemRows=[['Estacas concretadas (base reconciliada)',HIST[n-1]+' / '+AX[n-1]],['Blocos (referência histórica)',CFG.blocos.historicos_por_eixo[n-1]+' / 1'],['Pilares concretados (base reconciliada)',CFG.pilares.historicos_por_eixo[n-1]+' / '+CFG.pilares.previstos_por_eixo],['Eventos homologados para acompanhamento',String(published.length)]];
 root.innerHTML='<p class="small-note">Eixo '+String(n).padStart(2,'0')+' · unidades conhecidas somente por agrupamento, sem posição individual confirmada.</p>'+systemRows.map(([a,b])=>'<div class="evidence-item"><span>'+a+'</span><strong>'+b+'</strong></div>').join('')+
 (published.length?published.map(e=>'<div class="evidence-item"><span>'+escapeHTML(dateBR(e.date))+' · '+escapeHTML(e.activity)+'</span><strong>Registro homologado</strong></div>').join(''):'<p class="small-note">Nenhum evento homologado publicado para esta frente. Ausência de publicação não indica paralisação.</p>');
}
function redrawTimeline(){
 const sel=$('timelineSelect'), root=$('timelineContent'), count=$('timelineCount');if(!sel||!root||!count)return;
 const events=currentEvents().filter(e=>/^\d{4}-\d{2}-\d{2}$/.test(e.date));
 const dates=[...new Set(events.map(e=>e.date))].sort();
 const previous=sel.value;
 sel.innerHTML=dates.length?dates.map(d=>'<option value="'+d+'">'+dateBR(d)+'</option>').join(''):'<option value="">Sem datas de registros homologados</option>';
 sel.disabled=!dates.length;
 if(previous&&dates.includes(previous))sel.value=previous;
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
renderSummary();makeBars();makeChooser();
const sel=$('timelineSelect');if(sel)sel.addEventListener('change',redrawTimeline);
window.addEventListener('certare:select',onSelection);
window.addEventListener('certare:public-data',()=>{redrawTimeline();drawEvidence()});
redrawTimeline();drawEvidence();
})();
