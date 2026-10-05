#!/usr/bin/env python3
"""Build the catalog flow:
   /catalog.html          — chooser: פחיות ↔ פאוצ׳ים  (mimics main Gaya catalog's tuna-type.html)
   /catalog-can.html      — 12 cans, grouped by kosher
   /catalog-pouch.html    — 17 pouches, grouped by kosher

Also injects 'המבחר' nav item into every existing HTML page.
"""
import re, json, os

ROOT = os.path.dirname(__file__)
SITE = os.path.join(ROOT, 'site')

with open('/tmp/tuna_products.json') as f:
    PRODUCTS = json.load(f)

# ---- Group products by type + kosher ----
def kosher_group(p):
    s = p.get('subtitle','')
    if 'לנדא' in s or 'גלאט' in s: return 'לנדא / גלאט'
    if 'עד״ח' in s or 'עדה' in s:   return 'עדה חרדית'
    return 'בית יוסף'

def by_type_kosher():
    tree = {'can': {'בית יוסף':[], 'לנדא / גלאט':[], 'עדה חרדית':[]},
            'pouch':{'בית יוסף':[], 'לנדא / גלאט':[], 'עדה חרדית':[]}}
    for p in PRODUCTS:
        t = p.get('type')
        if t not in tree: continue
        tree[t][kosher_group(p)].append(p)
    return tree

TREE = by_type_kosher()

def has_image(sku):
    for ext in ('.png','.jpg','.jpeg','.webp'):
        if os.path.exists(os.path.join(SITE,'images','products-gaya',sku+ext)):
            return sku+ext
    return None

def size_label(p):
    s = p.get('subtitle','')
    parts = [x.strip() for x in s.split('·')]
    return parts[0] if parts else ''

def kosher_short(p):
    s = p.get('subtitle','')
    if 'לנדא' in s: return 'לנדא'
    if 'גלאט' in s: return 'גלאט'
    if 'עד״ח' in s or 'עדה' in s: return 'עדה חרדית'
    return 'בית יוסף'

# ---- product card ----
def card_html(p):
    img = has_image(p['sku'])
    img_html = (
        f'<img src="/images/products-gaya/{img}" alt="{p["name"]}" '
        f'loading="lazy" class="w-full h-full object-contain p-6 group-hover:scale-105 transition-transform duration-500" />'
        if img else
        f'<div class="w-full h-full flex items-center justify-center text-slate-300 text-xs">בקרוב</div>'
    )
    return f'''
        <div class="card-b2b flex flex-col h-full overflow-hidden group bg-white border border-slate-100/60 hover:border-brand-primary/20 hover:shadow-lg transition-all duration-500 rounded-2xl">
          <div class="relative aspect-square bg-brand-light overflow-hidden">
            {img_html}
            <span class="absolute top-3 left-3 text-[10px] font-bold uppercase tracking-widest bg-white/95 text-brand-primary px-2.5 py-1 rounded-full shadow-sm" dir="ltr">{p["sku"]}</span>
          </div>
          <div class="p-6 flex-grow flex flex-col">
            <h3 class="text-lg font-bold text-slate-900 mb-2 group-hover:text-brand-primary transition-colors leading-tight">{p["name"]}</h3>
            <p class="text-xs text-slate-500 mb-4">{size_label(p)}</p>
            <div class="mt-auto pt-4 border-t border-slate-50 flex items-center justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">כשרות</span>
              <span class="text-xs text-brand-primary font-bold">{kosher_short(p)}</span>
            </div>
          </div>
        </div>'''

def section_html(kosher, products, bg_cls='bg-white'):
    if not products: return ''
    cards = ''.join(card_html(p) for p in products)
    return f'''
    <section class="section-padding {bg_cls}">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="mb-12 flex items-end justify-between">
          <div>
            <span class="text-xs font-bold uppercase tracking-widest text-brand-primary mb-3 block">כשרות</span>
            <h2 class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">{kosher}</h2>
          </div>
          <span class="text-sm text-slate-500 font-medium">{len(products)} מוצרים</span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {cards}
        </div>
      </div>
    </section>'''

