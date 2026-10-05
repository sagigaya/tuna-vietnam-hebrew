#!/usr/bin/env python3
"""Transform raw tunavietnam.vn HTML into a static Hebrew mirror.

Steps per page:
  1) Strip <script>...</script> (breaks Next.js hydration; content is pre-rendered)
  2) Rewrite /_next/image?url=<encoded>&w=W&q=75  -> local file path (biggest variant only)
  3) Rewrite direct Sanity CDN URLs -> local images/*
  4) Rewrite internal /en/* links -> *.html
  5) Set <html lang="he" dir="rtl">
  6) Apply string-level translations from TRANSLATIONS dict
"""
import os, re, sys, urllib.parse, shutil, json

SRC = os.path.join(os.path.dirname(__file__), '_mirror_raw')
OUT = os.path.join(os.path.dirname(__file__), 'site')

PAGES = {
    'home.html':          'index.html',
    'about.html':         'about.html',
    'products.html':      'products.html',
    'processing.html':    'processing.html',
    'sustainability.html':'sustainability.html',
    'certifications.html':'certifications.html',
    'contact.html':       'contact.html',
}

INTERNAL_LINKS = {
    '/en':                'index.html',
    '/en/about':          'about.html',
    '/en/products':       'products.html',
    '/en/processing':     'processing.html',
    '/en/sustainability': 'sustainability.html',
    '/en/certifications': 'certifications.html',
    '/en/contact':        'contact.html',
    '/vi':                'index.html',
    '/vi/about':          'about.html',
    '/vi/products':       'products.html',
    '/vi/processing':     'processing.html',
    '/vi/sustainability': 'sustainability.html',
    '/vi/certifications': 'certifications.html',
    '/vi/contact':        'contact.html',
}

# Map Sanity CDN filename -> local file (already downloaded to site/images/)
SANITY_MAP = {
    '25b73ef9c3d81bbbd153ca8479d37e777f663784-614x792.jpg': 'images/25b73ef9c3d81bbbd153ca8479d37e777f663784-614x792.jpg',
    '33dbd80127161337e17d9e41fb9d921d2823814f-1170x353.jpg':'images/33dbd80127161337e17d9e41fb9d921d2823814f-1170x353.jpg',
    '4215b2ec322561a975775dbd1a137ef38f9cfae5-560x370.jpg': 'images/4215b2ec322561a975775dbd1a137ef38f9cfae5-560x370.jpg',
    '757ad556ec4770074e4dbeb9a1ae6ef3d196f921-1170x420.jpg':'images/757ad556ec4770074e4dbeb9a1ae6ef3d196f921-1170x420.jpg',
    '7992e7978c6c03411180c1f7b75c0d2a8b383625-4128x3096.jpg':'images/7992e7978c6c03411180c1f7b75c0d2a8b383625-4128x3096.jpg',
    '83dc128ece80539a7a1136a4ab336a0c7ab19a8d-560x370.jpg': 'images/83dc128ece80539a7a1136a4ab336a0c7ab19a8d-560x370.jpg',
    '9c74699b11f2c5db9ce766b4f02156a25f8047a7-618x872.jpg': 'images/9c74699b11f2c5db9ce766b4f02156a25f8047a7-618x872.jpg',
    'c0e9cc2434c62876f157252c45aac12121a5cd16-1068x657.png':'images/c0e9cc2434c62876f157252c45aac12121a5cd16-1068x657.png',
    'eaa96ce3ed8100a83a022ac9f31b8a5d8f79af70.pdf':         'images/eaa96ce3ed8100a83a022ac9f31b8a5d8f79af70.pdf',
}

def resolve_next_image(nurl):
    """Given /_next/image?url=<enc>&w=W&q=75, return the LOCAL file path."""
    m = re.match(r'/_next/image\?url=([^&]+)&w=\d+&q=\d+', nurl)
    if not m:
        m = re.match(r'/_next/image\?url=([^&]+)', nurl)
        if not m: return nurl
    inner = urllib.parse.unquote(m.group(1))
    # Case A: Sanity CDN
    for fname, local in SANITY_MAP.items():
        if fname in inner:
            return '/' + local
    # Case B: local /images/... path on tunavietnam.vn
    if inner.startswith('/images/'):
        return inner
    return inner  # fallback

