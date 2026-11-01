import streamlit as st

from app import checks, labels, rights  # noqa: F401 (labels fills TEXT)
from app.i18n import TEXT

# Only constants and engine-computed values go through unsafe_allow_html, never user text
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Telugu:wght@400;600;700&display=swap');
:root { --primary: #12326e; --primary-dark: #0b2352; --accent: #0b6fb8; --saffron: #ff9933; --green: #0f6b06; --danger: #a4161a; --line: #d8deea; --ink: #111a33; --muted: #4a5468; --page: #ffffff; --tint: #eef3fb; }
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp li { font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Telugu', sans-serif; }
.stApp { background: var(--page); }
iframe[title="streamlit.components.v1.html"], [data-testid="stIFrame"] { border-radius: 18px; }
[data-testid="stCustomComponentV1"], .stElementContainer:has(iframe) { border-radius: 18px; overflow: hidden; }
.stMain { overflow-x: clip; }
.block-container { padding-top: 0 !important; max-width: 1080px; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.wp-bleed { margin-left: calc(50% - 50vw); margin-right: calc(50% - 50vw); padding-left: calc(50vw - 50%); padding-right: calc(50vw - 50%); }
.wp-bar { margin-top: -16px; background: var(--primary-dark); color: #fff; font-size: .86rem; padding-top: 8px; padding-bottom: 8px; border-bottom: 3px solid var(--saffron); display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 20px; }
.wp-bar a { color: #fff !important; text-decoration: underline; }
.wp-brand { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px 20px; padding: 10px 0 14px; }
.wp-name { font-size: 1.9rem; font-weight: 700; color: var(--primary); line-height: 1.1; }
.wp-name span { font-size: 1rem; font-weight: 600; color: var(--muted); margin-left: 8px; }
a.wp-call { display: inline-flex; align-items: center; min-height: 44px; padding: 8px 16px; border-radius: 8px; background: var(--danger); color: #fff !important; font-weight: 700; text-decoration: none; }
[data-testid="stHeaderActionElements"] { display: none; }
*:focus-visible { outline: 3px solid var(--accent) !important; outline-offset: 2px; }
.wp-row { display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border: 1px solid var(--line); border-left-width: 5px; border-radius: 6px; margin-bottom: 8px; font-size: .92rem; background: #fff; color: var(--ink); animation: wp-in .4s ease-out both; }
.wp-row b { font-weight: 600; }
.wp-row em { font-style: normal; font-weight: 700; white-space: nowrap; }
.wp-row.ok { border-left-color: var(--green); } .wp-row.ok em { color: var(--green); }
.wp-row.bad { border-left-color: var(--danger); background: #fff5f5; } .wp-row.bad em { color: var(--danger); }
.wp-row.info { border-left-color: var(--primary); } .wp-row.info em { color: var(--primary); }
.wp-row:nth-child(2) { animation-delay: .25s; } .wp-row:nth-child(3) { animation-delay: .5s; } .wp-row:nth-child(4) { animation-delay: .75s; }
@keyframes wp-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.wp-section { color: var(--ink); font-size: 1.35rem; font-weight: 700; margin: 26px 0 12px; scroll-margin-top: 16px; }
.wp-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.wp-stat { background: var(--tint); border-radius: 12px; padding: 14px 16px; }
.wp-stat b { display: block; font-size: 1.6rem; color: var(--primary); }
.wp-stat small { color: var(--muted); font-size: .9rem; line-height: 1.4; display: block; }
.wp-table { width: 100%; border-collapse: separate; border-spacing: 0; background: #fff; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; font-size: .95rem; }
.wp-table th { background: var(--tint); color: var(--ink); text-align: left; padding: 10px 12px; font-weight: 700; border: none; }
.wp-table td { border: none; border-top: 1px solid var(--line); padding: 10px 12px; color: var(--ink); }
.wp-amount { font-weight: 700; white-space: nowrap; }
.wp-table td.wp-lost { color: var(--danger); }
.wp-table td.wp-kept { color: var(--green); }
.wp-group { font-weight: 700; color: var(--primary); margin: 6px 0 2px; }
.wp-foot { margin-top: 36px; padding-top: 18px; padding-bottom: 18px; background: var(--primary-dark); color: #e6eafa; font-size: .88rem; line-height: 1.6; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 4px; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { padding: 8px 14px !important; min-height: 44px; border-radius: 8px; color: var(--primary); font-weight: 600; }
.stTabs [aria-selected="true"] { background: var(--primary) !important; color: #fff !important; }
.stTabs [aria-selected="true"] p { color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stApp button, .stLinkButton a { min-height: 44px !important; cursor: pointer; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted) !important; opacity: 1 !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] strong { color: var(--ink) !important; }
[data-testid="stAlert"] > div { border-left: 5px solid var(--danger); border-radius: 8px; }
.stFormSubmitButton button, .stDownloadButton button, .stLinkButton a { background: var(--primary) !important; color: #fff !important; border-radius: 8px !important; font-weight: 600; }
.stFormSubmitButton button p, .stDownloadButton button p, .stLinkButton a p { color: #fff !important; }
[data-testid="stForm"] { border: 1px solid var(--line); border-radius: 12px; background: #fff; padding: 20px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
@media (max-width: 820px) { .wp-stats { grid-template-columns: 1fr; } }
@media (max-width: 480px) { .wp-name { font-size: 1.6rem; } .wp-table { font-size: .86rem; } }
.st-key-wizard { background: #fff; border: 1px solid var(--line); border-top: 5px solid var(--primary); border-radius: 4px; padding: 24px clamp(14px, 3vw, 32px) !important; margin-top: 10px; }
.wp-q { color: var(--ink) !important; font-size: clamp(1.4rem, 3.4vw, 2rem) !important; line-height: 1.25 !important; font-weight: 700 !important; padding: 8px 0 12px !important; font-family: inherit !important; }
.st-key-wizard button { min-height: 64px !important; border-radius: 6px !important; }
.st-key-wizard button p { font-size: 1.1rem !important; font-weight: 700 !important; }
.st-key-wizard input { font-size: 1.5rem !important; min-height: 56px; }
.wp-progress { display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: .9rem; }
.wp-progress i { width: 34px; height: 6px; border-radius: 3px; background: var(--line); }
.wp-progress i.on { background: var(--saffron); }
.wp-progress span { margin-left: 6px; }
a.wp-big { display: flex; align-items: center; justify-content: center; min-height: 64px; margin: 10px 0; padding: 12px; background: var(--danger); color: #fff !important; font-size: 1.25rem; font-weight: 700; border-radius: 6px; text-decoration: none; }
.wp-bar { border-bottom: none; }
.wp-flagline { height: 5px; background: linear-gradient(90deg, var(--saffron) 0 33.3%, #fff 33.3% 66.6%, #138808 66.6%); }
.wp-brand { border-bottom: 1px solid var(--line); }
.wp-mark { width: 56px; height: 56px; flex: none; border: 3px solid var(--primary); border-radius: 8px; color: var(--primary); font-weight: 700; font-size: 1.7rem; display: flex; align-items: center; justify-content: center; }
.wp-id { display: flex; align-items: center; gap: 12px; }
.wp-hi { color: var(--primary); font-size: 1.05rem; font-weight: 700; }
.wp-nav { background: var(--primary); display: flex; flex-wrap: wrap; gap: 0; }
.wp-nav a { color: #fff !important; text-decoration: none; font-weight: 600; font-size: .94rem; padding: 12px 14px; min-height: 44px; }
.wp-nav a:hover { background: var(--primary-dark); text-decoration: underline; }
.wp-notice { display: flex; gap: 10px; align-items: baseline; background: #fff8ec; border-bottom: 1px solid #f2d9ad; font-size: .92rem; padding-top: 8px; padding-bottom: 8px; color: var(--ink); }
.wp-notice b { background: var(--danger); color: #fff; padding: 1px 8px; border-radius: 3px; white-space: nowrap; font-size: .82rem; }
.wp-section { color: var(--primary); font-size: 1.15rem; padding: 8px 12px; background: var(--tint); border-left: 5px solid var(--primary); }
.wp-table, [data-testid="stForm"], .wp-stat { border-radius: 4px; }
.wp-table th { background: var(--primary); color: #fff; }
.stTabs [data-baseweb="tab-list"] { border-radius: 4px; background: var(--tint); }
.stTabs [data-baseweb="tab"] { border-radius: 3px; }
.stFormSubmitButton button, .stDownloadButton button, .stLinkButton a { border-radius: 4px !important; }
iframe { border: 1px solid var(--line) !important; border-radius: 4px; }
.wp-foot { border-top: 5px solid #138808; padding-top: 20px; }
.wp-foot-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 12px; }
.wp-foot b { display: block; color: #fff; margin-bottom: 4px; }
.wp-foot a { color: #fff !important; display: block; padding: 3px 0; }
.wp-foot-note { border-top: 1px solid #3a5a96; padding-top: 10px; }
@media (max-width: 640px) { .wp-foot-grid { grid-template-columns: 1fr; } .wp-mark { width: 46px; height: 46px; font-size: 1.4rem; } .wp-nav a { padding: 11px 10px; font-size: .88rem; } }
</style>
"""
SIZES = {"A−": "14px", "A": "16px", "A+": "19px"}


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def page_style():
    html(CSS)


def top_bar(language):
    html(f"""<div class="wp-bar wp-bleed"><span>{TEXT['bar'][language]}</span><a href="#main">{TEXT['skip'][language]}</a></div><div class="wp-flagline wp-bleed"></div>""")


def text_size(choice):
    html(f"<style>html {{ font-size: {SIZES.get(choice, '16px')}; }}</style>")


def brand(language):
    t = lambda key: TEXT[key][language]
    html(
        f"""<div class="wp-brand"><div class="wp-id"><div class="wp-mark" aria-hidden="true">W</div><div><div class="wp-hi">वापसी · వాపసీ</div><div class="wp-name">Wapsi</div><div class="wp-tagline">{t('tagline')}</div></div></div><a class="wp-call" href="tel:1930">{t('helpline')}: 1930</a></div>
<nav class="wp-nav wp-bleed" aria-label="Main"><a href="#top">{t('nav_home')}</a><a href="#main">{t('more_help')}</a><a href="https://cybercrime.gov.in/" target="_blank" rel="noopener">{t('nav_ncrp')}</a><a href="https://cms.rbi.org.in/" target="_blank" rel="noopener">{t('nav_rbi')}</a></nav>
<div class="wp-notice wp-bleed" id="top"><b>{t('notice_label')}</b><span>{t('notice')}</span></div>"""
    )


def section(text, anchor=None):
    attr = f' id="{anchor}"' if anchor else ""
    html(f'<div class="wp-section"{attr}>{text}</div>')


def footer(language, checked_at):
    t = lambda key: TEXT[key][language]
    repo = "https://github.com/aadityaa0523/wapsi"
    html(
        f"""<footer class="wp-foot wp-bleed"><div class="wp-foot-grid">
<div><b>{t('foot_official')}</b><a href="tel:1930">{t('helpline')} 1930</a><a href="https://cybercrime.gov.in/" target="_blank" rel="noopener">cybercrime.gov.in</a><a href="https://cms.rbi.org.in/" target="_blank" rel="noopener">cms.rbi.org.in</a></div>
<div><b>{t('foot_about')}</b><a href="{repo}/blob/main/SECURITY.md" target="_blank" rel="noopener">{t('foot_security')}</a><a href="{repo}" target="_blank" rel="noopener">{t('foot_code')}</a></div>
<div><b>{t('foot_checked')}</b><span>{checked_at}</span></div>
</div><div class="wp-foot-note">{t('foot')}</div></footer>"""
    )


def stats(status):
    expected = sum(1 for source in checks.SOURCES if "clause" in source)
    found = sum(1 for source in status["sources"] if source.get("clause_verified"))
    reachable = sum(1 for source in status["sources"] if source["reachable"])
    html(
        f"""<div class="wp-stats">
<div class="wp-stat"><b>{rights.REPORT_DAYS} days</b><small>to file both, from the date of the fraud</small></div>
<div class="wp-stat"><b>{found} of {expected}</b><small>rule clauses found on RBI's site in the latest live check</small></div>
<div class="wp-stat"><b>{reachable} of {len(status['sources'])}</b><small>official source checks reachable just now</small></div>
</div>"""
    )


def two_report_table():
    rows = "".join(
        f"<tr><td>{name}</td><td class='wp-amount {'wp-kept' if amount else 'wp-lost'}'>Rs {amount:,} {'(eligible)' if amount else '(lost)'}</td></tr>"
        for name, amount in rights.two_report_scenarios()
    )
    html(f"<table class='wp-table'><tr><th>Same Rs {rights.EXAMPLE_LOSS:,} loss. What was reported?</th><th>Compensation possible</th></tr>{rows}</table>")


def report_tracker(language, deadlines, bank_report, police_report, as_of):
    t = lambda key: TEXT[key][language]
    row = lambda name, date: f"<div class='wp-row {'ok' if date else 'bad'}'><b>{name}</b><em>{f'{date:%d %b %Y}' if date else t('missing')}</em></div>"
    rows = row(t("bank_report"), bank_report) + row(t("police_report"), police_report)
    for name, deadline in deadlines.items():
        left = (deadline - as_of).days
        rows += f"<div class='wp-row info'><b>{name}</b><em>{deadline:%d %b %Y} ({left} days left)</em></div>"
    html(f"<div>{rows}</div>")
