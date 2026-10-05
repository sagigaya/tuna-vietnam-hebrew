#!/usr/bin/env python3
"""Inject a floating WhatsApp CTA button into every HTML page.
Clicking opens wa.me/972545650111 (Ohad — primary contact for Israeli leads).
"""
import os, re

SITE = os.path.join(os.path.dirname(__file__), 'site')

WHATSAPP_HTML = '''
<!-- Floating WhatsApp CTA (Ohad — +972 54-565-0111) -->
<a href="https://wa.me/972545650111?text=%D7%94%D7%99%D7%99%20%D7%A8%D7%90%D7%99%D7%AA%D7%99%20%D7%90%D7%AA%20%D7%94%D7%A7%D7%98%D7%9C%D7%95%D7%92%20%D7%95%D7%90%D7%A9%D7%9E%D7%97%20%D7%9C%D7%A7%D7%91%D7%9C%20%D7%A4%D7%A8%D7%98%D7%99%D7%9D"
   target="_blank" rel="noopener"
   aria-label="שליחת ווטסאפ"
   style="position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;align-items:center;gap:10px;background:#25D366;color:#fff;padding:14px 20px;border-radius:9999px;box-shadow:0 8px 24px rgba(37,211,102,0.35),0 2px 8px rgba(0,0,0,0.1);font-family:Heebo,sans-serif;font-weight:700;font-size:15px;text-decoration:none;transition:transform .2s ease,box-shadow .2s ease;"
   onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 12px 32px rgba(37,211,102,0.5),0 4px 12px rgba(0,0,0,0.15)'"
   onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 8px 24px rgba(37,211,102,0.35),0 2px 8px rgba(0,0,0,0.1)'">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.966-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
  <span>ווטסאפ</span>
</a>
<!-- /Floating WhatsApp CTA -->
'''

def inject_all():
    for f in os.listdir(SITE):
        if not f.endswith('.html'): continue
        path = os.path.join(SITE, f)
        with open(path) as fh: html = fh.read()
        # Remove any existing WhatsApp CTA (idempotent)
        html = re.sub(r'\n?<!-- Floating WhatsApp CTA[^>]*-->.*?<!-- /Floating WhatsApp CTA -->\n?', '\n', html, flags=re.DOTALL)
        # Inject before </body>
        if '</body>' in html:
            html = html.replace('</body>', WHATSAPP_HTML + '</body>', 1)
        with open(path,'w') as fh: fh.write(html)
        print(f'  injected: {f}')

if __name__ == '__main__':
    inject_all()
