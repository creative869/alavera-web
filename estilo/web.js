/* ALAVERA · comportamiento de la web (menú, portada en escena, texto que se enciende,
   fotos que se mueven a distinta velocidad, foto que crece al pasar el ratón, scroll suave). */
(function () {
  'use strict';
  var raiz = document.querySelector('.raiz');
  if (!raiz) return;
  var doc = document.documentElement;
  var quieto = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var sinRaton = window.matchMedia && window.matchMedia('(any-hover: none)').matches;
  var conScroll = function () { return doc.scrollHeight > window.innerHeight + 80; };

  /* ---------- Menú ---------- */
  var menu = document.querySelector('.menu-capa');
  function abrir() { if (menu) { menu.hidden = false; var c = menu.querySelector('.menu-cerrar'); if (c) c.focus(); } }
  function cerrar() { if (menu) menu.hidden = true; }
  document.querySelectorAll('.boton-menu').forEach(function (b) { b.addEventListener('click', abrir); });
  if (menu) {
    menu.querySelectorAll('.menu-fondo, .menu-cerrar, a').forEach(function (b) { b.addEventListener('click', cerrar); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') cerrar(); });
  }

  /* ---------- Copiar correo ---------- */
  document.querySelectorAll('.copiar').forEach(function (b) {
    var texto = b.textContent, hecho = b.getAttribute('data-copiado') || 'OK', t;
    b.addEventListener('click', function () {
      var listo = function () { b.textContent = hecho; clearTimeout(t); t = setTimeout(function () { b.textContent = texto; }, 2000); };
      try { navigator.clipboard.writeText(b.getAttribute('data-correo')).then(listo, listo); } catch (e) { listo(); }
    });
  });

  /* ---------- Vídeos: el póster se cambia por YouTube al pulsar ---------- */
  document.querySelectorAll('button.video[data-youtube]').forEach(function (b) {
    b.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-youtube') + '?autoplay=1&rel=0';
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen = true;
      f.title = b.getAttribute('aria-label') || 'Vídeo';
      var marco = document.createElement('div');
      marco.className = 'video';
      marco.appendChild(f);
      b.replaceWith(marco);
    });
  });

  /* ---------- Aparecer al entrar en pantalla (y volver a irse al salir) ---------- */
  if ('IntersectionObserver' in window) {
    raiz.classList.add('anima');
    var vigia = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) { e.target.classList.toggle('visto', e.isIntersecting); });
    }, { threshold: 0.05, rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('[data-vigilar], .entra').forEach(function (el) { vigia.observe(el); });
  }

  /* ---------- Portada: carrusel ---------- */
  var escena = document.querySelector('.escena');
  var capas = document.querySelectorAll('.carrusel-capa');
  if (capas.length > 1) {
    var i = 0, seg = Math.max(2, parseFloat(escena && escena.getAttribute('data-segundos')) || 3);
    setInterval(function () {
      capas[i].classList.remove('activa');
      capas.forEach(function (c) { c.classList.remove('previa'); });
      capas[i].classList.add('previa');
      i = (i + 1) % capas.length;
      capas[i].classList.add('activa');
    }, seg * 1000);
  }

  /* ---------- Scroll: barra, texto que se enciende, títulos gigantes, escena y profundidad ---------- */
  var barra = document.querySelector('.barra');
  var esPortada = !!escena;
  var revela = document.querySelector('.revela');
  var palabras = revela ? revela.querySelectorAll('.palabra') : [];
  var tras = document.querySelector('.manifiesto');
  var cuadro = null, yLupa;

  function profundidad() {
    cuadro = null;
    var alto = window.innerHeight;
    var mueve = !quieto && conScroll();
    var activo = mueve && window.innerWidth > 640;

    // Títulos gigantes: se deslizan en horizontal y pasan a gris cuando llegan las fotos
    document.querySelectorAll('.tablero').forEach(function (sec) {
      if (!mueve) { sec.style.removeProperty('--avance'); sec.style.removeProperty('--g'); return; }
      var r = sec.getBoundingClientRect();
      sec.style.setProperty('--avance', Math.min(1, Math.max(0, (alto - r.top) / (r.height + alto * 0.4))).toFixed(3));
      sec.style.setProperty('--g', r.top < alto * 0.15 ? '1' : '0');
    });

    // Portada en escena
    if (escena) {
      if (!mueve || window.innerWidth <= 1000) {
        ['--p', '--alto', '--recorrido'].forEach(function (v) { escena.style.removeProperty(v); });
      } else {
        var recorrido = Math.round(alto * 2.4), pausa = Math.round(alto * 1.3);
        escena.style.setProperty('--alto', alto + 'px');
        escena.style.setProperty('--recorrido', (recorrido + pausa) + 'px');
        escena.style.setProperty('--p', Math.min(1, Math.max(0, window.scrollY / recorrido)).toFixed(3));
      }
    }

    // Cada foto de los collages a su propia velocidad
    document.querySelectorAll('.collage [data-vel]').forEach(function (el) {
      if (!activo) { el.style.removeProperty('--py'); return; }
      var r = el.getBoundingClientRect();
      if (r.bottom < -alto || r.top > alto * 2) return;
      var vel = parseFloat(el.getAttribute('data-vel')) || 0;
      el.style.setProperty('--py', Math.round(-(r.top + r.height / 2 - alto / 2) * vel) + 'px');
    });
  }
  function pedirProfundidad() { if (!cuadro) cuadro = requestAnimationFrame(profundidad); }

  function alBajar() {
    if (yLupa !== undefined && Math.abs(window.scrollY - yLupa) > 60) {
      document.querySelectorAll('.tesela.grande').forEach(function (t) { t.classList.remove('grande'); });
      yLupa = undefined;
    }
    var alto = window.innerHeight;
    if (esPortada && barra) {
      var bajado = tras ? tras.getBoundingClientRect().top < alto * 0.75 : window.scrollY > alto * 0.6;
      barra.classList.toggle('dentro', bajado);
    }
    if (revela && palabras.length) {
      var n = palabras.length;
      if (conScroll()) {
        var r = revela.getBoundingClientRect();
        var avance = Math.min(1, Math.max(0, (alto * 0.85 - r.top) / (r.height + alto * 0.35)));
        n = Math.round(avance * palabras.length);
      }
      palabras.forEach(function (p, k) { p.classList.toggle('on', k < n); });
    }
    pedirProfundidad();
  }
  window.addEventListener('scroll', alBajar, { passive: true });
  window.addEventListener('resize', alBajar);
  alBajar();

  /* ---------- Foto que crece en su sitio al pasar el ratón (solo ordenador) ---------- */
  function puedeLupa() { return !sinRaton && window.innerWidth > 900 && conScroll(); }
  if (puedeLupa()) raiz.classList.add('con-lupa');
  var tLupa;
  document.addEventListener('mouseover', function (ev) {
    var t = ev.target.closest && ev.target.closest('.collage .tesela');
    if (!t || t.classList.contains('grande') || !puedeLupa()) return;
    raiz.classList.add('con-lupa');
    clearTimeout(tLupa);
    tLupa = setTimeout(function () {
      var r = t.getBoundingClientRect();
      t.style.setProperty('--s', Math.max(1.12, Math.min(1.3, 1 + 90 / Math.max(r.width, 1))).toFixed(3));
      t.classList.add('grande');
      yLupa = window.scrollY;
    }, 110);
  });
  document.addEventListener('mouseout', function (ev) {
    var t = ev.target.closest && ev.target.closest('.collage .tesela');
    if (!t || (ev.relatedTarget && t.contains(ev.relatedTarget))) return;
    clearTimeout(tLupa);
    t.classList.remove('grande');
  });

  /* ---------- Scroll más lento y suave con la rueda del ratón ---------- */
  if (!quieto) {
    var objetivo = window.scrollY, deslizando = false;
    var deslizar = function () {
      deslizando = true;
      var y = window.scrollY, d = objetivo - y;
      if (Math.abs(d) < 0.5) { window.scrollTo(0, objetivo); deslizando = false; return; }
      window.scrollTo(0, y + d * 0.06);
      requestAnimationFrame(deslizar);
    };
    window.addEventListener('wheel', function (ev) {
      if (ev.ctrlKey || sinRaton || window.innerWidth <= 900 || !conScroll()) return;
      if (menu && !menu.hidden) return;
      ev.preventDefault();
      var max = doc.scrollHeight - window.innerHeight;
      if (!deslizando) objetivo = window.scrollY;
      var paso = ev.deltaMode === 1 ? ev.deltaY * 32 : ev.deltaY;
      objetivo = Math.max(0, Math.min(max, objetivo + paso * 0.28));
      if (!deslizando) deslizar();
    }, { passive: false });
  }
})();
