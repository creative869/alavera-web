# Web de ALAVERA · www.alavera.org

## Cambiar textos y fotos (sin tocar código)

1. Entra en **https://app.pagescms.org** y pulsa *Sign in with GitHub* con la cuenta **creative869**.
2. Elige el repositorio **alavera-web**.
3. En el menú de la izquierda tienes cada página: *Inicio*, *Compañía*, cada proyecto y *Menú, pie y botones*.
   Dentro de cada una, los textos están separados por idioma (Castellano, Català, English, Français).
4. Cambia lo que quieras y pulsa **Save**. En uno o dos minutos la web se actualiza sola.

Trucos:
- Entre `*asteriscos*` el texto sale en *cursiva*.
- En los textos largos, deja una línea en blanco entre párrafos. Si un párrafo empieza por `>` sale como cita grande.
- Fotos: en *Media* puedes subir fotos nuevas. Luego, en cualquier campo de foto, elige cuál va.
  Mejor JPG de unos 2000 px de ancho y menos de 600 KB.
- Vídeos de YouTube: se pone solo el código, lo que va después de `watch?v=` en el enlace.
- En la portada, cada foto de los tableros tiene *columna* y *fila* (dónde se coloca en una rejilla de 12 columnas)
  y *velocidad* (cuánto se mueve al hacer scroll).

## Cómo está hecha

- `contenido/` — todos los textos, en archivos `.yml`.
- `imagenes/` — las fotos. `marca/` — logo, símbolo y sello.
- `estilo/` — diseño (CSS) y animaciones (JS).
- `construir.py` — junta todo y genera la web. GitHub lo ejecuta solo en cada cambio
  (`.github/workflows/publicar.yml`) y la publica con GitHub Pages.

Idiomas: castellano en `alavera.org/`, catalán en `/ca/`, inglés en `/en/` y francés en `/fr/`.

## Dominio

La web se sirve con GitHub Pages en **www.alavera.org**. En el DNS del dominio:
- `www` → registro CNAME a `creative869.github.io`
- dominio sin www (`@`) → registros A a 185.199.108.153, 185.199.109.153, 185.199.110.153 y 185.199.111.153
- Los registros **MX** (correo de Google) no se tocan.
