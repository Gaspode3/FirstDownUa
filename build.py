#!/usr/bin/env python3
"""
Генератор сторінок «Перша вниз / First Down».

З одного шаблону (src/index.template.html) і translations.js створює:
  index.html     — українська версія, https://firstdown.org.ua/
  en/index.html  — англійська версія,  https://firstdown.org.ua/en/
  sitemap.xml, robots.txt

Що робить:
  * вставляє переклад прямо в HTML (пошуковик бачить текст без JavaScript);
  * окрема адреса для кожної мови + canonical + hreflang;
  * свій <title>, description, Open Graph для кожної мови;
  * JSON-LD (Organization + FAQPage) з тих самих питань, що видно на сторінці;
  * перемикач UA/EN стає звичайними посиланнями (/ та /en/).

Запуск (з кореня репозиторію):   python3 build.py
Потрібен лише Python 3.8+, без додаткових бібліотек.
"""
import html as htmllib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "src" / "index.template.html"
TRANSLATIONS = ROOT / "translations.js"
SITE = "https://firstdown.org.ua"

SEO_EN = {
    "title": "First Down (Перша вниз) | Adaptive motorcycle project for amputee veterans — Lviv, Ukraine",
    "description": "First Down is a habilitation motorcycle project for veterans with amputations by NGO "
                   "Motodopomoga Lviv: a safe closed track, adapted motorcycles, qualified instructors and "
                   "5 free sessions. Apply now.",
    "keywords": "First Down, First Down Ukraine, First Down UA, adaptive motorcycle, motorcycle for amputees, "
                "amputee veterans Ukraine, veteran rehabilitation, Motodopomoga Lviv, Lemberg Moto, Zgraya",
    "author": "Project 'First Down' & NGO 'Motodopomoga Lviv'",
    "og:title": "First Down | Adaptive motorcycle project for amputee veterans",
    "og:description": "Habilitation motorcycle project for veterans with amputations by NGO Motodopomoga Lviv. "
                      "Safe closed track, adapted motorcycles, free sessions.",
    "twitter:title": "First Down | Adaptive motorcycle project for amputee veterans",
    "twitter:description": "Habilitation motorcycle project for veterans with amputations by NGO Motodopomoga Lviv.",
}

# Тексти атрибутів (alt, aria-label, title), які не лежать у translations.js
EN_ATTR_REPLACEMENTS = [
    ('alt="Логотип Перша вниз"', 'alt="First Down logo"'),
    ('aria-label="Перша вниз - На головну"', 'aria-label="First Down — home"'),
    ('alt="ГО Мотодопомога Львів"', 'alt="NGO Motodopomoga Lviv"'),
    ('title="ГО Мотодопомога Львів"', 'title="NGO Motodopomoga Lviv"'),
    ('title="Перейти на сторінку ГО Мотодопомога Львів"', 'title="Go to NGO Motodopomoga Lviv"'),
    ('aria-label="Вибір мови"', 'aria-label="Language"'),
    ('aria-label="Відкрити меню"', 'aria-label="Open menu"'),
    ('aria-label="Попереднє фото"', 'aria-label="Previous photo"'),
    ('aria-label="Наступне фото"', 'aria-label="Next photo"'),
    ('aria-label="Наш Instagram"', 'aria-label="Our Instagram"'),
    ('alt="Момент проєкту"', 'alt="Project moment"'),
    ('alt="Момент проєкту Перша вниз #', 'alt="First Down project moment #'),
]

warnings = []


def warn(msg):
    warnings.append(msg)
    print("  ! " + msg)


# ---------------------------------------------------------------- переклади
def parse_translations(text):
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)  # коментарі
    starts = {}
    for lang in ("ua", "en"):
        m = re.search(r'"%s"\s*:\s*\{' % lang, text)
        if not m:
            sys.exit(f"У translations.js не знайдено блок \"{lang}\"")
        starts[lang] = m.end()
    order = sorted(starts, key=starts.get)
    result = {}
    for idx, lang in enumerate(order):
        end = starts[order[idx + 1]] if idx + 1 < len(order) else len(text)
        block = text[starts[lang]:end]
        pairs = re.findall(r'"([A-Za-z0-9_]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', block, re.S)
        result[lang] = {k: json.loads('"' + v + '"', strict=False) for k, v in pairs}
    return result


