
'use strict';
const CONFIG=JSON.parse(document.getElementById('certare-config').textContent);
const AX=CONFIG.estacas.previstas_por_eixo,HIST=CONFIG.estacas.historicas_por_eixo;
const $=s=>document.querySelector(s), safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let events=[];let selected=7;
function drawBridge(){window.Certare4D?.setSelection(selected)}
function selectAxis(i){
 selected=i;drawBridge();
 $('#axisTitle').textContent='Eixo '+String(i).padStart(2,'0');
 const code='E'+String(i).padStart(2,'0'),specific=events.filter(e=>e.target===code);
 const axis=CONFIG.consolidacao?.evolucao_fisica?.estacas_por_eixo?.[i-1]||null;
 const byDate=(a,b)=>String(a.date+' '+(a.time||'')).localeCompare(String(b.date+' '+(b.time||'')));
 const recent=(metric)=>specific.filter(e=>e.state==='snapshot'&&e.metric===metric).sort(byDate).at(-1);
 const concrete=recent('estacas_concretadas'),undefinedStep=recent('estacas_feitas_etapa_indefinida');
 const sleeves=recent('camisas_sem_concretagem');
 const ordinal=specific.filter(e=>e.quantity_kind==='ordinal_em_execucao').sort(byDate).at(-1);
 const ordinalValid=ordinal&&(!axis?.data_execucao_campo||ordinal.date>=axis.data_execucao_campo);
 const ordinalText=ordinal?(ordinal.quantity+'ª · '+ordinal.activity+(ordinalValid?'':' (registro anterior, não é estágio atual)')):'Não informado';
 const field=axis?.origem_execucao==='campo_homologado';
 const prov=field?'Campo homologado em '+axis.data_execucao_campo:'Base histórica sem data individual determinada';
 let rows=[['Estacas previstas em projeto',axis?.previstas_projeto??AX[i-1]],
   ['Execução registrada · acumulado',axis?.executadas_registradas??HIST[i-1]],
   ['Concretagem identificada · acumulado',axis?.concretadas_identificadas??HIST[i-1]],
   ['Fonte do acumulado',prov],
   ['Concretadas · relato da mesma etapa',concrete?concrete.quantity+' (já conciliadas)':'Sem novo snapshot explícito'],
   ['Relato anterior · etapa não definida',undefinedStep?undefinedStep.quantity:'Não informado'],
   ['Somente camisas sem concretagem',sleeves?sleeves.quantity:'Não informado'],
   ['Etapa ordinal informada',ordinalText],
   ['Registros homologados nesta frente',specific.length]];
 if(axis?.excedente_executado>0)rows.splice(3,0,['Excedente de execução sobre projeto','+'+axis.excedente_executado+' · locação/resistência não determinadas']);
 if(i===3&&CONFIG.consolidacao?.evolucao_fisica?.pilares_E03_concretagem_parcial)
   rows.push(['Pilares E03-P03 e E03-P04','Metades inferiores concretadas; topo não confirmado']);
 $('#axisRows').innerHTML=rows.map(([k,v])=>'<div class="axis-row"><span>'+safe(k)+'</span><strong>'+safe(v)+'</strong></div>').join('');
 $('#axisStatus').textContent=field?'Execução homologada · etapa final a distinguir':'Registro histórico · sem atesto por estaca';
}
function date(v){if(!v)return '—';let p=v.slice(0,10).split('-');return p.length===3?p[2]+'/'+p[1]+'/'+p[0]:v}
async function readData(){try{let manifest=await fetch('data/manifest.json',{cache:'no-store'});if(!manifest.ok)throw Error('Manifesto indisponível');let m=await manifest.json();if(!Array.isArray(m.files))throw Error('Manifesto inválido');let docs=await Promise.all(m.files.filter(p=>/^data\/observacoes-\d{4}-\d{2}\.json$/.test(p)).map(async p=>{let r=await fetch(p,{cache:'no-store'});if(!r.ok)throw Error('Arquivo indisponível');return r.json()}));events=docs.flatMap(d=>Array.isArray(d.events)?d.events:[]);let seen=new Set();events=events.filter(e=>{if(!e.id||seen.has(e.id))return false;seen.add(e.id);return true});window.CertarePublicEvents=events;window.CertarePublicInferences=docs.flatMap(d=>Array.isArray(d.inferences)?d.inferences:[]);window.dispatchEvent(new CustomEvent('certare:public-data'));let listed=events.filter(e=>!['seguranca','qualidade'].includes(e.service)).sort((a,b)=>String(b.date+' '+(b.time||'')).localeCompare(String(a.date+' '+(a.time||'')))).slice(0,5);$('#noticePending').hidden=listed.length>0;$('#updates').innerHTML=listed.length?listed.map(e=>'<div class="update"><time>'+safe(date(e.date))+'</time><div><strong>'+safe(e.activity)+' · '+safe(e.target)+'</strong><span class="chip">Homologado para acompanhamento</span><p>'+safe(e.element||'')+' · '+safe(e.state||'Registro técnico')+'</p></div></div>').join(''):'<p class="subtle">Não há observações publicadas.</p>';let last=events.map(e=>e.date).filter(Boolean).sort().at(-1);$('#headerDate').textContent=last?'Último registro: '+date(last):'Sem registro consolidado';$('#dataStatus').textContent=events.length+' registros homologados para acompanhamento · não equivalem a medição';selectAxis(selected)}catch(err){$('#updates').innerHTML='<p class="error">Registros temporariamente indisponíveis.</p>';$('#dataStatus').textContent='Não foi possível consultar a base GitHub; indicadores históricos permanecem identificados.';window.CertarePublicEvents=[];$('#noticePending').hidden=false;window.dispatchEvent(new CustomEvent('certare:public-data'));selectAxis(selected)}}
document.querySelectorAll('.nav a').forEach(a=>a.onclick=()=>{document.querySelectorAll('.nav a').forEach(b=>b.classList.remove('active'));a.classList.add('active')});window.Certare4D?.init((kind,index)=>{if(kind==='eixo')selectAxis(index)});selectAxis(7);readData();
