"""Construye la web de ALAVERA a partir de los textos de /contenido y las fotos de /imagenes.

No hace falta tocar este archivo para cambiar textos o fotos: se editan los .yml de /contenido
(o desde el panel de Pages CMS). GitHub ejecuta esto solo cada vez que se guarda un cambio.
Para probar en local:  python construir.py  →  la web queda en la carpeta _site
"""
import html
import os
import re
import shutil
import glob
import yaml

RAIZ = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(RAIZ, '_site')
DOMINIO = 'https://www.alavera.org'
IDIOMAS = ['es', 'ca', 'en', 'fr']
LOCALE = {'es': 'es_ES', 'ca': 'ca_ES', 'en': 'en_GB', 'fr': 'fr_FR'}
GRUPOS = ['gira', 'pedagogia', 'colaboraciones']
MENU = {'gira': 'menu_gira', 'pedagogia': 'menu_pedagogia', 'colaboraciones': 'menu_colaboraciones', 'compania': 'menu_compania'}
# Direcciones de la web antigua (Squarespace) que se redirigen a las nuevas
ANTIGUAS = {'creaciones/american-portraiture-k5z37': 'a-medio-camino', 'creaciones/the-ruse-7ls44': 'happy-everything',
            'creaciones/chotto-motto-e5trn': 'blue-monday', 'creaciones': '', 'info': 'compania', 'contacto': '#contacto'}

FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&amp;family=Playfair+Display:ital,wght@0,400;1,400&amp;family=Inter+Tight:ital,wght@0,700;1,400&amp;family=Inter:wght@400;500&amp;display=swap">')
HAM = '<svg viewBox="0 0 28 18" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M0 1h28M0 9h28M0 17h28"></path></svg>'
PLAY = '<svg viewBox="0 0 80 80" fill="none" aria-hidden="true"><circle cx="40" cy="40" r="38.5" stroke="currentColor" stroke-width="1.5"></circle><path d="M33 27 L55 40 L33 53 Z" fill="currentColor"></path></svg>'
INSTA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="5"></rect><circle cx="12" cy="12" r="4.2"></circle><circle cx="17.4" cy="6.6" r="1" fill="currentColor" stroke="none"></circle></svg>'

e = lambda s: html.escape(str(s or ''), quote=True)