def hero_html(kicker, title, subtitle, bg_image):
    return f'''<section class="relative flex items-center overflow-hidden bg-white min-h-[25vh] md:min-h-[30vh]">
      <div class="absolute inset-0 z-0">
        <img src="{bg_image}" alt="" class="w-full h-full object-cover" />
      </div>
      <div class="absolute inset-0 z-10" style="background-image:linear-gradient(to left,#fff 0%,#fff 30%,rgba(255,255,255,0.85) 55%,transparent 95%)"></div>
      <div class="relative z-20 w-full container mx-auto px-6 lg:px-8 max-w-7xl py-14 md:py-16">
        <div class="max-w-4xl mr-auto">
          <span class="text-xs font-bold uppercase tracking-widest text-brand-primary mb-3 block">{kicker}</span>
          <h1 class="font-display font-bold tracking-tighter leading-[1] text-balance flex flex-wrap items-baseline gap-x-10 text-3xl md:text-4xl lg:text-5xl mb-6">
            <span class="text-brand-primary uppercase">{title}</span>
          </h1>
          <p class="text-slate-700 text-base md:text-lg leading-relaxed max-w-2xl">{subtitle}</p>
        </div>
      </div>
    </section>'''

def breadcrumb_back(label, href):
    return f'''<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
      <a href="{href}" class="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-brand-primary transition-colors font-medium">
        <span>←</span> {label}
      </a>
    </div>'''

# ---- Page 1: chooser ----
def chooser_page(shell):
    can_count   = sum(len(v) for v in TREE['can'].values())
    pouch_count = sum(len(v) for v in TREE['pouch'].values())
    main = f'''<main>
    {hero_html("המבחר בישראל", "המבחר שלנו", "מגוון מוצרי הטונה שגאיה מספקת בישראל — שימורים ופאוצ׳ים במגוון גדלים וכשרויות.", "/images/products/product-tuna-saku.jpg")}
    <section class="section-padding bg-slate-50/50 border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="mb-12 text-center">
          <span class="text-xs font-bold uppercase tracking-widest text-brand-primary mb-3 block">בחירה</span>
          <h2 class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">איזה סוג אריזה?</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <a href="/catalog-can.html" class="card-b2b group bg-white border border-slate-100/60 hover:border-brand-primary/40 hover:shadow-xl transition-all duration-500 rounded-2xl overflow-hidden">
            <div class="relative aspect-[16/10] bg-brand-light overflow-hidden">
              <img src="/images/products-gaya/TUC001.png" alt="פחיות טונה" class="w-full h-full object-contain p-10 group-hover:scale-105 transition-transform duration-500" />
            </div>
            <div class="p-10 text-center">
              <h3 class="text-3xl font-bold text-slate-900 mb-2 group-hover:text-brand-primary transition-colors">פחיות</h3>
              <p class="text-slate-500 mb-6">{can_count} מוצרים</p>
              <span class="inline-block bg-brand-primary text-white px-8 py-3 rounded-full text-sm font-bold uppercase tracking-widest group-hover:bg-brand-dark transition-colors">לצפייה</span>
            </div>
          </a>
          <a href="/catalog-pouch.html" class="card-b2b group bg-white border border-slate-100/60 hover:border-brand-primary/40 hover:shadow-xl transition-all duration-500 rounded-2xl overflow-hidden">
            <div class="relative aspect-[16/10] bg-brand-light overflow-hidden">
              <img src="/images/products-gaya/TUP009.png" alt="פאוצ׳ים" class="w-full h-full object-contain p-10 group-hover:scale-105 transition-transform duration-500" />
            </div>
            <div class="p-10 text-center">
              <h3 class="text-3xl font-bold text-slate-900 mb-2 group-hover:text-brand-primary transition-colors">פאוצ׳ים</h3>
              <p class="text-slate-500 mb-6">{pouch_count} מוצרים</p>
              <span class="inline-block bg-brand-primary text-white px-8 py-3 rounded-full text-sm font-bold uppercase tracking-widest group-hover:bg-brand-dark transition-colors">לצפייה</span>
            </div>
          </a>
        </div>
      </div>
    </section>
  </main>'''
    html = re.sub(r'<main[^>]*>.*?</main>', main, shell, count=1, flags=re.DOTALL)
    html = re.sub(r'<title>[^<]*</title>', '<title>המבחר שלנו | TUNA VIETNAM</title>', html, count=1)
    html = re.sub(r'<meta name="description" content="[^"]*"',
                  '<meta name="description" content="המבחר של גאיה — פחיות ופאוצ׳ים של טונה בכשרויות בית יוסף, לנדא/גלאט ועדה חרדית."', html, count=1)
    return html

