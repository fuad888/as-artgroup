(function(){
  'use strict';

  /* ---- il ---- */
  document.getElementById('year').textContent = new Date().getFullYear();

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
  var setActive = function(){
    var pos = window.scrollY + window.innerHeight * 0.35;
    var current = sections[0];
    sections.forEach(function(s){ if (s.offsetTop <= pos) current = s; });
    links.forEach(function(a){
      a.classList.toggle('is-active', !!current && a.hash === '#' + current.id);
    });
  };
  window.addEventListener('scroll', setActive, {passive:true});
  window.addEventListener('resize', setActive);
  setActive();

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
      console.log('[contact] POST', endpoint, payload);

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
        console.log('[contact] response', result.status, result.data);

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

})();
