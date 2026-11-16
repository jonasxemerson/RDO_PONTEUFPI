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
    const latest = (target, service) => events
      .filter(e => e.target === target && e.service === service && e.quantity_kind === 'total_reportado')
      .sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time))
      .slice(-1)[0];
    const e7 = latest('E07', 'estacas'), e9 = latest('E09', 'estacas');
    const validated = events.filter(e => e.validation === 'validado_campo').length;
    const notice = $('ghMainSummary');
    if (notice) notice.textContent = 'Atualização GitHub: ' + events.length + ' registros técnicos. Eixo 9: ' +
      (e9 ? e9.quantity + ' estacas “feitas” (' + date(e9.date) + ')' : 'sem dados') +
      ' · Eixo 7: ' + (e7 ? e7.quantity + ' estacas relatadas (' + date(e7.date) + ')' : 'sem dados') +
      '. Etapa exata pendente de validação; não incluída automaticamente nas estacas concretadas.';
    $('ghStatus').innerHTML = `<div class="warning"><b>Situação:</b> ${safe(data.approval_state)}
      · ${events.length} observações · ${inferences.length} inferência(s).
      Sem registro não significa obra paralisada.</div>`;
    const kpis = [
      ['Eixo 9', e9 ? e9.quantity : '—', e9 ? '“Feitas”, etapa não definida — ' + date(e9.date) : 'Sem dado'],
      ['Eixo 7', e7 ? e7.quantity : '—', e7 ? 'Informadas, etapa não definida — ' + date(e7.date) : 'Sem dado'],
      ['Observações', events.length, 'Histórico registrado no GitHub'],
      ['Validadas em campo', validated, 'Relatos não homologados ficam separados']
    ];
    $('ghCards').innerHTML = kpis.map(k => `<div class="kpi"><div class="label">${safe(k[0])}</div>
      <div class="num">${safe(k[1])}</div><div class="mini">${safe(k[2])}</div></div>`).join('');
    $('ghRows').innerHTML = events.slice().sort((a, b) =>
      (b.date + b.time).localeCompare(a.date + a.time)).map(e => {
      const qty = e.quantity == null ? '—' : safe(e.quantity) + ' (' + safe(e.quantity_kind) + ')';
      return `<tr><td>${safe(date(e.date))}<div class="mini">${safe(e.time)}</div></td>
        <td>${safe(e.target)}<div class="mini">${safe(e.element || '')}</div></td>
        <td>${safe(e.activity)}</td><td><span class="badge">${safe(e.state)}</span></td>
        <td>${qty}</td><td>${safe(e.detail || '')}
        ${e.review ? '<div class="mini">Revisão pendente</div>' : ''}</td></tr>`;
    }).join('');
    $('ghInferences').innerHTML = inferences.length ? inferences.map(e =>
      `<div class="item"><b>${safe(e.element)} · ${safe(e.activity)}</b>
        <p>Concluída por inferência até ${safe(date(e.completed_no_later_than))};
        data exata desconhecida. ${safe(e.reason || '')}</p></div>`).join('') :
      '<div class="empty">Nenhuma inferência registrada.</div>';
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
        inferences: files.flatMap(d => d.inferences || [])
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