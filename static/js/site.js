(function(){
  'use strict';

  /* ---- il ----
     Guarded: this file is one IIFE, so an exception this early would take the
     menu, the dock and the contact form down with it. */
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---- reveal on scroll ---- */
  var reveals = document.querySelectorAll('.rv');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, {threshold:0.12, rootMargin:'0px 0px -8% 0px'});
    reveals.forEach(function(el){ io.observe(el); });
  } else {
    reveals.forEach(function(el){ el.classList.add('in'); });
  }

  /* Tells the inline head script that the reveal machinery is armed. Without
     this flag it drops the "js" class on load and shows everything outright. */
  window.__siteReady = true;

  /* ---- stat counters ---- */
  var counters = document.querySelectorAll('.count');
  var runCount = function(el){
    var target = parseInt(el.dataset.to, 10) || 0;
    var start = null, dur = 1500;
    var step = function(ts){
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  if ('IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (e.isIntersecting) { runCount(e.target); cio.unobserve(e.target); }
      });
    }, {threshold:0.5});
    counters.forEach(function(el){ cio.observe(el); });
  } else {
    counters.forEach(function(el){ el.textContent = el.dataset.to; });
  }

  /* ---- dock active section ----
     Dock links are absolute now (/az/#ana) so they work from detail pages;
     match on the hash rather than the whole href. */
  var links = Array.prototype.slice.call(document.querySelectorAll('.dock a'))
    .filter(function(a){ return a.hash && document.querySelector(a.hash); });
  var sections = links.map(function(a){ return document.querySelector(a.hash); });
  /* Reading offsetTop forces the browser to flush layout. Doing that for every
     section on every scroll event is what locked up phones, so offsets are
     measured once (and again on resize) and the scroll path only reads cached
     numbers. Class writes are skipped unless the active link actually changed. */
  var offsets = [];
  var measure = function(){
    offsets = sections.map(function(s){ return s.offsetTop; });
  };

  var topbar = document.getElementById('topbar');
  var stuck = false;
  var activeHash = null;

  var apply = function(){
    var y = window.scrollY;

    if (topbar) {
      var shouldStick = y > 20;
      if (shouldStick !== stuck) {
        stuck = shouldStick;
        topbar.classList.toggle('is-stuck', stuck);
      }
    }

    if (!offsets.length) return;
    var pos = y + window.innerHeight * 0.35;
    var current = 0;
    for (var i = 0; i < offsets.length; i++) {
      if (offsets[i] <= pos) current = i;
    }
    var hash = links[current] ? links[current].hash : null;
    if (hash === activeHash) return;
    activeHash = hash;
    links.forEach(function(a){ a.classList.toggle('is-active', a.hash === hash); });
  };

  var queued = false;
  var onScroll = function(){
    if (queued) return;
    queued = true;
    requestAnimationFrame(function(){ queued = false; apply(); });
  };

  var onResize = function(){ measure(); apply(); };

  window.addEventListener('scroll', onScroll, {passive:true});
  window.addEventListener('resize', onResize, {passive:true});
  // Late-loading images change section offsets, so re-measure once settled.
  window.addEventListener('load', onResize);
  measure();
  apply();

  /* ---- parallax on floating shapes ---- */
  var shapes = document.querySelectorAll('.shape');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduce && window.innerWidth > 860) {
    var ticking = false;
    window.addEventListener('scroll', function(){
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function(){
        var y = window.scrollY;
        shapes.forEach(function(s, i){
          var k = (i % 3 + 1) * 0.045;
          s.style.translate = '0 ' + (-y * k).toFixed(1) + 'px';
        });
        ticking = false;
      });
    }, {passive:true});
  }

  /* ---- address links ----
     Desktop and iOS follow the Google Maps universal link (iOS opens the Maps
     app when installed). Android understands geo:, which makes the system show
     a chooser listing every installed navigation app (Maps, Waze, Yandex...). */
  if (/Android/i.test(navigator.userAgent)) {
    document.querySelectorAll('.js-map-link[data-map-query]').forEach(function(link){
      var query = link.getAttribute('data-map-query');
      if (query) {
        link.setAttribute('href', 'geo:0,0?q=' + encodeURIComponent(query));
        link.removeAttribute('target');
      }
    });
  }

  /* ---- contact form ----
     API: POST /api/v1/contact/messages/  (contact.api.views.ContactMessageCreateView)
       request  : {name, email, phone, message}
       201      -> lead stored, visible in the admin
       400      -> {"<field>": ["<message>", ...]} from the shared validators
       429      -> throttled (5 submissions/hour per IP)
     Copy comes from data-msg-* on the form so this file stays static and
     translatable text still follows the active language. */
  var form = document.getElementById('contactForm');
  var ok = document.getElementById('formOk');

  if (form && ok) {
    var msg = function(key, fallback){ return form.getAttribute('data-msg-' + key) || fallback; };
    var value = function(name){
      var field = form.elements[name];
      return field ? field.value.trim() : '';
    };
    var show = function(text, isError){
      ok.textContent = text;
      ok.classList.toggle('err', !!isError);
      ok.classList.add('show');
    };

    var endpoint = form.getAttribute('data-endpoint') || '/api/v1/contact/messages/';
    var submitButton = form.querySelector('button[type="submit"]');
    var submitLabel = submitButton ? submitButton.innerHTML : '';

    form.addEventListener('submit', function(e){
      e.preventDefault();

      var payload = {
        name: value('name'),
        email: value('email'),
        phone: value('phone'),
        message: value('message')
      };

      /* Client-side checks mirror contact/validators.py so the user gets
         instant feedback; the server re-validates regardless. */
      if (!payload.name || !payload.email || !payload.phone || !payload.message) {
        show(msg('required', 'Zəhmət olmasa bütün sahələri doldurun.'), true);
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(payload.email)) {
        show(msg('email', 'Email ünvanı düzgün görünmür.'), true);
        return;
      }
      var digits = payload.phone.replace(/\D/g, '');
      if (digits.length < 9 || digits.length > 15 || /[^\d\s+()\-.]/.test(payload.phone)) {
        show(msg('phone', 'Telefon nömrəsi düzgün görünmür. Nümunə: +994 50 000 00 00'), true);
        return;
      }

      // Loading state: reuse the existing button, no new markup or styling.
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = msg('sending', 'Göndərilir...');
      }

      var csrf = form.querySelector('[name=csrfmiddlewaretoken]');

      fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf ? csrf.value : ''
        },
        body: JSON.stringify(payload)
      }).then(function(response){
        return response.json().catch(function(){ return {}; }).then(function(data){
          return {status: response.status, data: data};
        });
      }).then(function(result){
        if (result.status === 201) {
          show(msg('success', 'Təşəkkürlər! Sorğunuz qeydə alındı.').replace('{name}', payload.name));
          form.reset();
          return;
        }
        if (result.status === 429) {
          show(msg('throttled', 'Çox sayda sorğu göndərildi. Bir qədər sonra yenidən cəhd edin.'), true);
          return;
        }
        // DRF returns {field: [messages]} — surface the first one.
        var first = '';
        Object.keys(result.data || {}).some(function(key){
          var entry = result.data[key];
          first = Array.isArray(entry) ? entry[0] : entry;
          return !!first;
        });
        show(first || msg('error', 'Göndərmək mümkün olmadı. Zəhmət olmasa yenidən cəhd edin.'), true);
      }).catch(function(error){
        console.error('[contact] network error', error);
        show(msg('offline', 'Şəbəkə xətası. İnternet bağlantınızı yoxlayın.'), true);
      }).finally(function(){
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.innerHTML = submitLabel;
        }
      });
    });
  }

  /* ---- mobile menu ----
     Below 1080px .topnav is hidden by CSS, so without this the header carries
     no navigation at all — not even the language switcher, which lives in it. */
  var navToggle = document.getElementById('navToggle');
  var mobnav = document.getElementById('mobnav');

  if (navToggle && mobnav) {
    var hideTimer = null;
    var isOpen = function(){ return navToggle.getAttribute('aria-expanded') === 'true'; };

    var setOpen = function(open){
      if (open === isOpen()) return;
      clearTimeout(hideTimer);
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.classList.toggle('nav-open', open);

      if (open) {
        mobnav.hidden = false;
        // One deliberate reflow so the panel animates in from its closed state.
        void mobnav.offsetWidth;
        mobnav.classList.add('is-open');
      } else {
        mobnav.classList.remove('is-open');
        // Keep it out of the accessibility tree once the transition is done.
        // The timeout also covers reduced-motion, where transitionend never fires.
        hideTimer = setTimeout(function(){ mobnav.hidden = true; }, 360);
      }
    };

    navToggle.addEventListener('click', function(){ setOpen(!isOpen()); });

    // Same-page anchors do not reload, so the panel has to close itself.
    mobnav.addEventListener('click', function(e){
      if (e.target.closest('a')) setOpen(false);
    });

    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape' && isOpen()) {
        setOpen(false);
        navToggle.focus();
      }
    });

    // Rotating to a width where .topnav is visible again must not leave the
    // panel open or the body scroll-locked.
    var desktop = window.matchMedia('(min-width:1081px)');
    var onChange = function(e){ if (e.matches) setOpen(false); };
    if (desktop.addEventListener) desktop.addEventListener('change', onChange);
    else if (desktop.addListener) desktop.addListener(onChange);
  }

})();
