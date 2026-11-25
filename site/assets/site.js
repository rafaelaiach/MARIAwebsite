/* Maria Aiach, architecte — interactions. No library. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  };
  const transition = (fn) => (document.startViewTransition && !reduce ? document.startViewTransition(fn) : fn());

  /* ---------------------------------------------------------- header */
  const top = $('[data-top]');
  const hero = $('.hero, .p-hero');
  let lastY = scrollY;
  const onScroll = () => {
    const y = scrollY;
    const limit = hero ? hero.offsetHeight - 90 : 30;
    top.classList.toggle('is-solid', y > limit);
    const goingDown = y > lastY + 4, goingUp = y < lastY - 4;
    if (goingDown && y > 500 && !document.body.classList.contains('menu-open')) top.classList.add('is-hidden');
    if (goingUp || y < 200) top.classList.remove('is-hidden');
    lastY = y;
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ------------------------------------------------------------ menu */
  const menuBtn = $('[data-menu-btn]'), menu = $('[data-menu]');
  const setMenu = (open) => {
    menuBtn.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('menu-open', open);
    if (open) { menu.hidden = false; requestAnimationFrame(() => menu.classList.add('is-open')); }
    else { menu.classList.remove('is-open'); setTimeout(() => { if (!menu.classList.contains('is-open')) menu.hidden = true; }, 350); }
  };
  menuBtn?.addEventListener('click', () => setMenu(menuBtn.getAttribute('aria-expanded') !== 'true'));
  $$('a', menu).forEach((a) => a.addEventListener('click', () => setMenu(false)));
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.body.classList.contains('menu-open')) setMenu(false); });

  /* ----------------------------------------------------- hero slides */
  const slides = $$('[data-slide]');
  if (slides.length > 1) {
    const dots = $$('[data-dots] button');
    const label = $('[data-slide-label]');
    const MS = 6000;
    document.documentElement.style.setProperty('--slide-ms', MS + 'ms');
    let cur = 0, timer;
    const show = (n) => {
      slides[cur].classList.remove('is-on'); slides[cur].tabIndex = -1;
      dots.forEach((d, i) => { d.classList.remove('is-on'); d.classList.toggle('is-done', i < n); });
      cur = (n + slides.length) % slides.length;
      slides[cur].classList.add('is-on'); slides[cur].tabIndex = 0;
      void dots[cur]?.offsetWidth; dots[cur]?.classList.add('is-on');
      if (label) { label.style.opacity = 0; setTimeout(() => { label.textContent = slides[cur].dataset.label; label.href = slides[cur].getAttribute('href'); label.style.opacity = 1; }, 300); }
      clearTimeout(timer); if (!reduce) timer = setTimeout(() => show(cur + 1), MS);
    };
    dots.forEach((d, i) => d.addEventListener('click', () => show(i)));
    document.addEventListener('visibilitychange', () => { if (document.hidden) clearTimeout(timer); else show(cur); });
    if (!reduce) timer = setTimeout(() => show(1), MS);
  }

  /* ------------------------------------------- parallax on project top */
  const pMedia = $('.p-hero-media img');
  if (pMedia && !reduce) {
    addEventListener('scroll', () => { const y = scrollY; if (y < innerHeight) pMedia.style.transform = `translate3d(0, ${y * 0.22}px, 0) scale(1.04)`; }, { passive: true });
  }

  /* --------------------------------------------------------- reveals */
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  $$('.reveal').forEach((el) => io.observe(el));

  /* ---------------------------------------------- filters and views */
  const grid = $('[data-grid]'), list = $('[data-list]');
  if (grid && list) {
    const chips = $$('[data-filter]');
    chips.forEach((chip) => chip.addEventListener('click', () => {
      const k = chip.dataset.filter;
      transition(() => {
        chips.forEach((c) => { const on = c === chip; c.classList.toggle('is-on', on); c.setAttribute('aria-pressed', on); });
        grid.classList.toggle('is-filtered', k !== 'all');
        $$('[data-kind]', grid).concat($$('[data-kind]', list)).forEach((el) => {
          el.classList.toggle('is-out', k !== 'all' && el.dataset.kind !== k);
          el.classList.add('is-in');
        });
      });
    }));
    const views = $$('[data-view]');
    const setView = (v, animate) => {
      const run = () => {
        views.forEach((b) => { const on = b.dataset.view === v; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on); });
        grid.hidden = v !== 'grid'; list.hidden = v !== 'list';
        $$('.reveal', v === 'grid' ? grid : list).forEach((el) => el.classList.add('is-in'));
      };
      animate ? transition(run) : run();
      store.set('ma-view', v);
    };
    views.forEach((b) => b.addEventListener('click', () => setView(b.dataset.view, true)));
    if (store.get('ma-view') === 'list') setView('list', false);

    /* a photo follows the pointer over the list */
    const cur = $('[data-cursor]'), curImg = cur && $('img', cur);
    if (cur && matchMedia('(pointer: fine)').matches) {
      let x = 0, y = 0, tx = 0, ty = 0, raf;
      const loop = () => { tx += (x - tx) * 0.16; ty += (y - ty) * 0.16; cur.style.transform = `translate(${tx}px, ${ty}px) translate(-50%, -50%) scale(${cur.classList.contains('is-on') ? 1 : .9})`; raf = requestAnimationFrame(loop); };
      $$('a[data-preview]', list).forEach((a) => {
        a.addEventListener('mouseenter', () => { curImg.src = a.dataset.preview; cur.classList.add('is-on'); if (!raf) loop(); });
        a.addEventListener('mouseleave', () => cur.classList.remove('is-on'));
      });
      list.addEventListener('mousemove', (e) => { x = e.clientX + 170; y = e.clientY; });
    }
  }

  /* ------------------------------------------- drag to scroll (art) */
  $$('[data-strip]').forEach((strip) => {
    let down = false, sx = 0, sl = 0, moved = false;
    strip.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse') return; down = true; moved = false; sx = e.clientX; sl = strip.scrollLeft; strip.style.scrollSnapType = 'none'; });
    addEventListener('pointermove', (e) => { if (!down) return; const dx = e.clientX - sx; if (Math.abs(dx) > 4) moved = true; strip.scrollLeft = sl - dx; });
    addEventListener('pointerup', () => { if (!down) return; down = false; strip.style.scrollSnapType = ''; });
    strip.addEventListener('click', (e) => { if (moved) e.preventDefault(); }, true);
    strip.addEventListener('dragstart', (e) => e.preventDefault());
  });

  /* -------------------------------------------------------- lightbox */
  const lb = $('[data-lightbox]');
  if (lb) {
    const lbImg = $('[data-lb-img]', lb), lbCap = $('[data-lb-cap]', lb), lbCount = $('[data-lb-count]', lb);
    let items = [], idx = 0, opener = null;
    const big = (img) => (img.currentSrc || img.src).replace(/-1000\.webp$/, '-2000.webp');
    const render = (swap) => {
      const btn = items[idx], img = $('img', btn);
      const cap = btn.closest('figure')?.querySelector('figcaption')?.textContent || '';
      const apply = () => { lbImg.src = big(img); lbImg.alt = img.alt; lbCap.textContent = cap; lbCount.textContent = `${idx + 1} / ${items.length}`; lbImg.classList.remove('is-swapping'); };
      if (swap) { lbImg.classList.add('is-swapping'); setTimeout(apply, 180); } else apply();
      [items[idx + 1], items[idx - 1]].forEach((b) => { if (b) { const p = new Image(); p.src = big($('img', b)); } });
    };
    const open = (btn) => {
      items = $$('[data-lb-item]', btn.closest('[data-lb-group]') || document);
      idx = items.indexOf(btn); opener = btn;
      render(false);
      lb.hidden = false; document.body.classList.add('lb-open');
      requestAnimationFrame(() => lb.classList.add('is-open'));
      $('[data-lb-close]', lb).focus();
    };
    const close = () => {
      lb.classList.remove('is-open'); document.body.classList.remove('lb-open');
      setTimeout(() => { lb.hidden = true; lbImg.removeAttribute('src'); }, 350);
      opener?.focus();
    };
    const go = (d) => { idx = (idx + d + items.length) % items.length; render(true); };
    document.addEventListener('click', (e) => { const b = e.target.closest('[data-lb-item]'); if (b) open(b); });
    $('[data-lb-close]', lb).addEventListener('click', close);
    $('[data-lb-prev]', lb).addEventListener('click', () => go(-1));
    $('[data-lb-next]', lb).addEventListener('click', () => go(1));
    lb.addEventListener('click', (e) => { if (e.target === lb) close(); });
    addEventListener('keydown', (e) => {
      if (lb.hidden) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight') go(1);
      if (e.key === 'ArrowLeft') go(-1);
    });
    let sx = null;
    lb.addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', (e) => { if (sx === null) return; const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1); sx = null; });
  }
})();

