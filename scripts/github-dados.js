/* Leitura da fonte GitHub. Sem token de escrita no cliente. */
(() => {
  'use strict';
  const nav = document.getElementById('nav');
  const main = document.querySelector('main');
  if (!nav || !main) return;

  const button = document.createElement('button');
  button.dataset.page = 'github';
  button.textContent = '☁   Dados GitHub';
  nav.appendChild(button);

  const page = document.createElement('section');
  page.id = 'page-github';
  page.className = 'view';
  page.innerHTML = `<div class="panel">
    <div class="row"><div><h2>Dados versionados no GitHub</h2>
      <p class="sub">Observações técnicas com origem e situação de validação.</p></div>
      <button class="btn" id="ghRefresh">Atualizar leitura</button></div>
    <div id="ghStatus" class="section">Carregando dados do GitHub...</div>
    <div id="ghCards" class="kpis section" style="margin-top:16px"></div>
    <div class="section"><h3>Histórico de observações</h3>
      <p class="mini">Totais reportados são estados acumulados; não representam produção adicional.</p>
      <div class="tablewrap"><table><thead><tr><th>Data</th><th>Frente</th><th>Atividade</th>
      <th>Situação</th><th>Quantidade / tipo</th><th>Observações</th></tr></thead>
      <tbody id="ghRows"></tbody></table></div></div>
    <div class="section"><h3>Etapas inferidas</h3><div id="ghInferences" class="list section"></div></div>
    <div class="section"><h3>Pendências de planejamento</h3><div id="ghPlanning" class="list section"></div></div>
    <div class="callout section">Fonte central: arquivos data/ do GitHub. A base local legada permanece separada até reconciliação.
    Novos registros devem ser inseridos por commit ou Pull Request, nunca com token de escrita embutido no site.</div>
  </div>`;
  main.appendChild(page);
  const mainKpis = main.querySelector(':scope > .kpis');
  if (mainKpis) {
    const notice = document.createElement('div');
    notice.id = 'ghMainSummary';
    notice.className = 'callout';
    notice.style.margin = '0 0 16px';
    notice.textContent = 'GitHub: aguardando leitura do registro de campo versionado.';
    mainKpis.insertAdjacentElement('afterend', notice);
  }

  const $ = id => document.getElementById(id);
  const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);
  const date = input => {
    if (!input) return 'data não informada';
    const parts = String(input).slice(0, 10).split('-');
    return parts.length === 3 ? parts[2] + '/' + parts[1] + '/' + parts[0] : String(input);
  };
  let data = null;

  function render() {
    const events = data.events || [];
    const inferences = data.inferences || [];
    const planning = data.planning_requests || [];
    const byDate = (a, b) => (a.date + ' ' + (a.time || '')).localeCompare(b.date + ' ' + (b.time || ''));
    const last = predicate => events.filter(predicate).sort(byDate).slice(-1)[0];
    const latestMetric = (target, metric) => last(e => e.target === target && e.state === 'snapshot' && e.metric === metric);
    const currentDrilling = target => last(e => e.target === target && e.service === 'estacas' &&
      e.quantity_kind === 'ordinal_em_execucao' && e.state === 'em_andamento');
    const e7 = latestMetric('E07', 'estacas_feitas_etapa_indefinida');
    const e9 = latestMetric('E09', 'estacas_feitas_etapa_indefinida');
    const e8 = latestMetric('E08', 'estacas_concretadas');
    const e8Sleeves = latestMetric('E08', 'camisas_sem_concretagem');
    const e3Pillars = latestMetric('E03', 'pilares_concretados');
    const e7Drilling = currentDrilling('E07'), e9Drilling = currentDrilling('E09');
    const long2 = last(e => e.service === 'longarina' && e.element === 'Longarina 2' && e.activity === 'Desforma concluída');
    const long3 = last(e => e.service === 'longarina' && e.element === 'Longarina 3' && e.activity === 'Instalação de fôrmas');
    const validated = events.filter(e => e.validation === 'validado_campo').length;
    const totalText = (event, fallback = '—') => event ? event.quantity : fallback;
    const dateText = event => event ? ' · ' + date(event.date) : '';
    const notice = $('ghMainSummary');
    if (notice) notice.textContent = 'Última atualização GitHub: ' + events.length + ' registros. ' +
      'Eixo 8: ' + (e8 ? e8.quantity + ' estacas concretadas' : 'sem novo total') +
      '; Eixo 9: ' + (e9 ? e9.quantity + ' “feitas”' : 'sem novo total') +
      (e9Drilling ? ', perfurando a ' + e9Drilling.quantity + 'ª' : '') +
      '; Eixo 7: ' + (e7 ? e7.quantity + ' relatadas' : 'sem novo total') +
      (e7Drilling ? ', perfurando a ' + e7Drilling.quantity + 'ª' : '') +
      '. Totais, ordinais e produção histórica não são somados entre si.';

    $('ghStatus').innerHTML = '<div class="warning"><b>Situação:</b> ' + safe(data.approval_state) +
      ' · ' + events.length + ' observações · ' + inferences.length + ' inferência(s)' +
      ' · ' + planning.length + ' pendência(s) de planejamento.' +
      ' Ausência de registro não equivale a paralisação; relatos ainda exigem validação de campo.</div>';

    const kpis = [
      ['Eixo 8 · concretagem', totalText(e8), 'Acumulado informado' + dateText(e8) +
        (e8Sleeves ? ' · ' + e8Sleeves.quantity + ' outras somente com camisas' : '')],
      ['Eixo 9 · estacas', totalText(e9), '“Feitas”, etapa indefinida' + dateText(e9) +
        (e9Drilling ? ' · ' + e9Drilling.quantity + 'ª em perfuração em ' + date(e9Drilling.date) : '')],
      ['Eixo 7 · estacas', totalText(e7), 'Total relatado' + dateText(e7) +
        (e7Drilling ? ' · ' + e7Drilling.quantity + 'ª em perfuração em ' + date(e7Drilling.date) : '')],
      ['Longarina 2', long2 ? 'Desformada' : '—', long2 ? 'Registro em ' + date(long2.date) : 'Sem novo registro'],
      ['Longarina 3', long3 ? long3.quantity + '%' : '—',
        long3 ? 'Fôrmas instaladas parcialmente em ' + date(long3.date) : 'Sem novo registro'],
      ['Pilares · Eixo 3', totalText(e3Pillars), 'Concretados (mesmo total de 04/11)' + dateText(e3Pillars) +
        ' · 2 outros em armação'],
      ['Registros GitHub', events.length, validated + ' homologado(s); demais são relatos técnicos']
    ];
    $('ghCards').innerHTML = kpis.map(k => '<div class="kpi"><div class="label">' + safe(k[0]) + '</div>' +
      '<div class="num">' + safe(k[1]) + '</div><div class="mini">' + safe(k[2]) + '</div></div>').join('');

    $('ghRows').innerHTML = events.slice().sort((a,b) => -byDate(a,b)).map(e => {
      const qty = e.quantity == null ? '—' : safe(e.quantity) + ' (' + safe(e.quantity_kind) + ')';
      return '<tr><td>' + safe(date(e.date)) + '<div class="mini">' + safe(e.time) + '</div></td>' +
        '<td>' + safe(e.target) + '<div class="mini">' + safe(e.element || '') + '</div></td>' +
        '<td>' + safe(e.activity) + '</td><td><span class="badge">' + safe(e.state) + '</span></td>' +
        '<td>' + qty + '</td><td>' + safe(e.detail || '') +
        (e.review ? '<div class="mini">Revisão pendente</div>' : '') + '</td></tr>';
    }).join('');
    $('ghInferences').innerHTML = inferences.length ? inferences.map(e =>
      '<div class="item"><b>' + safe(e.element) + ' · ' + safe(e.activity) + '</b>' +
      '<p>Concluída por inferência até ' + safe(date(e.completed_no_later_than)) +
      '; data exata desconhecida. ' + safe(e.reason || '') + '</p></div>').join('') :
      '<div class="empty">Nenhuma inferência registrada.</div>';
    const planningRoot = $('ghPlanning');
    if (planningRoot) planningRoot.innerHTML = planning.length ? planning.map(x =>
      '<div class="item"><b>' + safe(x.title) + '</b><p>' +
      safe(x.description) + ' — ' + safe(x.caution || '') + '</p></div>').join('') :
      '<div class="empty">Nenhuma pendência cadastrada.</div>';
  }

  async function refresh() {
    $('ghStatus').textContent = 'Lendo repositório GitHub...';
    try {
      const makeUrl = path => {
        const url = new URL(path, document.baseURI);
        url.searchParams.set('t', String(Date.now()));
        return url.toString();
      };
      const listing = await fetch(makeUrl('data/manifest.json'), { cache: 'no-store' });
      if (!listing.ok) throw new Error('Manifesto HTTP ' + listing.status);
      const manifest = await listing.json();
      if (manifest.schema_version !== 1 || !Array.isArray(manifest.files)) {
        throw new Error('Manifesto inválido');
      }
      const files = await Promise.all(manifest.files.map(async path => {
        if (typeof path !== 'string' || !/^data\/observacoes-\d{4}-\d{2}\.json$/.test(path)) {
          throw new Error('Caminho de dados não permitido');
        }
        const result = await fetch(makeUrl(path), { cache: 'no-store' });
        if (!result.ok) throw new Error(path + ' HTTP ' + result.status);
        const doc = await result.json();
        if (doc.schema_version !== 1 || !Array.isArray(doc.events)) {
          throw new Error('Estrutura inesperada em ' + path);
        }
        return doc;
      }));
      const incoming = {
        schema_version: 1,
        approval_state: files.some(d => d.approval_state === 'revisao_pendente') ?
          'revisao_pendente' : 'registros_publicados',
        events: files.flatMap(d => d.events),
        inferences: files.flatMap(d => d.inferences || []),
        planning_requests: files.flatMap(d => d.planning_requests || [])
      };
      data = incoming;
      render();
    } catch (error) {
      $('ghStatus').innerHTML = `<div class="warning">Não foi possível ler a fonte central
        (${safe(error.message)}). Publique o repositório completo no GitHub Pages.
        A aba não altera seus registros locais.</div>`;
    }
  }
  $('ghRefresh').addEventListener('click', refresh);
  refresh();
  setInterval(() => { if (document.visibilityState !== 'hidden') refresh(); }, 300000);
})();