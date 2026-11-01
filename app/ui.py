import streamlit as st

from app import checks, rights

# Only constants and engine-computed values go through unsafe_allow_html, never user text
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600&family=Noto+Sans+Telugu:wght@400;600&display=swap');
:root { --navy: #0b2f6b; --saffron: #ff9933; --green: #138808; --line: #d5dce8; --ink: #1b2533; --muted: #4f5b6b; --pale: #f2f5fa; }
html, body, [class*="css"], .stApp { font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Telugu', sans-serif; }
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
.wp-note { color: var(--muted); font-size: .82rem; margin: -6px 0 14px; }
.wp-section { color: var(--navy); font-size: 1.2rem; font-weight: 700; border-left: 5px solid var(--saffron); padding-left: 10px; margin: 22px 0 4px; }
.wp-sub2 { color: var(--muted); font-size: .9rem; margin-bottom: 10px; }
.wp-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
.wp-stat { border: 1px solid var(--line); border-top: 4px solid var(--navy); padding: 12px 14px; background: #fff; }
.wp-stat b { display: block; font-size: 1.55rem; color: var(--navy); }
.wp-stat small { color: var(--muted); font-size: .84rem; }
.wp-table { width: 100%; border-collapse: collapse; font-size: .94rem; }
.wp-table th { background: var(--navy); color: #fff; text-align: left; padding: 8px 10px; }
.wp-table td { border: 1px solid var(--line); padding: 8px 10px; color: var(--ink); }
.wp-amount { font-weight: 700; white-space: nowrap; }
.wp-table td.wp-lost { color: #a4161a; }
.wp-table td.wp-kept { color: var(--green); }
.wp-steps { list-style: none; counter-reset: step; padding: 0 !important; margin: 0 !important; display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; }
.wp-steps li { counter-increment: step; background: var(--pale); border: 1px solid var(--line); padding: 10px 12px; font-size: .88rem; color: var(--ink); }
.wp-steps li::before { content: "Step " counter(step); display: block; font-size: .74rem; font-weight: 700; color: var(--navy); text-transform: uppercase; }
.wp-steps li.you { background: #fff6ea; border-color: var(--saffron); }
.wp-foot { margin-top: 30px; padding: 12px 0; border-top: 3px solid var(--green); color: var(--muted); font-size: .82rem; }
.stTabs [data-baseweb="tab-list"] { gap: 2px; background: var(--pale); border-bottom: 2px solid var(--navy); flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { padding: 10px 16px !important; color: var(--navy); font-weight: 600; }
.stTabs [aria-selected="true"] { background: var(--navy) !important; color: #fff !important; }
.stTabs [aria-selected="true"] p { color: #fff !important; }
.stFormSubmitButton button, .stDownloadButton button, .stLinkButton a { background: var(--navy) !important; color: #fff !important; border-radius: 4px !important; font-weight: 600; }
.stFormSubmitButton button p, .stDownloadButton button p, .stLinkButton a p { color: #fff !important; }
[data-testid="stForm"] { border: 1px solid var(--line); border-radius: 4px; background: var(--pale); }
@media (max-width: 640px) { .wp-name { font-size: 1.6rem; } .wp-help { white-space: normal; } .wp-table { font-size: .84rem; } }
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


def footer():
    st.markdown(FOOTER, unsafe_allow_html=True)


def stats(status):
    expected = sum(1 for source in checks.SOURCES if "clause" in source)
    found = sum(1 for source in status["sources"] if source.get("clause_verified"))
    reachable = sum(1 for source in status["sources"] if source["reachable"])
    st.markdown(
        f"""<div class="wp-stats">
<div class="wp-stat"><b>2</b><small>reports needed for compensation: bank and police</small></div>
<div class="wp-stat"><b>{rights.REPORT_DAYS} days</b><small>to file both, from the date of the fraud</small></div>
<div class="wp-stat"><b>{found} of {expected}</b><small>rule clauses found on RBI's site in the latest live check</small></div>
<div class="wp-stat"><b>{reachable} of {len(status['sources'])}</b><small>official source checks reachable just now</small></div>
</div>""",
        unsafe_allow_html=True,
    )


def two_report_table():
    rows = "".join(
        f"<tr><td>{name}</td><td class='wp-amount {'wp-kept' if amount else 'wp-lost'}'>Rs {amount:,}</td></tr>"
        for name, amount in rights.two_report_scenarios()
    )
    st.markdown(
        f"<table class='wp-table'><tr><th>Same fraud, same Rs {rights.EXAMPLE_LOSS:,} loss. What was reported?</th><th>Compensation possible</th></tr>{rows}</table>",
        unsafe_allow_html=True,
    )


def how_it_works():
    st.markdown(
        """<ol class="wp-steps">
<li>You describe what happened. OTPs are blocked and account numbers masked.</li>
<li>The AI identifies the type of fraud and asks if unsure.</li>
<li>Plain code picks the RBI rules by date and sets the deadlines.</li>
<li>Wapsi warns which report is missing and drafts both.</li>
<li class="you">You check the facts, log in and submit yourself. Wapsi never files for you.</li>
</ol>""",
        unsafe_allow_html=True,
    )
