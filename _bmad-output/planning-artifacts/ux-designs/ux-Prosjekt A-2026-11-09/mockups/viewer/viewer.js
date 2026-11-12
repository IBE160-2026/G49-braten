// Shared concept viewer. Wraps every <section class="screen" data-id data-name> in a device frame,
// adds a neutral toolbar (page picker, all-pages grid, device, theme) and keeps state in the URL hash:
//   #P03              one page, keeps current device and theme
//   #P03/mobil/dark   page, device (desktop|nettbrett|mobil), theme (light|dark)
//   #alle/desktop     grid of every page
//   .../clean         no chrome, for screenshots
// Screens link to each other with plain <a href="#P05">.
(function () {
  const DEVICES = [['desktop', 'Desktop'], ['nettbrett', 'Nettbrett'], ['mobil', 'Mobil']];
  const THEMES = [['light', 'Lys'], ['dark', 'Mørk']];
  const screens = Array.from(document.querySelectorAll('section.screen[data-id]'));
  if (!screens.length) return;

  const state = { page: screens[0].dataset.id, device: 'desktop', theme: 'light', clean: false };
  const body = document.body;
  const label = (s) => `${s.dataset.id} ${s.dataset.name || ''}`.trim();

  // Stage and frames
  const stage = document.createElement('main');
  stage.className = 'cv-stage';
  const single = document.createElement('div');
  single.className = 'cv-single';
  const grid = document.createElement('div');
  grid.className = 'cv-grid';
  stage.append(single, grid);

  const frames = new Map();
  screens.forEach((s) => {
    const frame = document.createElement('div');
    frame.className = 'cv-frame';
    frame.appendChild(s); // detaches the section; render() mounts only what is on view
    frames.set(s.dataset.id, frame);
  });

  // Toolbar
  const bar = document.createElement('header');
  bar.className = 'cv-bar';
  const num = body.dataset.conceptNumber || '';
  const name = body.dataset.conceptName || document.title;
  bar.innerHTML = `<div class="cv-title">${num ? `<small>Konsept ${num}</small>` : ''}${name}</div>`;

  const prev = button('‹', 'Forrige side');
  const next = button('›', 'Neste side');
  const select = document.createElement('select');
  select.className = 'cv-select';
  select.setAttribute('aria-label', 'Velg side');
  const pages = screens.filter((s) => !/^D/i.test(s.dataset.id));
  const dialogs = screens.filter((s) => /^D/i.test(s.dataset.id));
  [['Sider', pages], ['Dialoger', dialogs]].forEach(([title, list]) => {
    if (!list.length) return;
    const og = document.createElement('optgroup');
    og.label = title;
    list.forEach((s) => og.append(new Option(label(s), s.dataset.id)));
    select.append(og);
  });
  const nav = group([prev, next]);
  const allBtn = button('Alle sider', 'Vis alle sider');
  const devGroup = group(DEVICES.map(([v, t]) => button(t, t, () => go({ device: v }), v)));
  const themeGroup = group(THEMES.map(([v, t]) => button(t, `${t} tema`, () => go({ theme: v }), v)));
  const spacer = document.createElement('div');
  spacer.className = 'cv-spacer';
  bar.append(nav, select, group([allBtn]), spacer, devGroup, themeGroup);

  prev.onclick = () => step(-1);
  next.onclick = () => step(1);
  select.onchange = () => go({ page: select.value });
  allBtn.onclick = () => go({ page: state.page === 'alle' ? (state.last || screens[0].dataset.id) : 'alle' });

  body.prepend(bar);
  body.append(stage);
  body.classList.add('cv-ready');

  function button(text, title, onClick, value) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'cv-btn';
    b.textContent = text;
    b.title = title;
    if (value) b.dataset.value = value;
    if (onClick) b.onclick = onClick;
    return b;
  }
  function group(items) {
    const g = document.createElement('div');
    g.className = 'cv-group';
    g.append(...items);
    return g;
  }
  function step(delta) {
    const ids = screens.map((s) => s.dataset.id);
    const i = Math.max(0, ids.indexOf(state.page === 'alle' ? state.last : state.page));
    go({ page: ids[(i + delta + ids.length) % ids.length] });
  }

  function render() {
    const { page, device, theme, clean } = state;
    document.documentElement.dataset.theme = theme;
    body.classList.toggle('cv-clean', clean);
    frames.forEach((f) => (f.dataset.device = device));
    grid.dataset.device = device;
    const isGrid = page === 'alle';
    if (isGrid) {
      single.replaceChildren();
      grid.replaceChildren(...screens.map((s) => {
        const cell = document.createElement('figure');
        cell.className = 'cv-cell';
        const cap = document.createElement('figcaption');
        cap.innerHTML = `<span>${s.dataset.id}</span>${s.dataset.name || ''}`;
        cell.append(frames.get(s.dataset.id), cap);
        cell.onclick = () => go({ page: s.dataset.id });
        return cell;
      }));
      grid.classList.remove('cv-hidden');
    } else {
      grid.replaceChildren();
      grid.classList.add('cv-hidden');
      const frame = frames.get(page) || frames.get(screens[0].dataset.id);
      single.replaceChildren(frame);
      state.last = page;
      select.value = page;
      if (!clean) window.scrollTo(0, 0);
    }
    allBtn.setAttribute('aria-pressed', String(isGrid));
    devGroup.querySelectorAll('.cv-btn').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.value === device)));
    themeGroup.querySelectorAll('.cv-btn').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.value === theme)));
    const s = screens.find((x) => x.dataset.id === page);
    document.title = `${s ? label(s) : 'Alle sider'} · ${name}`;
  }

  function parse(hash) {
    const parts = decodeURIComponent(hash.replace(/^#/, '')).split('/').filter(Boolean);
    const out = {};
    parts.forEach((p) => {
      if (p === 'alle' || frames.has(p)) out.page = p;
      else if (DEVICES.some(([v]) => v === p)) out.device = p;
      else if (THEMES.some(([v]) => v === p)) out.theme = p;
      else if (p === 'clean') out.clean = true;
    });
    return out;
  }
  function go(change) {
    Object.assign(state, change);
    const hash = `#${state.page}/${state.device}/${state.theme}${state.clean ? '/clean' : ''}`;
    if (location.hash !== hash) history.replaceState(null, '', hash);
    render();
  }

  // In-screen links (<a href="#P05">) navigate without losing device and theme.
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || a.closest('.cv-bar')) return;
    const target = parse(a.getAttribute('href'));
    if (target.page) { e.preventDefault(); go({ page: target.page }); }
  });
  window.addEventListener('hashchange', () => { Object.assign(state, parse(location.hash)); render(); });
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea, select, [contenteditable]')) return;
    if (e.key === 'ArrowRight' && e.altKey) step(1);
    if (e.key === 'ArrowLeft' && e.altKey) step(-1);
  });

  // Scripted access for screenshots: viewer.go('P03', 'mobil', 'dark', true)
  window.viewer = {
    go: (page, device, theme, clean) => go({ page, device: device || state.device, theme: theme || state.theme, clean: !!clean }),
    pages: () => screens.map((s) => ({ id: s.dataset.id, name: s.dataset.name })),
  };

  Object.assign(state, parse(location.hash));
  render();
})();
