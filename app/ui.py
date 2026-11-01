import streamlit as st

from app import checks, rights
from app.i18n import TEXT

# Only constants and engine-computed values go through unsafe_allow_html, never user text
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Noto+Serif:wght@700&family=Noto+Serif+Devanagari:wght@700&family=Noto+Serif+Telugu:wght@700&family=Noto+Sans+Devanagari:wght@400;600&family=Noto+Sans+Telugu:wght@400;600&display=swap');
:root { --navy: #0f2a5c; --accent: #0369a1; --saffron: #ff9933; --green: #0f6b06; --danger: #a4161a; --line: #cbd5e1; --ink: #0f172a; --muted: #475569; --pale: #f1f5f9; }
html, body, [class*="css"], .stApp { font-family: 'Atkinson Hyperlegible', 'Noto Sans Devanagari', 'Noto Sans Telugu', sans-serif; font-size: 16px; }
.stApp { background: #ffffff; }
.block-container { padding-top: 0 !important; max-width: 980px; }
header[data-testid="stHeader"] { background: transparent; }
.wp-flag { position: fixed; top: 0; left: 0; right: 0; height: 6px; z-index: 999999; background: linear-gradient(90deg, var(--saffron) 0 33.3%, #ffffff 33.3% 66.6%, var(--green) 66.6%); }
.wp-head { display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: center; justify-content: space-between; padding: 44px 0 14px; border-bottom: 3px solid var(--navy); margin-bottom: 14px; }
.wp-name { font-size: 2rem; font-weight: 700; color: var(--navy); line-height: 1.15; }
.wp-name span { font-size: 1.05rem; font-weight: 600; color: var(--muted); margin-left: 8px; }
.wp-sub { color: var(--ink); font-size: .98rem; margin-top: 2px; }
.wp-help { background: var(--navy); color: #fff; padding: 8px 14px; border-radius: 4px; font-weight: 700; white-space: nowrap; }
.wp-help a { color: #fff; text-decoration: underline; }
.wp-hero { background: linear-gradient(180deg, #ffffff 0%, #fdf6ea 70%, #f9ead2 100%); padding: 40px 28px 34px; margin: 12px 0 8px; text-align: center; border: 1px solid #f0e2c8; border-radius: 8px; }
.wp-hero h1 { color: var(--navy) !important; font-family: 'Noto Serif', 'Noto Serif Devanagari', 'Noto Serif Telugu', serif !important; font-size: 2.6rem; line-height: 1.2; font-weight: 700; padding: 0 0 14px; margin: 0 auto; max-width: 42rem; }
.wp-hero p { color: var(--ink); font-size: 1.1rem; line-height: 1.6; margin: 0 auto 22px; max-width: 40rem; }
a.wp-cta { display: inline-flex; align-items: center; min-height: 48px; padding: 10px 22px; background: var(--navy); color: #fff !important; font-weight: 700; font-size: 1.05rem; text-decoration: none; border-radius: 4px; transition: background-color .2s; }
a.wp-cta:hover { background: var(--accent); }
*:focus-visible { outline: 3px solid var(--accent) !important; outline-offset: 2px; }
.wp-case { border: 1px solid var(--line); border-radius: 8px; padding: 18px; background: #fff; box-shadow: 0 2px 10px rgba(15, 42, 92, .08); }
.wp-case-title { font-weight: 700; color: var(--navy); font-size: 1.05rem; }
.wp-tag { display: inline-block; margin-left: 8px; padding: 1px 9px; border-radius: 12px; background: #fff6ea; border: 1px solid var(--saffron); color: var(--ink); font-size: .8rem; font-weight: 700; }
.wp-track { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 14px 0; padding: 0; list-style: none; }
.wp-track li { font-size: .9rem; color: var(--ink); font-weight: 600; }
.wp-track li::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: var(--green); margin-right: 6px; }
.wp-row { display: grid; grid-template-columns: 1fr auto; gap: 2px 12px; padding: 10px 12px; border: 1px solid var(--line); border-left-width: 5px; border-radius: 4px; margin-bottom: 8px; animation: wp-in .4s ease-out both; }
.wp-row b { color: var(--ink); }
.wp-row small { grid-column: 1; color: var(--muted); font-size: .86rem; }
.wp-row em { grid-column: 2; grid-row: 1 / span 2; align-self: center; font-style: normal; font-weight: 700; font-size: .88rem; }
.wp-row.ok { border-left-color: var(--green); } .wp-row.ok em { color: var(--green); }
.wp-row.bad { border-left-color: var(--danger); background: #fff5f5; } .wp-row.bad em { color: var(--danger); }
.wp-row.info { border-left-color: var(--navy); } .wp-row.info em { color: var(--navy); }
.wp-row:nth-child(2) { animation-delay: .5s; } .wp-row:nth-child(3) { animation-delay: 1s; } .wp-row:nth-child(4) { animation-delay: 1.5s; }
.wp-verdict { margin-top: 12px; padding: 12px 14px; background: var(--navy); color: #fff; border-radius: 4px; font-weight: 700; animation: wp-in .4s ease-out 2s both; }
.wp-human { margin-top: 10px; color: var(--ink); font-weight: 700; text-align: center; }
@keyframes wp-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.wp-note { color: var(--muted); font-size: .88rem; margin: -6px 0 14px; }
.wp-section { color: var(--navy); font-size: 1.2rem; font-weight: 700; border-left: 5px solid var(--saffron); padding-left: 10px; margin: 22px 0 4px; }
.wp-sub2 { color: var(--muted); font-size: .95rem; margin-bottom: 10px; }
.wp-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
.wp-stat { border: 1px solid var(--line); border-top: 4px solid var(--navy); padding: 12px 14px; background: #fff; }
.wp-stat b { display: block; font-size: 1.7rem; color: var(--navy); }
.wp-stat small { color: var(--muted); font-size: .92rem; line-height: 1.4; display: block; }
.wp-table { width: 100%; border-collapse: collapse; font-size: .94rem; }
.wp-table th { background: var(--navy); color: #fff; text-align: left; padding: 8px 10px; }
.wp-table td { border: 1px solid var(--line); padding: 8px 10px; color: var(--ink); }
.wp-amount { font-weight: 700; white-space: nowrap; }
.wp-table td.wp-lost { color: #a4161a; }
.wp-table td.wp-kept { color: var(--green); }
.wp-steps { list-style: none; counter-reset: step; padding: 0 !important; margin: 0 !important; display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; }
.wp-steps li { counter-increment: step; background: var(--pale); border: 1px solid var(--line); padding: 10px 12px; font-size: .92rem; line-height: 1.4; color: var(--ink); }
.wp-steps li::before { content: "Step " counter(step); display: block; font-size: .78rem; font-weight: 700; color: var(--navy); text-transform: uppercase; }
.wp-steps li.you { background: #fff6ea; border-color: var(--saffron); }
.wp-foot { margin-top: 30px; padding: 12px 0; border-top: 3px solid var(--green); color: var(--muted); font-size: .88rem; line-height: 1.5; }
.stTabs [data-baseweb="tab-list"] { gap: 2px; background: var(--pale); border-bottom: 2px solid var(--navy); flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { padding: 10px 16px !important; color: var(--navy); font-weight: 600; }
.stTabs [aria-selected="true"] { background: var(--navy) !important; color: #fff !important; }
.stTabs [aria-selected="true"] p { color: #fff !important; }
button, .stLinkButton a { min-height: 44px; cursor: pointer; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted) !important; opacity: 1 !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] strong { color: var(--ink) !important; }
[data-testid="stAlert"] > div { border-left: 5px solid var(--danger); border-radius: 4px; }
.stFormSubmitButton button, .stDownloadButton button, .stLinkButton a { background: var(--navy) !important; color: #fff !important; border-radius: 4px !important; font-weight: 600; }
.stFormSubmitButton button p, .stDownloadButton button p, .stLinkButton a p { color: #fff !important; }
[data-testid="stForm"] { border: 1px solid var(--line); border-radius: 4px; background: var(--pale); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
@media (max-width: 640px) { .wp-hero { padding: 24px 18px; } .wp-hero h1 { font-size: 1.85rem; } .wp-name { font-size: 1.6rem; } .wp-help { white-space: normal; } .wp-table { font-size: .84rem; } }
</style>
"""

HEADER = """
<div class="wp-flag"></div>
<div class="wp-head">
  <div>
    <div class="wp-name">Wapsi <span>वापसी · వాపసీ</span></div>
    <div class="wp-sub">Cyber Fraud Recovery Assistant</div>
  </div>
  <div class="wp-help">Official helpline: <a href="tel:1930">1930</a></div>
</div>
<div class="wp-note">Independent citizen project. Not a government website or service, and not linked to RBI, I4C or any bank.</div>
"""

FOOTER = """
<div class="wp-foot">Wapsi is an independent project and is not a government service. Not legal advice.
Official channels: helpline 1930, cybercrime.gov.in and cms.rbi.org.in. Wapsi never asks for an OTP, PIN, password or a fee.</div>
"""


def page_style():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(HEADER, unsafe_allow_html=True)


def hero(language):
    st.markdown(
        f"""<section class="wp-hero"><h1>{TEXT['hero_title'][language]}</h1><p>{TEXT['hero_sub'][language]}</p><a class="wp-cta" href="#start-here">{TEXT['hero_cta'][language]}</a></section>""",
        unsafe_allow_html=True,
    )


def footer():
    st.markdown(FOOTER, unsafe_allow_html=True)


def stats(status):
    expected = sum(1 for source in checks.SOURCES if "clause" in source)
    found = sum(1 for source in status["sources"] if source.get("clause_verified"))
    reachable = sum(1 for source in status["sources"] if source["reachable"])
    st.markdown(
        f"""<div class="wp-stats">
<div class="wp-stat"><b>{rights.REPORT_DAYS} days</b><small>to file both, from the date of the fraud</small></div>
<div class="wp-stat"><b>{found} of {expected}</b><small>rule clauses found on RBI's site in the latest live check</small></div>
<div class="wp-stat"><b>{reachable} of {len(status['sources'])}</b><small>official source checks reachable just now</small></div>
</div>""",
        unsafe_allow_html=True,
    )


def two_report_table():
    rows = "".join(
        f"<tr><td>{name}</td><td class='wp-amount {'wp-kept' if amount else 'wp-lost'}'>Rs {amount:,} {'(eligible)' if amount else '(lost)'}</td></tr>"
        for name, amount in rights.two_report_scenarios()
    )
    st.markdown(
        f"<table class='wp-table'><tr><th>Same fraud, same Rs {rights.EXAMPLE_LOSS:,} loss. What was reported?</th><th>Compensation possible</th></tr>{rows}</table>",
        unsafe_allow_html=True,
    )


def case_walkthrough():
    case = rights.example_case()
    st.markdown(
        f"""<div class="wp-case">
<div class="wp-case-title">Rs {rights.EXAMPLE_LOSS:,} lost after sharing an OTP <span class="wp-tag">Example, not a real case</span></div>
<ol class="wp-track"><li>Secrets blocked</li><li>Fraud type read</li><li>Rules picked by date</li><li>Both routes checked</li></ol>
<div>
<div class="wp-row ok"><b>Bank report</b><small>Paragraph 76T: filed on {case['txn']:%d %b %Y}</small><em>Done</em></div>
<div class="wp-row bad"><b>Police report (1930 or cybercrime.gov.in)</b><small>Paragraph 76T: required as well as the bank report</small><em>Missing</em></div>
<div class="wp-row info"><b>Deadline for both</b><small>Five calendar days from the fraud</small><em>{case['deadline']:%d %b %Y}</em></div>
<div class="wp-row info"><b>Who must prove fault</b><small>Paragraph 76K: the burden of proof lies on the bank</small><em>The bank</em></div>
</div>
<div class="wp-verdict">Up to Rs {case['at_risk']:,} at risk. File with 1930 by {case['deadline']:%d %b %Y}.</div>
</div>
<div class="wp-human">The AI drafts. You check every fact and file it yourself.</div>""",
        unsafe_allow_html=True,
    )
