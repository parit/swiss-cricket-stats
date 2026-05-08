(() => {
  // Capture script base URL synchronously at load time for default base-url resolution.
  const _scriptSrc = document.currentScript?.src;
  const _scriptBase = _scriptSrc ? new URL('.', _scriptSrc).href.replace(/\/$/, '') : null;

  const TEMPLATE = `
<style>
:host {
  display: block;
  font-family: Arial, sans-serif;
  --cs-accent: #00b5ad;
  --cs-bg:     #f4f4f4;
  --cs-surf:   #fff;
  --cs-text:   #222;
  --cs-muted:  #666;
  --cs-subtle: #555;
  --cs-border: #eee;
  --cs-ctrl:   #ccc;
  --cs-shadow: rgba(0,0,0,.1);
  --cs-pos:    #27ae60;
  --cs-neg:    #e74c3c;
  --cs-badge:  #222;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
[hidden] { display: none !important; }
.root { background: var(--cs-bg); padding: 16px; border-radius: 8px; color: var(--cs-text); }
.loading, .error { padding: 24px; text-align: center; color: var(--cs-muted); }

.selector { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.selector label { font-weight: 600; font-size: 0.9rem; }
.selector select { padding: 8px 12px; font-size: 0.9rem; border: 1px solid var(--cs-ctrl); border-radius: 4px; background: var(--cs-surf); cursor: pointer; min-width: 260px; }

.view-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.view-header h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }
.back-btn { background: none; border: none; color: var(--cs-muted); cursor: pointer; font-size: 0.85rem; padding: 0; font-family: inherit; }
.back-btn:hover { color: var(--cs-accent); }

.tabs { display: flex; border-bottom: 2px solid var(--cs-accent); margin-bottom: 24px; }
.tab-btn { padding: 10px 24px; font-size: 0.9rem; font-weight: 600; border: none; background: none; cursor: pointer; border-radius: 4px 4px 0 0; color: var(--cs-subtle); font-family: inherit; }
.tab-btn.active { background: var(--cs-accent); color: #fff; }

.sc-controls { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.view-toggle { display: flex; gap: 8px; }
.view-btn { padding: 6px 16px; font-size: 0.85rem; cursor: pointer; border: 1px solid var(--cs-ctrl); border-radius: 4px; background: var(--cs-surf); font-family: inherit; }
.view-btn.active { background: var(--cs-accent); color: #fff; border-color: var(--cs-accent); }
.team-filter { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }
.team-filter label { font-weight: 600; }
.cs-team-sel { padding: 6px 10px; font-size: 0.85rem; border: 1px solid var(--cs-ctrl); border-radius: 4px; background: var(--cs-surf); cursor: pointer; font-family: inherit; }

.cs-table { width: 100%; border-collapse: collapse; background: var(--cs-surf); border-radius: 4px; overflow: hidden; box-shadow: 0 1px 4px var(--cs-shadow); }
.cs-table thead { background: var(--cs-accent); color: #fff; }
.cs-table th, .cs-table td { padding: 8px 10px; border-bottom: 1px solid var(--cs-border); font-size: 0.85rem; text-align: left; }
.cs-table td.dt { white-space: nowrap; color: var(--cs-muted); }
.cs-table td.sc-team { font-weight: 600; white-space: nowrap; }
.cs-table td.score, .cs-table td.center { white-space: nowrap; text-align: center; }
.cs-table td.result { color: var(--cs-pos); font-weight: 500; }
.cs-table tbody tr:hover { background: #f0f8ff; }
td.pos { color: var(--cs-pos); font-weight: bold; }
td.neg { color: var(--cs-neg); font-weight: bold; }

.cs-team-btn { background: none; border: none; padding: 0; cursor: pointer; color: inherit; font-size: inherit; font-family: inherit; border-bottom: 1px dotted var(--cs-muted); font-weight: 600; text-align: left; }
.cs-team-btn:hover { color: var(--cs-accent); border-bottom-color: var(--cs-accent); }
.cs-venue-btn { background: none; border: none; padding: 0; cursor: pointer; color: inherit; font-size: inherit; font-family: inherit; border-bottom: 1px dotted var(--cs-muted); text-align: left; }
.cs-venue-btn:hover { color: var(--cs-accent); border-bottom-color: var(--cs-accent); }

.tourn-pill { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; color: #fff; white-space: nowrap; letter-spacing: 0.02em; border: none; cursor: pointer; font-family: inherit; }
.tourn-pill:hover { opacity: 0.85; }

.pt-section { margin-bottom: 32px; }
.pt-group-header { font-size: 1rem; background: var(--cs-accent); color: #fff; padding: 8px 12px; border-radius: 4px 4px 0 0; font-weight: 600; }
.sc-subtitle { background: none; color: var(--cs-text); padding: 0 0 8px; border-bottom: 2px solid var(--cs-accent); border-radius: 0; margin-bottom: 16px; font-size: 1rem; font-weight: 600; }

.match-section { margin-bottom: 32px; }
.match-section h3 { background: none; color: var(--cs-text); padding: 0 0 8px; border-bottom: 2px solid var(--cs-accent); border-radius: 0; margin-bottom: 16px; font-size: 1rem; font-weight: 600; }

.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.match-card { background: var(--cs-surf); border-radius: 8px; padding: 16px; box-shadow: 0 1px 4px var(--cs-shadow); display: flex; flex-direction: column; gap: 12px; }
.card-meta { display: flex; justify-content: space-between; align-items: flex-start; font-size: 0.8rem; color: var(--cs-muted); }
.badge { background: var(--cs-badge); color: #fff; border-radius: 12px; padding: 2px 10px; font-size: 0.75rem; white-space: nowrap; flex-shrink: 0; margin-left: 8px; }
.badge.upcoming { background: var(--cs-accent); }
.card-scores { display: flex; flex-direction: column; gap: 6px; }
.card-team-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.card-score { font-size: 0.9rem; white-space: nowrap; }
.card-score.winner { color: var(--cs-accent); font-weight: 600; }
.card-result { font-size: 0.85rem; font-weight: 600; border-top: 1px solid var(--cs-border); padding-top: 10px; }

.empty-msg { color: var(--cs-muted); font-style: italic; padding: 12px 0; font-size: 0.9rem; }
.muted { color: var(--cs-muted); font-size: 0.8rem; }
</style>
<div class="root"><div class="loading">Loading…</div></div>`;

  class CricketStats extends HTMLElement {
    static get observedAttributes() { return ['src', 'season', 'base-url', 'tournament', 'team', 'venue']; }
    _navStack = [];

    connectedCallback() {
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = TEMPLATE;
      this.shadowRoot.querySelector('.root').addEventListener('click', e => this._onClick(e));
      this._load();
    }

    attributeChangedCallback() {
      if (this.shadowRoot) this._load();
    }

    _resolveUrl() {
      const src = this.getAttribute('src');
      if (src) return src;
      const season = this.getAttribute('season');
      if (!season) return null;
      const base = (this.getAttribute('base-url') || (_scriptBase ? `${_scriptBase}/..` : null));
      if (!base) return null;
      return `${base.replace(/\/$/, '')}/${season}/data.json`;
    }

    async _load() {
      const src = this._resolveUrl();
      if (!src) return;
      try {
        const res = await fetch(src, { cache: 'no-cache' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        this._data = await res.json();
        const teamAttr = this.getAttribute('team');
        const tournAttr = this.getAttribute('tournament');
        const venueAttr = this.getAttribute('venue');
        if (teamAttr) {
          const match = this._data.teams.find(t => t.name.toLowerCase() === teamAttr.toLowerCase());
          this._navStack = [{ type: 'team', name: match ? match.name : teamAttr }];
        } else if (tournAttr) {
          const t = this._data.tournaments.find(t => t.slug.includes(tournAttr));
          this._navStack = t ? [{ type: 'tournament', slug: t.slug }] : [{ type: 'home' }];
        } else if (venueAttr) {
          const allGrounds = this._data.tournaments.flatMap(t =>
            [...t.past_matches, ...t.upcoming_matches].map(m => m.ground)
          );
          const match = allGrounds.find(g => g && g.toLowerCase() === venueAttr.toLowerCase());
          this._navStack = [{ type: 'venue', name: match || venueAttr }];
        } else {
          this._navStack = [{ type: 'home' }];
        }
        this._renderView();
      } catch (e) {
        this.shadowRoot.querySelector('.root').innerHTML =
          `<div class="error">Failed to load: ${e.message}</div>`;
      }
    }

    _onClick(e) {
      if (e.target.closest('[data-cs-back]')) { this._back(); return; }
      const team = e.target.closest('[data-cs-team]');
      if (team) { this._navTo({ type: 'team', name: team.dataset.csTeam }); return; }
      const tourn = e.target.closest('[data-cs-tourn]');
      if (tourn) { this._navTo({ type: 'tournament', slug: tourn.dataset.csTourn }); return; }
      const venue = e.target.closest('[data-cs-venue]');
      if (venue) { this._navTo({ type: 'venue', name: venue.dataset.csVenue }); return; }
      const tabBtn = e.target.closest('.tab-btn');
      if (tabBtn) { this._switchTab(tabBtn); return; }
      const viewBtn = e.target.closest('.view-btn');
      if (viewBtn) { this._switchView(viewBtn); return; }
    }

    _navTo(view) {
      this._navStack.push(view);
      this._renderView();
    }

    _back() {
      if (this._navStack.length > 1) this._navStack.pop();
      this._renderView();
    }

    _renderView() {
      const root = this.shadowRoot.querySelector('.root');
      const cur = this._navStack[this._navStack.length - 1];
      switch (cur.type) {
        case 'home':
          root.innerHTML = this._homeHTML();
          this._wireHome();
          break;
        case 'tournament':
          root.innerHTML = this._tournHTML(cur.slug);
          this._wireTeamFilter();
          break;
        case 'team':
          root.innerHTML = this._teamHTML(cur.name);
          this._wireTeamFilter();
          break;
        case 'venue':
          root.innerHTML = this._venueHTML(cur.name);
          this._wireTeamFilter();
          break;
      }
    }

    _switchTab(btn) {
      const container = btn.closest('.view-tabs');
      if (!container) return;
      container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      container.querySelectorAll('.tab-panel').forEach(p => {
        p.hidden = p.dataset.tab !== btn.dataset.tab;
      });
    }

    _switchView(btn) {
      const panel = btn.closest('.tab-panel') || btn.closest('.root');
      if (!panel) return;
      panel.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const isCards = btn.dataset.view === 'cards';
      panel.querySelectorAll('.list-view').forEach(el => el.hidden = isCards);
      panel.querySelectorAll('.cards-view').forEach(el => el.hidden = !isCards);
    }

    _wireHome() {
      const root = this.shadowRoot.querySelector('.root');
      const sel = root.querySelector('#cs-tourn');
      const pre = this.getAttribute('tournament');
      if (pre) {
        const opt = [...sel.options].find(o => o.value.includes(pre));
        if (opt) sel.value = opt.value;
      }
      this._updateHomeContent(sel.value);
      sel.addEventListener('change', () => this._updateHomeContent(sel.value));
    }

    _updateHomeContent(slug) {
      const root = this.shadowRoot.querySelector('.root');
      const t = this._data.tournaments.find(t => t.slug === slug);
      if (!t) return;
      root.querySelector('#cs-pt-panel').innerHTML = this._renderPT(t.points_table);
      root.querySelector('#cs-sc-panel').innerHTML = this._renderSC(t.past_matches, t.upcoming_matches, false);
      this._wireTeamFilter();
    }

    _wireTeamFilter() {
      const root = this.shadowRoot.querySelector('.root');
      const sel = root.querySelector('.cs-team-sel');
      if (!sel) return;
      sel.addEventListener('change', () => {
        const v = sel.value;
        root.querySelectorAll('[data-teams]').forEach(el => {
          el.hidden = v ? !el.dataset.teams.split('|').includes(v) : false;
        });
        root.querySelectorAll('.match-section').forEach(sec => {
          const items = [...sec.querySelectorAll('[data-teams]')];
          if (items.length) sec.hidden = items.every(i => i.hidden);
        });
      });
    }

    // === View builders ===

    _homeHTML() {
      const opts = this._data.tournaments.map(t =>
        `<option value="${t.slug}">${t.abbreviation || t.name}</option>`
      ).join('');
      return `
        <div class="selector">
          <label>Tournament</label>
          <select id="cs-tourn">${opts}</select>
        </div>
        <div class="view-tabs">
          <div class="tabs">
            <button class="tab-btn active" data-tab="pt">Points Table</button>
            <button class="tab-btn" data-tab="sc">Matches</button>
          </div>
          <div class="tab-panel" data-tab="pt" id="cs-pt-panel"></div>
          <div class="tab-panel" data-tab="sc" id="cs-sc-panel" hidden></div>
        </div>`;
    }

    _tournHTML(slug) {
      const t = this._data.tournaments.find(t => t.slug === slug);
      if (!t) return '<div class="error">Tournament not found.</div>';
      const hasPT = t.points_table && Object.keys(t.points_table).length;
      const hasSC = t.past_matches.length || t.upcoming_matches.length;

      let tabBtns = '', panels = '', first = true;
      if (hasPT) {
        const f = first; first = false;
        tabBtns += `<button class="tab-btn${f ? ' active' : ''}" data-tab="pt">Points Table</button>`;
        panels  += `<div class="tab-panel" data-tab="pt"${f ? '' : ' hidden'}>${this._renderPT(t.points_table)}</div>`;
      }
      if (hasSC) {
        const f = first; first = false;
        tabBtns += `<button class="tab-btn${f ? ' active' : ''}" data-tab="sc">Matches</button>`;
        panels  += `<div class="tab-panel" data-tab="sc"${f ? '' : ' hidden'}>${this._renderSC(t.past_matches, t.upcoming_matches, false)}</div>`;
      }

      const backBtn = this._navStack.length > 1 ? `<button class="back-btn" data-cs-back>&larr; Back</button>` : '';
      return `
        <div class="view-header">
          ${backBtn}
          <h2>${t.name}</h2>
        </div>
        <div class="view-tabs">
          <div class="tabs">${tabBtns}</div>
          ${panels}
        </div>`;
    }

    _teamHTML(name) {
      const tl = name.toLowerCase();
      const allPast = [], allUpcoming = [], teamTournaments = [];

      for (const t of this._data.tournaments) {
        const past = t.past_matches
          .filter(m => m.team_1st.toLowerCase() === tl || m.team_2nd.toLowerCase() === tl)
          .map(m => ({ ...m, _tourn: t.name, _slug: t.slug, _color: t.color }));
        const upcoming = t.upcoming_matches
          .filter(m => (m.home_team || '').toLowerCase() === tl || (m.away_team || '').toLowerCase() === tl)
          .map(m => ({ ...m, _tourn: t.name, _slug: t.slug, _color: t.color }));

        allPast.push(...past);
        allUpcoming.push(...upcoming);

        const inPT = Object.values(t.points_table || {}).some(rows =>
          rows.some(r => (r.Team || '').toLowerCase() === tl)
        );
        if (inPT) teamTournaments.push(t);
      }

      allPast.sort((a, b) => a.date.localeCompare(b.date));
      allUpcoming.sort((a, b) => a.date.localeCompare(b.date));

      const hasSC = allPast.length || allUpcoming.length;
      const hasPT = teamTournaments.length > 0;

      let tabBtns = '', panels = '', first = true;

      if (hasSC) {
        const f = first; first = false;
        tabBtns += `<button class="tab-btn${f ? ' active' : ''}" data-tab="sc">Matches</button>`;
        panels  += `<div class="tab-panel" data-tab="sc"${f ? '' : ' hidden'}>${this._renderSC(allPast, allUpcoming, true)}</div>`;
      }
      if (hasPT) {
        const f = first; first = false;
        const ptHTML = teamTournaments.map(t =>
          `<h3 class="sc-subtitle">${t.name}</h3>${this._renderPT(t.points_table)}`
        ).join('');
        tabBtns += `<button class="tab-btn${f ? ' active' : ''}" data-tab="pt">Points Table</button>`;
        panels  += `<div class="tab-panel" data-tab="pt"${f ? '' : ' hidden'}>${ptHTML}</div>`;
      }

      const backBtn = this._navStack.length > 1 ? `<button class="back-btn" data-cs-back>&larr; Back</button>` : '';
      return `
        <div class="view-header">
          ${backBtn}
          <h2>${name}</h2>
        </div>
        <div class="view-tabs">
          <div class="tabs">${tabBtns}</div>
          ${panels}
        </div>`;
    }

    _venueHTML(name) {
      const nl = name.toLowerCase();
      const allPast = [], allUpcoming = [];

      for (const t of this._data.tournaments) {
        const past = t.past_matches
          .filter(m => (m.ground || '').toLowerCase() === nl)
          .map(m => ({ ...m, _tourn: t.name, _slug: t.slug, _color: t.color }));
        const upcoming = t.upcoming_matches
          .filter(m => (m.ground || '').toLowerCase() === nl)
          .map(m => ({ ...m, _tourn: t.name, _slug: t.slug, _color: t.color }));
        allPast.push(...past);
        allUpcoming.push(...upcoming);
      }

      allPast.sort((a, b) => a.date.localeCompare(b.date));
      allUpcoming.sort((a, b) => a.date.localeCompare(b.date));

      const backBtn = this._navStack.length > 1 ? `<button class="back-btn" data-cs-back>&larr; Back</button>` : '';
      const sc = this._renderSC(allPast, allUpcoming, true);

      return `
    <div class="view-header">
      ${backBtn}
      <h2>${name}</h2>
    </div>
    <div class="view-tabs">
      <div class="tabs"><button class="tab-btn active" data-tab="sc">Matches</button></div>
      <div class="tab-panel" data-tab="sc">${sc}</div>
    </div>`;
    }

    // === Renderers ===

    _renderPT(groups) {
      if (!groups || !Object.keys(groups).length) return '<p class="empty-msg">No points table data.</p>';
      const cols = ['Team', 'M', 'W', 'L', 'D', 'T', 'NR', 'NRR', 'Pt.'];
      return Object.entries(groups).map(([group, rows]) => `
        <div class="pt-section">
          <h3 class="pt-group-header">${group}</h3>
          <table class="cs-table">
            <thead><tr>${cols.map(h => `<th>${h}</th>`).join('')}</tr></thead>
            <tbody>${rows.map(r => `<tr>${cols.map(h => {
              if (h === 'Team') {
                const n = r[h] || '';
                return `<td><button class="cs-team-btn" data-cs-team="${n}">${n}</button></td>`;
              }
              const v = r[h] || '';
              if (h === 'NRR') {
                const cls = parseFloat(v) > 0 ? ' class="pos"' : parseFloat(v) < 0 ? ' class="neg"' : '';
                return `<td${cls}>${v}</td>`;
              }
              return `<td class="center">${v}</td>`;
            }).join('')}</tr>`).join('')}</tbody>
          </table>
        </div>`).join('');
    }

    _renderSC(past, upcoming, showTourn) {
      const teams = new Set();
      [...past, ...upcoming].forEach(m => {
        [m.team_1st, m.team_2nd, m.home_team, m.away_team].filter(Boolean).forEach(t => teams.add(t));
      });
      const teamOpts = ['<option value="">All teams</option>',
        ...[...teams].sort().map(t => `<option value="${t}">${t}</option>`)
      ].join('');

      return `
        <div class="sc-controls">
          <div class="view-toggle">
            <button class="view-btn active" data-view="list">List</button>
            <button class="view-btn" data-view="cards">Cards</button>
          </div>
          <div class="team-filter">
            <label>Team</label>
            <select class="cs-team-sel">${teamOpts}</select>
          </div>
        </div>
        <div class="match-section">
          <h3>Past Matches</h3>
          <div class="list-view">${this._pastTable(past, showTourn)}</div>
          <div class="cards-view" hidden>${this._pastCards(past, showTourn)}</div>
        </div>
        <div class="match-section">
          <h3>Upcoming Matches</h3>
          <div class="list-view">${this._upcomingTable(upcoming, showTourn)}</div>
          <div class="cards-view" hidden>${this._upcomingCards(upcoming, showTourn)}</div>
        </div>`;
    }

    _winner(m) {
      const idx = (m.result || '').toLowerCase().indexOf(' won by');
      return idx > 0 ? m.result.slice(0, idx).trim() : '';
    }

    _pill(m) {
      const color = m._color || '#888';
      const t = this._data.tournaments.find(t => t.slug === m._slug);
      const label = (t && t.abbreviation) || m._tourn || m._slug;
      return `<button class="tourn-pill" data-cs-tourn="${m._slug}" style="background:${color}">${label}</button>`;
    }

    _teamBtn(name) {
      if (!name) return '';
      return `<button class="cs-team-btn" data-cs-team="${name}">${name}</button>`;
    }

    _venueBtn(name) {
      if (!name) return '';
      return `<button class="cs-venue-btn" data-cs-venue="${name}">${name}</button>`;
    }

    _fmtDate(str) {
      const d = new Date(str + 'T00:00:00');
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    _pastTable(matches, showTourn) {
      if (!matches.length) return '<p class="empty-msg">No past matches.</p>';
      const hdr = ['Date', 'Ground', 'Batting 1st', 'Score', 'Batting 2nd', 'Score', 'Result'];
      if (showTourn) hdr.push('Tournament');
      const rows = matches.map(m => {
        const borderL = showTourn ? ` style="border-left:5px solid ${m._color || '#888'};padding-left:10px"` : '';
        const tournCell = showTourn ? `<td>${this._pill(m)}</td>` : '';
        return `<tr data-teams="${m.team_1st}|${m.team_2nd}">
          <td class="dt"${borderL}>${this._fmtDate(m.date)}</td>
          <td>${this._venueBtn(m.ground)}</td>
          <td class="sc-team">${this._teamBtn(m.team_1st)}</td>
          <td class="score">${m.score_1st}</td>
          <td class="sc-team">${this._teamBtn(m.team_2nd)}</td>
          <td class="score">${m.score_2nd}</td>
          <td class="result">${m.result}</td>
          ${tournCell}
        </tr>`;
      }).join('');
      return `<table class="cs-table"><thead><tr>${hdr.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
    }

    _upcomingTable(matches, showTourn) {
      if (!matches.length) return '<p class="empty-msg">No upcoming matches scheduled yet.</p>';
      const hdr = ['Date', 'Ground', 'Team 1', 'Team 2'];
      if (showTourn) hdr.push('Tournament');
      const rows = matches.map(m => {
        const home = m.home_team || '';
        const away = m.away_team || '';
        const time = m.time && m.time !== 'TBD' ? ` <span class="muted">${m.time}</span>` : '';
        const borderL = showTourn ? ` style="border-left:5px solid ${m._color || '#888'};padding-left:10px"` : '';
        const tournCell = showTourn ? `<td>${this._pill(m)}</td>` : '';
        return `<tr data-teams="${home}|${away}">
          <td class="dt"${borderL}>${this._fmtDate(m.date)}${time}</td>
          <td>${this._venueBtn(m.ground)}</td>
          <td class="sc-team">${this._teamBtn(home)}</td>
          <td class="sc-team">${this._teamBtn(away)}</td>
          ${tournCell}
        </tr>`;
      }).join('');
      return `<table class="cs-table"><thead><tr>${hdr.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
    }

    _pastCards(matches, showTourn) {
      if (!matches.length) return '<p class="empty-msg">No past matches.</p>';
      return `<div class="cards-grid">${matches.map(m => {
        const bs = showTourn ? ` style="border-top:5px solid ${m._color || '#888'}"` : '';
        const pill = showTourn ? `<div>${this._pill(m)}</div>` : '';
        const winner = this._winner(m).toLowerCase();
        const s1cls = winner && winner === m.team_1st.toLowerCase() ? ' winner' : '';
        const s2cls = winner && winner === m.team_2nd.toLowerCase() ? ' winner' : '';
        return `<div class="match-card" data-teams="${m.team_1st}|${m.team_2nd}"${bs}>
          <div class="card-meta"><span>${this._venueBtn(m.ground)} &middot; ${this._fmtDate(m.date)}</span><span class="badge">Past</span></div>
          ${pill}
          <div class="card-scores">
            <div class="card-team-row"><span class="card-team bold">${this._teamBtn(m.team_1st)}</span><span class="card-score${s1cls}">${m.score_1st}</span></div>
            <div class="card-team-row"><span class="card-team">${this._teamBtn(m.team_2nd)}</span><span class="card-score${s2cls}">${m.score_2nd}</span></div>
          </div>
          <div class="card-result">${m.result}</div>
        </div>`;
      }).join('')}</div>`;
    }

    _upcomingCards(matches, showTourn) {
      if (!matches.length) return '<p class="empty-msg">No upcoming matches scheduled yet.</p>';
      return `<div class="cards-grid">${matches.map(m => {
        const home = m.home_team || '';
        const away = m.away_team || '';
        const time = m.time && m.time !== 'TBD' ? ` &middot; ${m.time}` : '';
        const bs = showTourn ? ` style="border-top:5px solid ${m._color || '#888'}"` : '';
        const pill = showTourn ? `<div>${this._pill(m)}</div>` : '';
        return `<div class="match-card" data-teams="${home}|${away}"${bs}>
          <div class="card-meta"><span>${this._venueBtn(m.ground)} &middot; ${this._fmtDate(m.date)}${time}</span><span class="badge upcoming">Upcoming</span></div>
          ${pill}
          <div class="card-scores">
            <div class="card-team-row">${this._teamBtn(home)}</div>
            <div class="card-team-row">${this._teamBtn(away)}</div>
          </div>
        </div>`;
      }).join('')}</div>`;
    }
  }

  customElements.define('cricket-stats', CricketStats);
})();