def leer(ruta):
    with open(os.path.join(RAIZ, ruta), encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def inl(s):
    """Texto de una línea: *así* sale en cursiva."""
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', e(s).strip())


def bloques(texto, sangria='    '):
    """Párrafos separados por una línea en blanco; los que empiezan por > salen como cita."""
    out = []
    for p in re.split(r'\n\s*\n', (texto or '').strip()):
        p = ' '.join(l.strip() for l in p.splitlines()).strip()
        if not p:
            continue
        if p.startswith('>'):
            out.append(f'<p class="pz-cita">{inl(p[1:])}</p>')
        else:
            out.append(f'<p>{inl(p)}</p>')
    return ('\n' + sangria).join(out)


def plano(s):
    return re.sub(r'\s+', ' ', re.sub(r'[*>]', '', str(s or ''))).strip()


# ------------------------------------------------------------------ datos
G = leer('contenido/general.yml')
PORTADA = leer('contenido/portada.yml')
CIA = leer('contenido/compania.yml')
P = {}
for ruta in sorted(glob.glob(os.path.join(RAIZ, 'contenido/proyectos/*.yml'))):
    slug = os.path.splitext(os.path.basename(ruta))[0]
    P[slug] = leer(os.path.relpath(ruta, RAIZ))
    P[slug]['slug'] = slug


TABLEROS = PORTADA.get('tableros', []) or []
TAB_GRUPO = {'en-gira': 'gira', 'pedagogia': 'pedagogia', 'colaboraciones': 'colaboraciones'}
# Una sección se puede apagar desde el Inicio (mostrar: false): desaparece del menú, de la portada y sus páginas no se publican.
VISIBLE = {g: True for g in GRUPOS}
for _tab in TABLEROS:
    if TAB_GRUPO.get(_tab.get('id')):
        VISIBLE[TAB_GRUPO[_tab['id']]] = _tab.get('mostrar', True) is not False


def grupo_de(p):
    """Sección en la que vive la página de un proyecto (None si su sección está apagada)."""
    if VISIBLE.get(p.get('grupo')):
        return p['grupo']
    if VISIBLE.get(p.get('tambien_en')):
        return p['tambien_en']
    return None


PUBLICADOS = [s for s, p in P.items() if grupo_de(p)]


def secuencia(grupo):
    """Orden de anterior/siguiente: el mismo orden que las fotos de ese tablero en el Inicio."""
    if not VISIBLE[grupo]:
        return []
    orden = []
    for tab in TABLEROS:
        if TAB_GRUPO.get(tab.get('id')) == grupo:
            for f in tab.get('fotos', []) or []:
                s = f.get('proyecto')
                if s in PUBLICADOS and s not in orden:
                    orden.append(s)
    resto = sorted([p for p in P.values() if p['slug'] in PUBLICADOS and p['slug'] not in orden
                    and (p.get('grupo') == grupo or p.get('tambien_en') == grupo)], key=lambda p: p.get('orden', 99))
    return orden + [p['slug'] for p in resto]


SEC = {g: secuencia(g) for g in GRUPOS}
PRIMERA = {g: (SEC[g][0] if SEC[g] else '') for g in GRUPOS}
PRIMERA['compania'] = 'compania'

# Colocación automática de las fotos de cada tablero (columna, fila, velocidad, encima), en el orden de la lista.
HUECOS = [('2 / 7', 1, 6, 0.04, False), ('7 / 12', 3, 6, 0.12, False), ('1 / 6', 7, 6, -0.05, False),
          ('6 / 11', 9, 5, 0.08, False), ('3 / 8', 13, 6, 0.02, False), ('8 / 12', 14, 5, -0.1, True),
          ('5 / 9', 19, 4, -0.06, False)]


def hueco(k):
    col, fila, alto, vel, encima = HUECOS[k % len(HUECOS)]
    fila += 22 * (k // len(HUECOS))
    return col, f'{fila} / {fila + alto}', vel, encima


# ------------------------------------------------------------------ rutas
def archivo(lang, clave):
    """clave '' = inicio, 'compania', o el slug de un proyecto."""
    pref = '' if lang == 'es' else lang + '/'
    return pref + ('index.html' if clave == '' else clave + '/index.html')


def enlace(desde, lang, clave, ancla=''):
    destino = archivo(lang, clave)
    hondo = desde.count('/')
    rel = '../' * hondo + destino
    rel = rel[:-len('index.html')] or './'
    return rel + ancla


def recurso(desde, ruta):
    return '../' * desde.count('/') + str(ruta or '').lstrip('/')


def url_abs(lang, clave):
    a = archivo(lang, clave)
    return DOMINIO + '/' + a[:-len('index.html')]


# ------------------------------------------------------------------ piezas comunes
def cabeza(lang, clave, titulo, descripcion, imagen, desde):
    alternos = ''.join(f'<link rel="alternate" hreflang="{l}" href="{url_abs(l, clave)}">' for l in IDIOMAS)
    alternos += f'<link rel="alternate" hreflang="x-default" href="{url_abs("es", clave)}">'
    return f'''<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<link rel="canonical" href="{url_abs(lang, clave)}">
{alternos}
<meta property="og:type" content="website">
<meta property="og:site_name" content="ALAVERA">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:image" content="{DOMINIO}/{e(str(imagen).lstrip('/'))}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="{recurso(desde, 'marca/favicon.png')}">
<link rel="apple-touch-icon" href="{recurso(desde, 'marca/icono.png')}">
{FUENTES}
<link rel="stylesheet" href="{recurso(desde, 'estilo/inicio.css')}">
<link rel="stylesheet" href="{recurso(desde, 'estilo/proyecto.css')}">
<link rel="stylesheet" href="{recurso(desde, 'estilo/web.css')}">
<script src="{recurso(desde, 'estilo/web.js')}" defer></script>
</head>'''


def idiomas(lang, clave, desde):
    t = G[lang]
    partes = []
    for l in IDIOMAS:
        if l == lang:
            partes.append(f'<a href="{enlace(desde, l, clave)}" class="actual" aria-current="true" lang="{l}">{l.upper()}</a>')
        else:
            partes.append(f'<a href="{enlace(desde, l, clave)}" lang="{l}" hreflang="{l}">{l.upper()}</a>')
    return f'<span class="idiomas" aria-label="{e(t["idioma"])}">' + ''.join(partes) + '</span>'


def menu(lang, desde, actual, portada):
    t = G[lang]
    lis = []
    for g in ['gira', 'pedagogia', 'colaboraciones', 'compania']:
        if not PRIMERA.get(g):
            continue
        c = ' class="actual"' if g == actual else ''
        lis.append(f'<li><a href="{enlace(desde, lang, PRIMERA[g])}"{c}>{e(t[MENU[g]])}</a></li>')
    pie = (f'<a href="#contacto">{e(t["contacto"])}</a>' if portada else
           f'<a href="{enlace(desde, lang, "")}">{e(t["inicio"])}</a><a href="{enlace(desde, lang, "", "#contacto")}">{e(t["contacto"])}</a>')
    return f'''<div class="menu-capa" hidden>
  <button class="menu-fondo" type="button" aria-label="{e(t["cerrar"])}"></button>
  <div class="menu-bloque" role="dialog" aria-modal="true" aria-label="Menú">
    <img src="{recurso(desde, 'marca/simbolo-negro.png')}" alt="">
    <ul class="menu-lista">
      {"".join(lis)}
    </ul>
    <div class="menu-lado">
      <button class="menu-cerrar" type="button">{e(t["cerrar"])}</button>
      <div class="menu-pie">{pie}</div>
    </div>
  </div>
</div>'''


def cabecera(lang, clave, desde, actual, portada):
    t = G[lang]
    inicio = '#inicio' if portada else enlace(desde, lang, '')
    boton = f'<button class="boton-menu" type="button" aria-label="{e(t["abrir_menu"])}">{HAM}</button>'
    cab = ''
    if portada:
        cab = f'''<header class="cab">
  <a class="cab-iso" href="{inicio}" aria-label="ALAVERA"><img src="{recurso(desde, 'marca/simbolo-blanco.png')}" alt=""></a>
  <div class="cab-der">{idiomas(lang, clave, desde)}{boton}</div>
</header>
'''
    else:
        cab = f'''<header class="cab">
  <a class="cab-iso" href="{inicio}" aria-label="ALAVERA"><img src="{recurso(desde, 'marca/simbolo-blanco.png')}" alt=""></a>
</header>
'''
    return cab + menu(lang, desde, actual, portada) + f'''
<nav class="barra{'' if portada else ' dentro'}" aria-label="Principal">
  <a class="barra-iso" href="{inicio}" aria-label="ALAVERA"><img src="{recurso(desde, 'marca/simbolo-negro.png')}" alt=""></a>
  <div class="barra-der">{idiomas(lang, clave, desde)}{boton}</div>
</nav>'''


def pie(lang):
    t = G[lang]
    return f'''<footer class="pie">
  <div class="pie-arriba">
    <a class="pie-insta" href="{e(G["instagram"])}" aria-label="Instagram" rel="noopener" target="_blank">{INSTA}</a>
    <a class="pie-boton" href="mailto:{e(G["correo"])}">{e(t["escribenos"])}</a>
  </div>
  <div class="pie-legal">
    <p>{e(t["derechos"])}</p>
    <small>{e(G["legal"])} · {e(G["correo"])}</small>
  </div>
</footer>'''


def documento(lang, clave, titulo, descripcion, imagen, cuerpo, actual, portada=False, clase=''):
    desde = archivo(lang, clave)
    return f'''<!doctype html>
<html lang="{lang}">
{cabeza(lang, clave, titulo, descripcion, imagen, desde)}
<body>
<div class="raiz velo-oscuro{(' ' + clase) if clase else ''}">
<a class="saltar" href="#contenido">{'Saltar al contenido' if lang == 'es' else {'ca': 'Salta al contingut', 'en': 'Skip to content', 'fr': 'Aller au contenu'}[lang]}</a>
{cabecera(lang, clave, desde, actual, portada)}
<main id="contenido">
{cuerpo}
</main>
{pie(lang)}
</div>
</body>
</html>
'''


def boton_copiar(lang):
    t = G[lang]
    return f'<button class="copiar" type="button" data-correo="{e(G["correo"])}" data-copiado="{e(t["copiado"])}">{e(t["copiar"])}</button>'


# ------------------------------------------------------------------ inicio
def inicio(lang):
    clave = ''
    desde = archivo(lang, clave)
    t = G[lang]
    d = PORTADA[lang]
    capas = []
    for k, f in enumerate(PORTADA.get('carrusel', []) or []):
        if isinstance(f, str):
            f = {'imagen': f}
        estado = ' activa' if k == 0 else ''
        capas.append(f'<span class="carrusel-capa{estado}"><img src="{recurso(desde, f["imagen"])}" alt=""{"" if k == 0 else " loading=\"lazy\""}></span>')
    acep = []
    for k, a in enumerate(d.get('acepciones', [])):
        cat = f'<span class="cat">{e(d.get("categoria"))}</span>' if k == 0 else ''
        acep.append(f'<p class="acepcion">{cat}<span class="num">{k + 1}.</span>{inl(a)}</p>')

    # frase que se enciende palabra a palabra
    pal = []
    dentro = False
    for w in str(d.get('frase', '')).split():
        abre = w.startswith('*')
        cierra = '*' in w[1:] if abre else '*' in w
        if abre:
            dentro = True
        pal.append(f'<span class="palabra{" cursiva" if dentro else ""}">{e(w.replace("*", ""))} </span>')
        if cierra:
            dentro = False

    tableros = []
    visibles = [tab for tab in TABLEROS if tab.get('mostrar', True) is not False]
    for n, tab in enumerate(visibles):
        teselas = []
        fotos = [f for f in (tab.get('fotos') or []) if f.get('proyecto') in PUBLICADOS and f.get('imagen')]
        for k, f in enumerate(fotos):
            p = P[f['proyecto']]
            pl = p.get(lang, {})
            fl = f.get(lang, {}) or {}
            nombre = pl.get('titulo', '')
            col, fila, vel, encima = hueco(k)
            col, fila = f.get('columna') or col, f.get('fila') or fila
            vel = f.get('velocidad', vel)
            enc = ' encima' if f.get('encima', encima) else ''
            dato = fl.get('dato') or pl.get('datos', '')
            teselas.append(f'''    <a class="tesela{enc}" href="{enlace(desde, lang, f["proyecto"])}" data-vel="{vel}" style="grid-column: {e(col)}; grid-row: {e(fila)}">
      <img src="{recurso(desde, f["imagen"])}" alt="{e(nombre)}" loading="lazy">
      <span class="velo"><span class="t-nombre">{e(nombre)}</span><span class="t-dato">{e(dato)}</span><span class="t-linea">{inl(fl.get("linea"))}</span></span>
    </a>''')
        tid = 't-' + tab['id']
        ultimo = ' ultimo' if n == len(visibles) - 1 else ''
        tableros.append(f'''<section class="tablero{ultimo}" id="{e(tab["id"])}" data-vigilar aria-labelledby="{tid}">
  <div class="gigante-pista"><h2 class="gigante" id="{tid}">{e(tab["titulo"][lang])}</h2></div>
  <div class="collage">
{chr(10).join(teselas)}
  </div>
</section>''')

    cuerpo = f'''<div class="escena" id="inicio" data-segundos="{PORTADA.get("segundos", 3)}">
  <div class="escena-fija">
    <div class="carrusel" aria-hidden="true">
      {"".join(capas)}
    </div>
    <div class="sello">
      <img src="{recurso(desde, 'marca/sello.png')}" alt="Alavera · Agnès Sales &amp; Héctor Plaza">
    </div>
    <section class="portada">
      <p class="portada-izq"><strong>Alavera</strong> — {inl(d.get("intro"))}</p>
      <div class="definicion">
        <h1 class="entrada">{e(d.get("palabra"))}</h1>
        <span class="silabas">{e(d.get("silabas")).replace("   ", " &nbsp; ")}</span>
        {"".join(acep)}
      </div>
      <div class="portada-marca">
        <span class="logo-partes">
          <img class="logo-iso" src="{recurso(desde, 'marca/logo.png')}" alt="Alavera">
          <img class="logo-letras" src="{recurso(desde, 'marca/logo.png')}" alt="">
        </span>
      </div>
    </section>
  </div>
</div>

<section class="manifiesto">
  <p class="revela">{"".join(pal)}</p>
</section>

{chr(10).join(tableros)}

<section class="escribir" id="contacto" data-vigilar>
  <span class="etiqueta aparece">{e(t["contacto"])}</span>
  <h2 class="aparece">{inl(d.get("contacto_titulo"))}</h2>
  <p class="aparece">{inl(d.get("contacto_texto"))}</p>
  <a class="correo aparece" href="mailto:{e(G["correo"])}">{e(G["correo"])}</a>
  <span class="aparece">{boton_copiar(lang)}</span>
</section>'''
    titulo = 'ALAVERA · Agnès Sales & Héctor Plaza'
    primera = (PORTADA.get('carrusel') or ['marca/logo.png'])[0]
    img = (primera.get('imagen') if isinstance(primera, dict) else primera).lstrip('/')
    return documento(lang, clave, titulo, t['descripcion'], img, cuerpo, actual='', portada=True)


# ------------------------------------------------------------------ proyecto
def pedir(lang, titular, texto):
    t = G[lang]
    return f'''<section class="pz-pedir entra">
  <span class="etiqueta">{e(t["contacto"])}</span>
  <h2>{inl(titular)}</h2>
  <p>{inl(texto or t["pedir_texto"])}</p>
  <a class="correo" href="mailto:{e(G["correo"])}">{e(G["correo"])}</a>
  {boton_copiar(lang)}
</section>'''


def galeria(desde, fotos, alt, lang, campo='credito'):
    t = G[lang]
    figs = []
    for f in fotos or []:
        pie_txt = f.get(campo) or ''
        if pie_txt and campo == 'credito':
            pie_txt = f'{t["foto"]}: {pie_txt}'
        cap = f'<figcaption>{e(pie_txt)}</figcaption>' if pie_txt else ''
        figs.append(f'<figure class="pz-foto {e(f.get("tamano", "ancha"))} entra"><img src="{recurso(desde, f["imagen"])}" alt="{e(alt)}" loading="lazy">{cap}</figure>')
    if not figs:
        return ''
    return '<section class="pz-galeria" aria-label="Fotos">\n  ' + '\n  '.join(figs) + '\n</section>'


def proyecto(lang, slug):
    p = P[slug]
    d = p[lang]
    t = G[lang]
    desde = archivo(lang, slug)
    grupo = grupo_de(p)
    sec = SEC[grupo]
    k = sec.index(slug)
    ant, sig = sec[(k - 1) % len(sec)], sec[(k + 1) % len(sec)]

    cred = f'<span class="pz-credito">{e(t["foto"])}: {e(p["credito_principal"])}</span>' if p.get('credito_principal') else ''
    ficha = ''.join(f'<dt>{e(x.get("dato"))}</dt><dd>{inl(x.get("valor"))}</dd>' for x in d.get('ficha', []) or [])

    video = ''
    v = p.get('video') or ''
    if v:
        poster = recurso(desde, p.get('video_portada') or p['foto_principal'])
        dentro = f'<img src="{poster}" alt="" loading="lazy"><span class="video-play">{PLAY}<span>{e(d.get("boton_video"))}</span></span>'
        if v.startswith('http'):
            principal = f'<a class="video" href="{e(v)}" target="_blank" rel="noopener">{dentro}</a>'
        else:
            principal = f'<button class="video" type="button" data-youtube="{e(v)}" aria-label="{e(d.get("boton_video"))}: {e(d.get("titulo"))}">{dentro}</button>'
        mas = ''.join(f'<a href="https://www.youtube.com/watch?v={e(m.get("youtube"))}" target="_blank" rel="noopener">{e(m.get("nombre"))}</a>' +
                      (f'<span>{e(m.get("duracion"))}</span>' if m.get('duracion') else '') for m in d.get('mas_videos', []) or [])
        mas = f'\n  <div class="mas-videos">{mas}</div>' if mas else ''
        video = f'<section class="pz-video entra" aria-label="Vídeo">\n  {principal}{mas}\n</section>'

    extra = ''
    tb = p.get('tambien')
    if tb and tb.get('proyecto') in PUBLICADOS:
        otro = P[tb['proyecto']][lang]
        extra = f'''<a class="pz-tambien entra" href="{enlace(desde, lang, tb["proyecto"])}">
  <img src="{recurso(desde, tb["imagen"])}" alt="" loading="lazy">
  <span class="pz-tambien-txt"><span class="pz-rotulo">{e(d.get("tambien_rotulo"))}</span><strong>{e(otro.get("titulo"))}</strong><span>{inl(d.get("tambien_texto"))}</span><span class="pz-tambien-ir">{e(d.get("tambien_enlace"))}</span></span>
</a>'''

    pasar = f'''<nav class="pz-pasar" aria-label="Más proyectos">
  <a href="{enlace(desde, lang, ant)}"><span class="pz-rotulo">{e(t["anterior"])}</span><strong>{e(P[ant][lang]["titulo"])}</strong></a>
  <a href="{enlace(desde, lang, sig)}"><span class="pz-rotulo">{e(t["siguiente"])}</span><strong>{e(P[sig][lang]["titulo"])}</strong></a>
</nav>'''

    cuerpo = f'''<section class="pz-hero" aria-label="{e(d["titulo"])}">
  <img src="{recurso(desde, p["foto_principal"])}" alt="{e(d["titulo"])}" style="object-position: {e(p.get("encuadre", "50% 50%"))}">
  {cred}
</section>

<section class="pz-texto">
  <div class="pz-cab entra">
    <span class="pz-rotulo">{e(d.get("rotulo"))}</span>
    <h1>{e(d["titulo"])}</h1>
    <p class="pz-meta">{e(d.get("datos"))}</p>
  </div>
  <div class="pz-cuerpo entra">
    {bloques(d.get("texto"))}
    <dl class="ficha">{ficha}</dl>
  </div>
</section>

{video}

{extra}

{galeria(desde, p.get("galeria"), d["titulo"], lang)}

{pedir(lang, d.get("pedir"), None)}

{pasar}'''
    desc = plano(d.get('texto', '')).split('. ')[0][:180]
    return documento(lang, slug, f'{d["titulo"]} · ALAVERA', desc, p['foto_principal'], cuerpo, actual=grupo, clase='pagina')


# ------------------------------------------------------------------ compañía
def compania(lang):
    d = CIA[lang]
    desde = archivo(lang, 'compania')
    premios = ''.join(f'<li><strong>{e(x.get("premio"))}</strong><span>{inl(x.get("detalle"))}</span></li>' for x in d.get('premios', []) or [])
    cuerpo = f'''<section class="pz-hero" aria-label="{e(d["titulo"])}">
  <img src="{recurso(desde, CIA["foto_principal"])}" alt="{e(d["titulo"])}" style="object-position: {e(CIA.get("encuadre", "50% 50%"))}">
</section>

<section class="pz-texto">
  <div class="pz-cab entra">
    <span class="pz-rotulo">{e(d.get("rotulo"))}</span>
    <h1>{e(d["titulo"])}</h1>
    <p class="pz-meta">{e(d.get("datos"))}</p>
  </div>
  <div class="pz-cuerpo entra">
    {bloques(d.get("texto"))}
  </div>
</section>

<section class="cia-bloques">
  <div class="cia-bloque entra">
    <h2>{e(d.get("creacion_titulo"))}</h2>
    <p>{inl(d.get("creacion"))}</p>
  </div>
  <div class="cia-bloque entra">
    <h2>{e(d.get("formacion_titulo"))}</h2>
    <p>{inl(d.get("formacion"))}</p>
  </div>
  <div class="cia-bloque entra">
    <h2>{e(d.get("premios_titulo"))}</h2>
    <ul class="premios">{premios}</ul>
  </div>
</section>

{galeria(desde, CIA.get("galeria"), d["titulo"], lang, campo="pie")}

{pedir(lang, d.get("pedir"), d.get("pedir_texto"))}'''
    desc = plano(d.get('texto', '')).split('. ')[0][:180]
    return documento(lang, 'compania', f'{G[lang]["menu_compania"]} · ALAVERA', desc, CIA['foto_principal'], cuerpo, actual='compania', clase='pagina')


# ------------------------------------------------------------------ otras
def no_existe():
    t = G['es']
    lang = 'es'
    cuerpo = f'''<section class="no-existe">
  <h1>{e(t["no_existe"])}</h1>
  <p>{e(t["no_existe_texto"])}</p>
  <a class="pie-boton" href="/">{e(t["volver"])}</a>
</section>'''
    doc = documento(lang, '', f'{t["no_existe"]} · ALAVERA', t['descripcion'], 'marca/logo.png', cuerpo, actual='', clase='pagina')
    # la 404 se sirve desde cualquier dirección: rutas absolutas
    return re.sub(r'(href|src)="(?:\./)?(estilo|marca|imagenes)/', r'\1="/\2/', doc).replace('href="./"', 'href="/"')


def redireccion(destino):
    url = '/' + destino if not destino.startswith('#') else '/' + destino
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>ALAVERA</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{DOMINIO}{url}">
<meta http-equiv="refresh" content="0; url={url}">
</head><body><p><a href="{url}">ALAVERA</a></p></body></html>
'''


def escribir(ruta, txt):
    ruta = os.path.join(SALIDA, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(txt)


def construir():
    if os.path.exists(SALIDA):
        shutil.rmtree(SALIDA)
    os.makedirs(SALIDA)
    for carpeta in ['estilo', 'marca', 'imagenes']:
        shutil.copytree(os.path.join(RAIZ, carpeta), os.path.join(SALIDA, carpeta))
    urls = []
    for lang in IDIOMAS:
        escribir(archivo(lang, ''), inicio(lang))
        escribir(archivo(lang, 'compania'), compania(lang))
        urls += [url_abs(lang, ''), url_abs(lang, 'compania')]
        for slug in PUBLICADOS:
            escribir(archivo(lang, slug), proyecto(lang, slug))
            urls.append(url_abs(lang, slug))
    escribir('404.html', no_existe())
    for vieja, nueva in ANTIGUAS.items():
        escribir(vieja + '/index.html', redireccion(nueva))
    escribir('CNAME', 'www.alavera.org\n')
    escribir('.nojekyll', '')
    escribir('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n')
    escribir('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
             ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    print(f'Web construida en {SALIDA}: {len(urls)} páginas')


if __name__ == '__main__':
    construir()