# ---- Page 2/3: type-specific ----
def type_page(shell, type_key, title, kicker, hero_img):
    kosher_order = ['בית יוסף','לנדא / גלאט','עדה חרדית']
    sections = []
    bgs = ['bg-slate-50/50 border-y border-slate-100','bg-white','bg-slate-50/50 border-y border-slate-100']
    for i, k in enumerate(kosher_order):
        sections.append(section_html(k, TREE[type_key][k], bgs[i]))
    total = sum(len(TREE[type_key][k]) for k in kosher_order)
    subtitle = f'{total} מוצרים במגוון גדלים וכשרויות.'
    main = f'''<main>
    {hero_html(kicker, title, subtitle, hero_img)}
    {breadcrumb_back("חזרה למבחר", "/catalog.html")}
    {''.join(sections)}
  </main>'''
    html = re.sub(r'<main[^>]*>.*?</main>', main, shell, count=1, flags=re.DOTALL)
    html = re.sub(r'<title>[^<]*</title>', f'<title>{title} | TUNA VIETNAM</title>', html, count=1)
    html = re.sub(r'<meta name="description" content="[^"]*"',
                  f'<meta name="description" content="{title} של גאיה — {total} מוצרים בכשרויות בית יוסף, לנדא ועדה חרדית."', html, count=1)
    return html

def add_nav_item():
    nav_tpl = '<a class="text-[13px] font-bold font-display uppercase tracking-widest transition-all duration-300 whitespace-nowrap relative py-2 group {klass}" href="/catalog.html">המבחר<span class="absolute bottom-0 left-0 h-0.5 bg-brand-primary transition-all duration-300 {span_w}"></span></a>'
    NAV_INACTIVE = nav_tpl.format(klass='text-slate-500 hover:text-brand-primary', span_w='w-0 group-hover:w-full')
    NAV_ACTIVE   = nav_tpl.format(klass='text-brand-primary', span_w='w-full')

    pages = ('index.html','products.html','about.html','processing.html','sustainability.html',
             'certifications.html','contact.html','catalog.html','catalog-can.html','catalog-pouch.html')
    for fname in pages:
        path = os.path.join(SITE, fname)
        if not os.path.exists(path): continue
        with open(path) as f: html = f.read()
        is_catalog = fname.startswith('catalog')
        # If already has המבחר link, remove and re-insert (idempotent)
        html = re.sub(r'<a[^>]*href="/catalog[^"]*\.html"[^>]*>המבחר[^<]*(?:<span[^>]*>[^<]*</span>)?</a>', '', html)
        pat = re.compile(r'(<a[^>]*href="/products\.html"[^>]*>[^<]*(?:<span[^>]*>[^<]*</span>)?</a>)')
        new_link = NAV_ACTIVE if is_catalog else NAV_INACTIVE
        html, _ = pat.subn(lambda m: m.group(1) + new_link, html, count=1)
        with open(path,'w') as f: f.write(html)
        print(f'  nav injected: {fname}')

def build_all():
    with open(os.path.join(SITE,'products.html')) as f: shell = f.read()
    # Chooser
    with open(os.path.join(SITE,'catalog.html'),'w') as f: f.write(chooser_page(shell))
    print(f'  catalog.html         ({sum(len(v) for v in TREE["can"].values()) + sum(len(v) for v in TREE["pouch"].values())} products total)')
    # Cans
    with open(os.path.join(SITE,'catalog-can.html'),'w') as f: f.write(type_page(shell, 'can', 'פחיות', 'המבחר', '/images/products/product-precook.jpg'))
    print(f'  catalog-can.html     ({sum(len(v) for v in TREE["can"].values())} products)')
    # Pouches
    with open(os.path.join(SITE,'catalog-pouch.html'),'w') as f: f.write(type_page(shell, 'pouch', 'פאוצ׳ים', 'המבחר', '/images/products/product-tuna-saku.jpg'))
    print(f'  catalog-pouch.html   ({sum(len(v) for v in TREE["pouch"].values())} products)')

if __name__ == '__main__':
    build_all()
    add_nav_item()
