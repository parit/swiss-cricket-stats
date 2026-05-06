(function () {
  var currentView = 'list';
  var currentRoot = document;

  // --- Tabs ---
  var tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      tabBtns.forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
      var id = 'tab-' + this.dataset.tab;
      document.querySelectorAll('.tab-content').forEach(function (tc) {
        if (tc.id === id) tc.classList.add('active');
        else tc.classList.remove('active');
      });
    });
  });

  // --- View toggle ---
  function applyView(root) {
    root.querySelectorAll('.list-view').forEach(function (el) {
      el.style.display = currentView === 'list' ? '' : 'none';
    });
    root.querySelectorAll('.cards-view').forEach(function (el) {
      el.style.display = currentView === 'cards' ? '' : 'none';
    });
  }

  var viewBtns = document.querySelectorAll('.view-btn');
  viewBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      viewBtns.forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
      currentView = this.dataset.view;
      applyView(document);
    });
  });

  // --- Team filter ---
  function getTeams(root) {
    var teams = new Set();
    root.querySelectorAll('[data-teams]').forEach(function (el) {
      el.dataset.teams.split('|').forEach(function (t) {
        if (t.trim()) teams.add(t.trim());
      });
    });
    return Array.from(teams).sort();
  }

  function populateTeamFilter(sel, root) {
    if (!sel) return;
    sel.innerHTML = '<option value="">All teams</option>';
    getTeams(root).forEach(function (t) {
      var opt = document.createElement('option');
      opt.value = t; opt.textContent = t;
      sel.appendChild(opt);
    });
    sel.value = '';
  }

  function applyTeamFilter(sel, root) {
    var selected = sel ? sel.value : '';
    root.querySelectorAll('[data-teams]').forEach(function (el) {
      if (!selected) { el.style.display = ''; return; }
      var teams = el.dataset.teams.split('|').map(function (t) { return t.trim(); });
      el.style.display = teams.indexOf(selected) !== -1 ? '' : 'none';
    });
  }

  // --- Page-type detection ---

  var statsSel = document.getElementById('stats-tournament-select');

  if (statsSel) {
    // ── Combined stats.html: shared dropdown syncs both tabs ──
    var ptSections = document.querySelectorAll('.pt-section');
    var scSections = document.querySelectorAll('.sc-section');

    // Wire each section's filter to its own root
    scSections.forEach(function (s) {
      var sel = s.querySelector('.sc-team-filter');
      if (sel) sel.addEventListener('change', function () { applyTeamFilter(sel, s); });
    });

    function showStatsTournament(slug) {
      ptSections.forEach(function (s) {
        s.style.display = s.id === 'pt-' + slug ? '' : 'none';
      });
      scSections.forEach(function (s) {
        var visible = s.id === 'sc-' + slug;
        s.style.display = visible ? '' : 'none';
        if (visible) {
          currentRoot = s;
          applyView(s);
          s.querySelectorAll('.view-btn').forEach(function (b) {
            if (b.dataset.view === currentView) b.classList.add('active');
            else b.classList.remove('active');
          });
          var sel = s.querySelector('.sc-team-filter');
          populateTeamFilter(sel, s);
          applyTeamFilter(sel, s);
        }
      });
    }

    if (statsSel.options.length) showStatsTournament(statsSel.options[0].value);
    statsSel.addEventListener('change', function () { showStatsTournament(this.value); });

  } else {
    // ── Per-tournament stats.html: no dropdown, tabs only ──
    var scTab = document.getElementById('tab-scorecards');
    if (scTab) {
      currentRoot = scTab;
      var sel = scTab.querySelector('.sc-team-filter');
      populateTeamFilter(sel, scTab);
      if (sel) sel.addEventListener('change', function () { applyTeamFilter(sel, scTab); });
    }
  }
})();