# -------------------------------------------------------- заповнення data-i18n
I18N_RE = re.compile(r'(<(\w+)\b[^>]*?\bdata-i18n="([^"]+)"[^>]*>)(\s*)(</\2>)', re.S)


def fill_i18n(page, d):
    missing = set()

    def repl(m):
        key = m.group(3)
        val = d.get(key)
        if not val:
            if key not in d:
                missing.add(key)
            return m.group(0)
        return m.group(1) + val + m.group(5)

    page = I18N_RE.sub(repl, page)
    for key in sorted(missing):
        warn(f"ключа «{key}» немає в translations.js")
    return page


# ---------------------------------------------------- «Наш шлях» (як у JS)
def render_path(d):
    total = 0
    while d.get(f"path_{total + 1:02d}_title"):
        total += 1
    out = []
    for i in range(1, total + 1):
        num = f"{i:02d}"
        title = d.get(f"path_{num}_title", "")
        desc = d.get(f"path_{num}_desc", "")
        tag = d.get(f"path_{num}_tag", "")
        even = i % 2 == 0
        last = i == total
        line = ("border-l-2 border-dashed border-brandOrange/80 h-28" if last
                else "bg-brandOrange/40 h-[calc(100%+3rem)] w-0.5")
        card = ("bg-[#0f0f0f] p-6 lg:p-8 border-2 border-brandOrange/80 hover:border-brandOrange transition-colors duration-300 rounded-sm shadow-xl relative z-10" if last
                else "bg-[#0f0f0f] p-6 lg:p-8 border border-neutral-800 hover:border-brandOrange/50 transition-colors duration-300 rounded-sm shadow-xl relative z-10")
        tag_html = (f'<span class="text-[10px] font-bold tracking-widest text-brandOrange uppercase '
                    f'bg-brandOrange/10 border border-brandOrange/30 px-2 py-0.5 rounded">{tag}</span>') if tag else ""
        out.append(f'''<div class="relative flex flex-col md:flex-row items-start {'md:flex-row-reverse' if even else ''} group mb-12">
<div class="absolute left-4 md:left-1/2 -translate-x-1/2 top-3 {line} z-0"></div>
<div class="absolute left-4 md:left-1/2 -translate-x-1/2 top-1.5 w-6 h-6 rounded-full bg-brandDark border-2 border-brandOrange flex items-center justify-center z-10 group-hover:scale-125 transition-transform duration-300"><div class="w-2 h-2 rounded-full bg-brandOrange"></div></div>
<div class="ml-12 md:ml-0 md:w-1/2 {'md:pl-12' if even else 'md:pr-12'} w-full">
<div class="{card}">
<div class="flex items-center justify-between mb-4"><span class="text-brandOrange font-black text-2xl tracking-wider md:hidden">{num}</span>{tag_html}</div>
<h3 class="text-white font-bold tracking-wider text-xl mb-3 uppercase md:hidden" data-i18n="path_{num}_title">{title}</h3>
<p class="text-textGray leading-relaxed text-sm lg:text-base font-normal" data-i18n="path_{num}_desc">{desc}</p>
</div></div>
<div class="hidden md:flex md:w-1/2 {'md:pr-12 justify-end text-right' if even else 'md:pl-12 justify-start text-left'} items-center self-center"><div class="space-y-1"><span class="text-brandOrange/80 font-black text-4xl lg:text-5xl tracking-tight block">{num}</span><h3 class="text-white font-black tracking-wider text-xl lg:text-2xl uppercase leading-snug" data-i18n="path_{num}_title">{title}</h3></div></div>
</div>''')
    return "\n".join(out)