/* before/after slider */
document.querySelectorAll('[data-ba]').forEach((frame) => {
  const range = frame.querySelector('[data-ba-range]');
  const set = (v) => frame.style.setProperty('--pos', v + '%');
  range.addEventListener('input', () => set(range.value));
  set(range.value);
});

/* 9 projects on the homepage; "Voir tous les projets" (or any filter) shows the rest */
(() => {
  const grid = document.querySelector('[data-grid]');
  const btn = document.querySelector('[data-more]');
  const wrap = document.querySelector('[data-more-wrap]');
  if (!grid || !btn) return;
  const showAll = (animate) => {
    const run = () => {
      grid.classList.add('show-all');
      wrap.classList.add('is-done');
      grid.querySelectorAll('.is-extra').forEach((el) => el.classList.add('is-in'));
    };
    (animate && document.startViewTransition) ? document.startViewTransition(run) : run();
  };
  btn.addEventListener('click', () => showAll(true));
  document.querySelectorAll('[data-filter]').forEach((c) => c.addEventListener('click', () => showAll(false)));
})();

/* before/after tabs: swap the pair shown in the slider */
(() => {
  const frame = document.querySelector('[data-ba]');
  const tabs = [...document.querySelectorAll('[data-ba-tab]')];
  if (!frame || !tabs.length) return;
  const after = frame.querySelector('[data-ba-after]'), before = frame.querySelector('[data-ba-before]');
  const range = frame.querySelector('[data-ba-range]'), link = document.querySelector('[data-ba-link]');
  tabs.forEach((tab) => {
    const f = tab.dataset.file;
    [new Image().src = `/img/${f}-after-2000.webp`, new Image().src = `/img/${f}-before-2000.webp`];
    tab.addEventListener('click', () => {
      if (tab.classList.contains('is-on')) return;
      tabs.forEach((t) => { const on = t === tab; t.classList.toggle('is-on', on); t.setAttribute('aria-selected', on); });
      frame.classList.add('is-swapping');
      setTimeout(() => {
        after.src = `/img/${f}-after-2000.webp`; before.src = `/img/${f}-before-2000.webp`;
        const w = +tab.dataset.w, h = +tab.dataset.h;
        frame.style.aspectRatio = `${w}/${h}`; frame.style.setProperty('--ar', (w / h).toFixed(4));
        range.value = 50; frame.style.setProperty('--pos', '50%');
        if (link) link.href = tab.dataset.url;
        Promise.all([after, before].map((im) => im.decode ? im.decode().catch(() => {}) : null)).then(() => frame.classList.remove('is-swapping'));
      }, 280);
    });
  });
})();

/* phones: the call bar shows after the top photo and hides on the contact section */
(() => {
  const bar = document.querySelector('[data-callbar]');
  if (!bar) return;
  const top = document.querySelector('.hero, .p-hero');
  const contact = document.getElementById('contact');
  let onContact = false;
  const update = () => bar.classList.toggle('is-on', scrollY > (top ? top.offsetHeight * .7 : 300) && !onContact);
  if (contact) new IntersectionObserver(([e]) => { onContact = e.isIntersecting; update(); }, { threshold: .05 }).observe(contact);
  addEventListener('scroll', update, { passive: true });
  update();
})();
