import streamlit as st

from app import checks, labels, rights  # noqa: F401 (labels fills TEXT)
from app.i18n import TEXT

# Only constants and engine-computed values go through unsafe_allow_html, never user text
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Telugu:wght@400;600;700&display=swap');
:root { --primary: #1f2f7a; --primary-dark: #141f57; --accent: #0b6fb8; --saffron: #ff9933; --green: #0f6b06; --danger: #a4161a; --line: #d8deea; --ink: #111a33; --muted: #4a5468; --page: #f5f7fb; --tint: #eef1fb; }
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp li { font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Telugu', sans-serif; }
.stApp { background: var(--page); }
.stMain { overflow-x: clip; }
.block-container { padding-top: 0 !important; max-width: 1080px; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.wp-bleed { margin-left: calc(50% - 50vw); margin-right: calc(50% - 50vw); padding-left: calc(50vw - 50%); padding-right: calc(50vw - 50%); }
.wp-bar { margin-top: -16px; background: var(--primary-dark); color: #fff; font-size: .86rem; padding-top: 8px; padding-bottom: 8px; border-bottom: 3px solid var(--saffron); display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 20px; }
.wp-bar a { color: #fff !important; text-decoration: underline; }
.wp-brand { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px 20px; padding: 10px 0 14px; }
.wp-name { font-size: 1.9rem; font-weight: 700; color: var(--primary); line-height: 1.1; }
.wp-name span { font-size: 1rem; font-weight: 600; color: var(--muted); margin-left: 8px; }
.wp-tagline { color: var(--muted); font-size: .92rem; }
a.wp-call { display: inline-flex; align-items: center; min-height: 44px; padding: 8px 16px; border-radius: 8px; background: var(--danger); color: #fff !important; font-weight: 700; text-decoration: none; }
.wp-hero { display: grid; grid-template-columns: 1.15fr 1fr; gap: 28px; align-items: center; background: var(--primary); border-radius: 16px; padding: 36px 32px; margin: 12px 0 20px; }
.wp-hero h1 { color: #fff !important; font-size: 2.3rem; line-height: 1.2; font-weight: 700; padding: 0 0 12px; margin: 0; font-family: inherit !important; }
[data-testid="stHeaderActionElements"] { display: none; }
.wp-hero p { color: #e6eafa; font-size: 1.05rem; line-height: 1.6; margin: 0 0 20px; }
a.wp-cta { display: inline-flex; align-items: center; min-height: 48px; padding: 10px 22px; background: #fff; color: var(--primary) !important; font-weight: 700; text-decoration: none; border-radius: 8px; transition: background-color .2s; }
a.wp-cta:hover { background: #ffe9cc; }
*:focus-visible { outline: 3px solid var(--accent) !important; outline-offset: 2px; }
.wp-hero a:focus-visible { outline-color: var(--saffron) !important; }
.wp-case { background: #fff; border-radius: 12px; padding: 16px; color: var(--ink); }
.wp-case-title { font-weight: 700; color: var(--primary); font-size: 1rem; margin-bottom: 10px; }
.wp-tag { display: inline-block; margin-left: 6px; padding: 0 8px; border-radius: 10px; background: #fff3e0; border: 1px solid var(--saffron); color: var(--ink); font-size: .76rem; font-weight: 700; }
.wp-row { display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border: 1px solid var(--line); border-left-width: 5px; border-radius: 6px; margin-bottom: 8px; font-size: .92rem; background: #fff; color: var(--ink); animation: wp-in .4s ease-out both; }
.wp-row b { font-weight: 600; }
.wp-row em { font-style: normal; font-weight: 700; white-space: nowrap; }
.wp-row.ok { border-left-color: var(--green); } .wp-row.ok em { color: var(--green); }
.wp-row.bad { border-left-color: var(--danger); background: #fff5f5; } .wp-row.bad em { color: var(--danger); }
.wp-row.info { border-left-color: var(--primary); } .wp-row.info em { color: var(--primary); }
.wp-row:nth-child(2) { animation-delay: .25s; } .wp-row:nth-child(3) { animation-delay: .5s; } .wp-row:nth-child(4) { animation-delay: .75s; }
.wp-verdict { padding: 10px 12px; background: var(--danger); color: #fff; border-radius: 6px; font-weight: 700; font-size: .95rem; animation: wp-in .4s ease-out .9s both; }
.wp-human { margin-top: 10px; color: var(--muted); font-size: .86rem; font-weight: 600; }
@keyframes wp-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.wp-section { color: var(--ink); font-size: 1.35rem; font-weight: 700; margin: 26px 0 12px; scroll-margin-top: 16px; }
.wp-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
a.wp-card { display: block; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 16px; text-decoration: none; transition: border-color .2s; }
a.wp-card:hover { border-color: var(--primary); }
.wp-card b { display: block; color: var(--primary); font-size: 1rem; margin-bottom: 4px; }
.wp-card span { color: var(--muted); font-size: .9rem; line-height: 1.4; }
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
@media (max-width: 820px) { .wp-hero { grid-template-columns: 1fr; padding: 24px 18px; } .wp-hero h1 { font-size: 1.8rem; } .wp-cards { grid-template-columns: 1fr 1fr; } .wp-stats { grid-template-columns: 1fr; } }
@media (max-width: 480px) { .wp-cards { grid-template-columns: 1fr; } .wp-name { font-size: 1.6rem; } .wp-table { font-size: .86rem; } }
</style>
"""
SIZES = {"A−": "14px", "A": "16px", "A+": "19px"}


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def page_style():
    html(CSS)


def top_bar(language):
    html(f"""<div class="wp-bar wp-bleed"><span>{TEXT['bar'][language]}</span><a href="#main">{TEXT['skip'][language]}</a></div>""")


def text_size(choice):
    html(f"<style>html {{ font-size: {SIZES.get(choice, '16px')}; }}</style>")


def brand(language):
    html(f"""<div class="wp-brand"><div><div class="wp-name">Wapsi <span>वापसी · వాపసీ</span></div><div class="wp-tagline">{TEXT['tagline'][language]}</div></div><a class="wp-call" href="tel:1930">{TEXT['helpline'][language]}: 1930</a></div>""")


def hero(language):
    case = rights.example_case()
    t = lambda key: TEXT[key][language]
    html(
        f"""<section class="wp-hero"><div><h1>{t('hero_title')}</h1><p>{t('hero_sub')}</p><a class="wp-cta" href="#main">{t('hero_cta')}</a></div>
<div class="wp-case"><div class="wp-case-title">{t('case_title')} <span class="wp-tag">{t('case_tag')}</span></div>
<div><div class="wp-row ok"><b>{t('bank_report')}</b><em>{t('done')}</em></div>
<div class="wp-row bad"><b>{t('police_report')}</b><em>{t('missing')}</em></div>
<div class="wp-row info"><b>{t('deadline')}</b><em>{case['deadline']:%d %b %Y}</em></div></div>
<div class="wp-verdict">Rs {case['at_risk']:,} {t('at_risk')}</div>
<div class="wp-human">{t('human')}</div></div></section>"""
    )


def section(text, anchor=None):
    attr = f' id="{anchor}"' if anchor else ""
    html(f'<div class="wp-section"{attr}>{text}</div>')


def services(language):
    cards = "".join(f"""<a class="wp-card" href="#main"><b>{TEXT[f'svc{n}'][language]}</b><span>{TEXT[f'svc{n}d'][language]}</span></a>""" for n in range(1, 5))
    html(f'<div class="wp-cards">{cards}</div>')


def footer(language):
    html(f'<div class="wp-foot wp-bleed">{TEXT["foot"][language]}</div>')


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