# ---------------------------------------------------------------- JSON-LD
def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def build_jsonld(lang, d):
    ua = lang == "ua"
    url = f"{SITE}/" if ua else f"{SITE}/en/"
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Перша вниз" if ua else "First Down",
        "alternateName": ["First Down", "ГО Мотодопомога Львів"] if ua
        else ["Перша вниз", "NGO Motodopomoga Lviv"],
        "url": url,
        "logo": f"{SITE}/logo-small.png",
        "description": ("Абілітаційний мотопроєкт для ветеранів з ампутаціями від ГО Мотодопомога Львів." if ua
                        else "Habilitation motorcycle project for veterans with amputations by NGO Motodopomoga Lviv."),
        "address": {"@type": "PostalAddress", "addressLocality": "Львів" if ua else "Lviv", "addressCountry": "UA"},
        "sameAs": [
            "https://www.instagram.com/first.down.ua",
            "https://facebook.com/motodopomoga",
            "https://www.motodopomoga.lviv.ua",
        ],
    }
    questions = []
    n = 1
    while d.get(f"faq_q{n}") and d.get(f"faq_a{n}"):
        questions.append({
            "@type": "Question",
            "name": strip_tags(d[f"faq_q{n}"]),
            "acceptedAnswer": {"@type": "Answer", "text": strip_tags(d[f"faq_a{n}"])},
        })
        n += 1
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "inLanguage": "uk" if ua else "en", "mainEntity": questions}
    body = json.dumps([org, faq], ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{body}\n</script>'


# ------------------------------------------------------------------ <head>
def set_meta(page, key, content):
    pat = re.compile(r'(<meta\s+(?:name|property)="%s"\s+content=")[^"]*(")' % re.escape(key), re.S)
    new, n = pat.subn(lambda m: m.group(1) + htmllib.escape(content, quote=True) + m.group(2), page)
    if n == 0:
        warn(f"у шаблоні немає мета-тега «{key}»")
    return new


def build_page(template, lang, tr):
    d = tr[lang]
    ua = lang == "ua"
    page = template
    url = f"{SITE}/" if ua else f"{SITE}/en/"

    # <html lang>
    page, n = re.subn(r'<html\s+lang="[^"]*"', f'<html lang="{"uk" if ua else "en"}"', page, count=1)
    if not n:
        warn("не знайдено <html lang=...>")

    # атрибути та alt англійською
    if not ua:
        for old, new in EN_ATTR_REPLACEMENTS:
            page = page.replace(old, new)
        for k in (1, 2, 3):
            name_ua, name_en = tr["ua"].get(f"team_{k}_title"), d.get(f"team_{k}_title")
            if name_ua and name_en:
                page = page.replace(name_ua, name_en)

    # переклад у HTML
    page = fill_i18n(page, d)

    # порожній абзац (about_p2 без тексту) прибираємо, щоб не було зайвого відступу
    page = re.sub(r'[ \t]*<p data-i18n="about_p2"></p>\n?', '', page)

    # «Наш шлях»
    page, n = re.subn(r'(<div id="path-container"[^>]*>)\s*(</div>)',
                      lambda m: m.group(1) + "\n" + render_path(d) + "\n" + m.group(2), page, count=1)
    if not n:
        warn("не знайдено порожній #path-container (можливо, вже заповнений)")

    # title / meta (для української лишаємо як у шаблоні)
    if not ua:
        page, n = re.subn(r"<title>.*?</title>",
                          lambda m: "<title>" + htmllib.escape(SEO_EN["title"], quote=False) + "</title>",
                          page, count=1, flags=re.S)
        if not n:
            warn("не знайдено <title>")
        for key in ("description", "keywords", "author", "og:title", "og:description",
                    "twitter:title", "twitter:description"):
            page = set_meta(page, key, SEO_EN[key])
        page = set_meta(page, "og:url", url)

    # canonical + hreflang + og:locale
    block = (f'<link rel="canonical" href="{url}">\n'
             f'<link rel="alternate" hreflang="uk" href="{SITE}/">\n'
             f'<link rel="alternate" hreflang="en" href="{SITE}/en/">\n'
             f'<link rel="alternate" hreflang="x-default" href="{SITE}/">\n'
             f'<meta property="og:locale" content="{"uk_UA" if ua else "en_US"}">\n'
             f'<meta property="og:locale:alternate" content="{"en_US" if ua else "uk_UA"}">')
    page, n = re.subn(r'<link rel="canonical" href="[^"]*">', lambda m: block, page, count=1)
    if not n:
        warn("не знайдено <link rel=\"canonical\">")

    # JSON-LD
    page, n = re.subn(r'<script type="application/ld\+json">.*?</script>',
                      lambda m: build_jsonld(lang, d), page, count=1, flags=re.S)
    if not n:
        warn("не знайдено блок JSON-LD")

    # перемикач мов: кнопки -> посилання
    ua_cls = "lang-active" if ua else "lang-inactive"
    en_cls = "lang-inactive" if ua else "lang-active"
    ua_label = "Українська" if ua else "Switch to Ukrainian"
    en_label = "Switch to English" if ua else "English"
    page, n1 = re.subn(r'<button id="btn-ua"[^>]*>UA</button>',
                       lambda m: f'<a id="btn-ua" href="/" hreflang="uk" lang="uk" class="{ua_cls}" aria-label="{ua_label}">UA</a>',
                       page, count=1)
    page, n2 = re.subn(r'<button id="btn-en"[^>]*>EN</button>',
                       lambda m: f'<a id="btn-en" href="/en/" hreflang="en" lang="en" class="{en_cls}" aria-label="{en_label}">EN</a>',
                       page, count=1)
    if not (n1 and n2):
        warn("не знайдено кнопки перемикача мови #btn-ua / #btn-en")

    # мова фіксована для сторінки (не залежить від localStorage)
    old_line = "let currentLang = localStorage.getItem('firstDownLang') || 'ua';"
    if old_line in page:
        page = page.replace(old_line, f"let currentLang = '{lang}'; // мова визначається адресою сторінки (build.py)")
    else:
        warn("не знайдено рядок «let currentLang = localStorage...» у скрипті")

    # англійська сторінка лежить у /en/ — шляхи до файлів роблю від кореня
    if not ua:
        page = re.sub(r'''(["'`(])gallery/''', r"\1/gallery/", page)
        page = re.sub(r'(\bsrc=")(?!https?://|/|data:|#|\$|")', r"\1/", page)
        page = page.replace('href="logo.png"', 'href="/logo.png"')

    # залишились порожні елементи?
    left = re.findall(r'<(\w+)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>\s*</\1>', page, re.S)
    left = sorted({k for _, k in left if k not in ("about_p2",)})
    if left:
        warn(f"[{lang}] порожні після збірки: {', '.join(left)}")
    return page


def build_sitemap():
    today = date.today().isoformat()
    def entry(loc):
        return (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n"
                f'    <xhtml:link rel="alternate" hreflang="uk" href="{SITE}/"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/en/"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>\n  </url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + entry(f"{SITE}/") + "\n" + entry(f"{SITE}/en/") + "\n</urlset>\n")


def main():
    if not TEMPLATE.exists():
        sys.exit(f"Немає шаблону {TEMPLATE}.\n"
                 f"Спершу перенесіть поточний index.html:  mkdir src && git mv index.html src/index.template.html")
    tr = parse_translations(TRANSLATIONS.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")

    only_ua = set(tr["ua"]) - set(tr["en"])
    only_en = set(tr["en"]) - set(tr["ua"])
    if only_ua:
        warn("ключі є лише в UA: " + ", ".join(sorted(only_ua)))
    if only_en:
        warn("ключі є лише в EN: " + ", ".join(sorted(only_en)))

    print("Збираю українську версію…")
    (ROOT / "index.html").write_text(build_page(template, "ua", tr), encoding="utf-8")
    print("Збираю англійську версію…")
    (ROOT / "en").mkdir(exist_ok=True)
    (ROOT / "en" / "index.html").write_text(build_page(template, "en", tr), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nDisallow: /src/\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    print("\nГотово: index.html, en/index.html, sitemap.xml, robots.txt")
    if warnings:
        print(f"Попереджень: {len(warnings)} — перегляньте вище.")


if __name__ == "__main__":
    main()
