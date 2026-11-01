import json

import streamlit as st

from app.i18n import TEXT

KEYS = ["clock_title", "clock_sub", "clock_bank", "clock_police", "clock_advised", "clock_done", "clock_ended", "clock_stake", "clock_protected", "clock_lost", "clock_note", "clock_preview", "clock_over"]

# Only numbers and translated constants reach this page, never user text
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700;800&family=Noto+Sans+Devanagari:wght@400;700;800&family=Noto+Sans+Telugu:wght@400;700;800&display=swap');
* { box-sizing: border-box; margin: 0; }
body { font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Telugu', sans-serif; background: #0a0f2c; color: #fff; padding: 22px clamp(12px, 3vw, 34px); border-radius: 18px; }
h1 { font-size: clamp(1.45rem, 4.4vw, 2.7rem); line-height: 1.15; font-weight: 800; }
.sub { color: #c8cfea; font-size: clamp(.9rem, 2vw, 1.05rem); margin-top: 6px; }
.room { display: grid; grid-template-columns: 1fr minmax(92px, 170px) 1fr; align-items: center; gap: clamp(2px, 2vw, 22px); margin-top: 16px; }
.clock { position: relative; width: 100%; max-width: 250px; aspect-ratio: 1; justify-self: center; }
.clock svg { width: 100%; height: 100%; transform: rotate(-90deg); display: block; }
.track { fill: none; stroke: #232a55; stroke-width: 9; }
.arc { fill: none; stroke-width: 9; stroke-linecap: round; }
.face { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 14%; }
.name { font-size: clamp(.72rem, 2.2vw, 1rem); font-weight: 700; color: #dfe4f7; }
.time { font-size: clamp(1rem, 3.6vw, 1.75rem); font-weight: 800; font-variant-numeric: tabular-nums; line-height: 1.2; }
.unit { font-size: clamp(.68rem, 1.8vw, .85rem); color: #c8cfea; }
.money { text-align: center; }
.amount { font-size: clamp(1.25rem, 5vw, 2.7rem); font-weight: 800; color: #ffb35c; line-height: 1.1; white-space: nowrap; }
.label { font-size: clamp(.72rem, 2vw, .95rem); color: #dfe4f7; }
.state { margin-top: 14px; padding: 9px 14px; border-radius: 8px; font-weight: 700; text-align: center; font-size: clamp(.84rem, 2vw, 1rem); }
.run { background: #1b2350; } .ok { background: #0f6b06; } .bad { background: #a4161a; }
.note { color: #aeb6d8; font-size: .76rem; text-align: center; margin-top: 7px; }
@media (max-width: 560px) {
  .room { grid-template-columns: 1fr 1fr; gap: 8px; }
  .money { grid-column: 1 / -1; order: -1; }
  .amount { font-size: 2.2rem; }
  .face { padding: 8%; }
  .time { font-size: .92rem; }
  .name { font-size: .78rem; }
}
</style></head><body>
<h1 id="title"></h1><p class="sub" id="sub"></p>
<div class="room"><div class="clock" id="bank"></div><div class="money"><div class="amount" id="amount"></div><div class="label" id="label"></div></div><div class="clock" id="police"></div></div>
<div class="state" id="state" role="status"></div><p class="note" id="note"></p>
<script>
const data = __DATA__;
const t = data.text;
const R = 54, C = 2 * Math.PI * R;
function face(id, name, done, optional, left) {
  const fraction = done ? 1 : Math.max(0, Math.min(1, left / data.total));
  const color = done ? "#3ddc55" : left <= 0 ? "#ff5a5f" : optional ? "#8fa0e8" : (id === "bank" ? "#ff9933" : "#7be07b");
  let main, unit = "";
  if (done) { main = "&#10003;"; unit = t.clock_done; }
  else if (left <= 0) { main = "0"; unit = t.clock_ended; }
  else {
    const d = Math.floor(left / 86400), h = Math.floor(left % 86400 / 3600), m = Math.floor(left % 3600 / 60), s = Math.floor(left % 60);
    main = (d ? d + "d " : "") + String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    unit = optional ? t.clock_advised : "";
  }
  document.getElementById(id).innerHTML = '<svg viewBox="0 0 120 120" aria-hidden="true"><circle class="track" cx="60" cy="60" r="' + R + '"/><circle class="arc" cx="60" cy="60" r="' + R + '" stroke="' + color + '" stroke-dasharray="' + C + '" stroke-dashoffset="' + (C * (1 - fraction)) + '"/></svg><div class="face"><div class="name">' + name + '</div><div class="time" style="color:' + color + '">' + main + '</div><div class="unit">' + unit + '</div></div>';
}
document.getElementById("title").textContent = t.clock_title;
document.getElementById("sub").textContent = t.clock_sub;
document.getElementById("note").textContent = (data.preview ? t.clock_preview + " " : "") + t.clock_note;
document.getElementById("amount").textContent = data.amount === null ? "" : "\\u20b9" + data.amount.toLocaleString("en-IN");
document.getElementById("label").textContent = t.clock_stake;
const start = Date.now();
function tick() {
  const left = data.remaining - (Date.now() - start) / 1000;
  face("bank", t.clock_bank, data.bank_done, false, left);
  face("police", t.clock_police, data.police_done, data.police_optional, left);
  const state = document.getElementById("state");
  const needed = data.bank_done && (data.police_done || data.police_optional);
  const message = data.over_limit ? [t.clock_over, "run"] : needed ? [t.clock_protected, "ok"] : left <= 0 ? [t.clock_lost, "bad"] : [data.waiting, "run"];
  state.textContent = message[0]; state.className = "state " + message[1];
}
tick(); setInterval(tick, 1000);
</script></body></html>"""


def show(state, language):
    text = {key: TEXT[key][language] for key in KEYS}
    waiting = TEXT["clock_wait_both"] if not state["bank_done"] and not state["police_done"] else TEXT["clock_wait_police"] if state["bank_done"] else TEXT["clock_wait_bank"]
    payload = state | {"text": text, "waiting": waiting[language]}
    # "</" is escaped so the data cannot close the script tag
    st.iframe(PAGE.replace("__DATA__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")), height="content", alt=text["clock_title"])