def rewrite_srcset(srcset):
    """A srcset is a comma-separated list of `<url> <width>` pairs. Return `local ` (single URL)."""
    parts = [p.strip() for p in srcset.split(',') if p.strip()]
    if not parts: return srcset
    # Prefer the largest 1920w if present, else last one
    chosen = None
    for p in parts:
        if p.endswith(' 1920w'): chosen = p; break
    if not chosen:
        chosen = parts[-1]
    url = chosen.rsplit(' ', 1)[0]
    local = resolve_next_image(url)
    return local  # single URL, no width

def transform(html):
    # 1) Strip all <script>...</script>
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<script\b[^/]*/>', '', html, flags=re.IGNORECASE)
    # Strip preload as="script"
    html = re.sub(r'<link[^>]*rel="preload"[^>]*as="script"[^>]*/?>', '', html, flags=re.IGNORECASE)

    # 2) Rewrite srcSet + src for /_next/image
    #    srcSet contains &amp; from HTML encoding — normalize first
    def _srcset_repl(m):
        raw = m.group(2).replace('&amp;','&')
        new = rewrite_srcset(raw)
        return f'{m.group(1)}"{new}"'
    html = re.sub(r'(srcSet=|srcset=)"([^"]+)"', _srcset_repl, html)

    def _src_repl(m):
        raw = m.group(1).replace('&amp;','&')
        if raw.startswith('/_next/image'):
            return 'src="' + resolve_next_image(raw) + '"'
        return m.group(0)
    html = re.sub(r'src="([^"]+)"', _src_repl, html)

    # 3) Rewrite direct Sanity CDN URLs (in <a href>, etc.)
    for fname, local in SANITY_MAP.items():
        html = html.replace(f'https://cdn.sanity.io/images/hdh8wm5b/production/{fname}', '/'+local)
        html = html.replace(f'https://cdn.sanity.io/files/hdh8wm5b/production/{fname}',  '/'+local)

    # 4) Internal /en/* links -> *.html
    #    Do longest first to avoid /en matching /en/about
    for src, dst in sorted(INTERNAL_LINKS.items(), key=lambda kv: -len(kv[0])):
        html = html.replace(f'href="{src}"', f'href="/{dst}"' if dst != 'index.html' else 'href="/"')

    # 5) lang/dir
    html = html.replace('<html lang="en" class="scroll-smooth">', '<html lang="he" dir="rtl" class="scroll-smooth">')

    # 6) sizes="100vw" attributes are fine; imageSizes preload was removed with scripts stripping? no, it's in <link>
    #    Remove the imageSrcSet preloads because they still point to /_next/image
    html = re.sub(r'<link[^>]*rel="preload"[^>]*as="image"[^>]*/?>', '', html, flags=re.IGNORECASE)

    # 7) Apply translations. Use robust text-node replacement: only substitute inside `>TEXT<` and inside attribute values we care about (alt, title, placeholder, content).
    tpath = os.path.join(os.path.dirname(__file__), 'translations.json')
    with open(tpath) as f:
        raw = json.load(f)
    tr = {k: v for k, v in raw.items() if not k.startswith('_')}

    # 7a) Replace text nodes: match `>SOMETHING<` and if SOMETHING trimmed is a key, translate it (preserving surrounding whitespace)
    def _text_repl(m):
        inner = m.group(1)
        stripped = inner.strip()
        norm = re.sub(r'\s+', ' ', stripped).replace('&amp;','&').replace('&#x27;',"'").replace('&quot;','"').replace('&nbsp;',' ')
        if norm in tr:
            # preserve leading/trailing whitespace
            lead = inner[:len(inner)-len(inner.lstrip())]
            trail = inner[len(inner.rstrip()):]
            return '>' + lead + tr[norm] + trail + '<'
        return m.group(0)
    html = re.sub(r'>([^<>]+)<', _text_repl, html)

    # 7b) Translate specific attributes: content (meta), alt, title, placeholder, aria-label
    def _attr_repl(attr):
        pat = re.compile(rf'\b{attr}="([^"]+)"')
        def _r(m):
            v = m.group(1).replace('&amp;','&').replace('&#x27;',"'").replace('&quot;','"')
            if v in tr:
                return f'{attr}="{tr[v]}"'
            return m.group(0)
        return pat, _r
    for a in ('content','alt','title','placeholder','aria-label'):
        pat,rep = _attr_repl(a)
        html = pat.sub(rep, html)

    # 7c) <title>...</title>
    def _title_repl(m):
        v = m.group(1).replace('&amp;','&')
        return f'<title>{tr.get(v, v)}</title>'
    html = re.sub(r'<title>([^<]+)</title>', _title_repl, html)

    # 8) Wrap phone/email/Latin address strings in dir=ltr so they render correctly inside RTL.
    #    Keys stay in Latin, but under `dir=rtl` the browser reorders +/digits. Force dir=ltr for these.
    ltr_strings = [
        '+84 258 3743666',
        'info@tunavietnam.com',
        'Lot A4-A8, Suoi Dau Industrial Zone, Cam Lam Ward, Khanh Hoa Province, Vietnam',
        'Lot A4-A8, Suoi Dau Industrial Zone, Cam Lam, Khanh Hoa',
        'Tuna Vietnam Co., Ltd',
        'TUNA VIETNAM CO., LTD.',
        'HACCP & BRC Standards',
        'NW/DW: 1880/1350, 1715/1260, 900/680, 200/140, 185/130, 170/120, 160/112, 150/105, 140/98, 130/91, 120/84, 95/68',
        'IVP, IQF',
        'IVP, Retail-ready',
        'Steaks: 4oz, 6oz, 8oz | Saku: 200-300g, 300-500g',
    ]
    for s in ltr_strings:
        # replace the raw string when it appears as a whole text node between > and <
        # (safe: these strings are not translated to Hebrew)
        needle = f'>{s}<'
        replacement = f'><span dir="ltr" style="unicode-bidi:isolate;display:inline-block">{s}</span><'
        html = html.replace(needle, replacement)

    # 9) RTL: flip left/right-anchored horizontal gradients so the "brightened" side
    #    ends up under the Hebrew text (which now sits on the right).
    html = re.sub(r'\bbg-gradient-to-r\b', 'bg-gradient-to-l', html)
    # Force stronger white on the RTL side using an inline linear-gradient (Tailwind's
    # arbitrary-stop classes aren't in the bundled CSS). Replaces the class-defined
    # gradient with an explicit gradient: solid white on the right 30%, fade to transparent by 95%.
    html = html.replace(
        'bg-gradient-to-l from-white via-white/80 to-transparent',
        '" style="background-image:linear-gradient(to left,#fff 0%,#fff 30%,rgba(255,255,255,0.85) 55%,transparent 95%)'
    )

    # 10) Certifications page: make "View Certificate Document" buttons real links.
    #     Source renders <button>...<span>View Certificate Document</span>...</button>
    #     inside each cert card; the JS hydration would attach the file URL.
    #     We patch statically by locating the button after each cert h4 name.
    cert_files = {
        'Dolphin Safe': '/images/cert-dolphin-safe.jpg',
        'BRC':          '/images/cert-brc.jpg',
    }
    for name, href in cert_files.items():
        pattern = re.compile(
            rf'({re.escape(name)}</h4>.*?)<button\b([^>]*)>(.*?)</button>',
            re.DOTALL
        )
        def _mk(href):
            def _r(m):
                return f'{m.group(1)}<a href="{href}" target="_blank" rel="noopener"{m.group(2)}>{m.group(3)}</a>'
            return _r
        html = pattern.sub(_mk(href), html, count=1)

    return html

def main():
    if os.path.exists(OUT):
        # keep _next/ and images/ (already have assets), overwrite HTML
        for f in os.listdir(OUT):
            fp = os.path.join(OUT, f)
            if os.path.isfile(fp) and f.endswith('.html'):
                os.remove(fp)
    else:
        os.makedirs(OUT)

    for src_name, out_name in PAGES.items():
        with open(os.path.join(SRC, src_name)) as f:
            html = f.read()
        html = transform(html)
        with open(os.path.join(OUT, out_name), 'w') as f:
            f.write(html)
        print(f'  {src_name:22s} -> {out_name} ({len(html):>7} chars)')

if __name__ == '__main__':
    main()
