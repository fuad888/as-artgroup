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

    /* ---- attachment chooser ---- */
    var ALLOWED_FILE = /\.(pdf|docx?|xlsx?)$/i;
    var fileInput = document.getElementById('fayl');
    var fileText  = form.querySelector('.file-drop__text');
    var fileClear = document.getElementById('fileClear');

    var clearFile = function(){
      if (!fileInput) return;
      fileInput.value = '';
      if (fileText) fileText.textContent = fileText.dataset.empty;
      if (fileClear) fileClear.hidden = true;
      form.classList.remove('has-file');
    };

    if (fileInput) {
      fileInput.addEventListener('change', function(){
        var chosen = fileInput.files.length ? fileInput.files[0] : null;
        if (!chosen) return clearFile();
        if (fileText) fileText.textContent = chosen.name;
        if (fileClear) fileClear.hidden = false;
        form.classList.add('has-file');
      });
    }
    if (fileClear) fileClear.addEventListener('click', clearFile);
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
      var file = fileInput && fileInput.files.length ? fileInput.files[0] : null;

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

      /* The server re-checks both of these; this only saves the visitor a
         round trip and an upload they would have had to redo. */
      if (file) {
        if (!ALLOWED_FILE.test(file.name)) {
          show(msg('filetype', 'Yalnız PDF, Word və Excel faylları qəbul olunur.'), true);
          return;
        }
        var maxMb = parseFloat(form.getAttribute('data-max-file-mb')) || 10;
        if (file.size > maxMb * 1024 * 1024) {
          show(msg('filesize', 'Fayl çox böyükdür. Maksimum ' + maxMb + ' MB.'), true);
          return;
        }
      }

      // Loading state: reuse the existing button, no new markup or styling.
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = msg('sending', 'Göndərilir...');
      }

      var csrf = form.querySelector('[name=csrfmiddlewaretoken]');

      /* multipart rather than JSON so the optional attachment rides along.
         Content-Type is left unset on purpose: the browser has to add the
         multipart boundary itself. */
      var body = new FormData();
      Object.keys(payload).forEach(function(key){ body.append(key, payload[key]); });
      if (file) body.append('attachment', file);

      fetch(endpoint, {
        method: 'POST',
        headers: {'X-CSRFToken': csrf ? csrf.value : ''},
        body: body
      }).then(function(response){
        return response.json().catch(function(){ return {}; }).then(function(data){
          return {status: response.status, data: data};
        });
      }).then(function(result){
        if (result.status === 201) {
          show(msg('success', 'Təşəkkürlər! Sorğunuz qeydə alındı.').replace('{name}', payload.name));
          form.reset();
          clearFile();
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

  /* ---- project gallery lightbox ----
     Items carry their own data-* payload, so this needs no server-rendered
     JSON blob and works for any number of gallery entries. */
  var galleryGrid = document.getElementById('gallery');
  var lightbox = document.getElementById('lightbox');

  if (galleryGrid && lightbox) {
    var items = Array.prototype.slice.call(galleryGrid.querySelectorAll('.gallery__item'));
    var media = document.getElementById('lbMedia');
    var caption = document.getElementById('lbCaption');
    var counter = document.getElementById('lbCounter');
    var prevBtn = document.getElementById('lbPrev');
    var nextBtn = document.getElementById('lbNext');
    var closeBtn = document.getElementById('lbClose');
    var current = 0;
    var lastFocused = null;

    var single = items.length < 2;
    prevBtn.hidden = nextBtn.hidden = single;

    var clearMedia = function(){
      // Removing the node stops a playing <video>/<iframe> dead.
      media.innerHTML = '';
    };

    var render = function(index){
      var el = items[index];
      if (!el) return;
      current = index;
      clearMedia();

      var node;
      if (el.dataset.embed) {
        node = document.createElement('iframe');
        node.src = el.dataset.embed;
        node.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture';
        node.allowFullscreen = true;
        node.title = el.dataset.caption || document.title;
      } else if (el.dataset.video) {
        node = document.createElement('video');
        node.src = el.dataset.video;
        node.controls = true;
        node.autoplay = true;
        node.playsInline = true;
        if (el.dataset.full) node.poster = el.dataset.full;
      } else {
        node = document.createElement('img');
        node.src = el.dataset.full;
        node.alt = el.dataset.caption || '';
      }
      media.appendChild(node);

      caption.textContent = el.dataset.caption || '';
      counter.textContent = single ? '' : (index + 1) + ' / ' + items.length;
    };

    var step = function(delta){
      render((current + delta + items.length) % items.length);
    };

    var open = function(index){
      lastFocused = document.activeElement;
      lightbox.hidden = false;
      void lightbox.offsetWidth;          // let the fade run from the closed state
      lightbox.classList.add('is-open');
      document.body.classList.add('lightbox-open');
      render(index);
      closeBtn.focus();
    };

    var close = function(){
      lightbox.classList.remove('is-open');
      document.body.classList.remove('lightbox-open');
      setTimeout(function(){
        lightbox.hidden = true;
        clearMedia();                     // only after the fade, or it flickers
      }, 300);
      if (lastFocused) lastFocused.focus();
    };

    items.forEach(function(el, index){
      el.addEventListener('click', function(){ open(index); });
    });
    prevBtn.addEventListener('click', function(){ step(-1); });
    nextBtn.addEventListener('click', function(){ step(1); });
    closeBtn.addEventListener('click', close);

    // Clicking the backdrop closes; clicking the media itself must not.
    lightbox.addEventListener('click', function(e){
      if (e.target === lightbox || e.target === media) close();
    });

    document.addEventListener('keydown', function(e){
      if (lightbox.hidden) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft' && !single) step(-1);
      else if (e.key === 'ArrowRight' && !single) step(1);
    });

    // Swipe, the way a carousel is expected to work on a phone.
    var touchX = null;
    lightbox.addEventListener('touchstart', function(e){
      touchX = e.changedTouches[0].clientX;
    }, {passive:true});
    lightbox.addEventListener('touchend', function(e){
      if (touchX === null || single) return;
      var dx = e.changedTouches[0].clientX - touchX;
      if (Math.abs(dx) > 45) step(dx < 0 ? 1 : -1);
      touchX = null;
    }, {passive:true});
  }

})();
