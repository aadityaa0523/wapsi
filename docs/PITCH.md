# Wapsi: submission text

Forge '26, Theme 1, Problem 3: Autonomous Public Service and Bureaucracy Execution Agent

## Problem statement

### The problem in one line

**After cyber fraud, victims in India have to deal with their bank and the police separately, in panic, under deadlines and rules nobody has told them about, so they can lose money they were entitled to protect.**

### What it looks like in real life

*An illustrative example, not a real case:* a retired man gets a call saying his KYC has expired. He shares an OTP and Rs 10,000 leaves his account. He calls his bank and thinks he has done everything. He now faces questions he cannot answer:

- Have I done enough, or do I also need to report to the police, and how?
- Is there a deadline? When did it start?
- The bank says the fraud was my fault. Do I just accept that?
- Someone has called offering to recover my money for a fee. Is that real?

### Why this is a problem today

These rules already apply under the [RBI 2017 circular](https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040):

- **Delay costs money.** If someone shared credentials, they bear the loss until they report to the bank (paragraph 7). Zero liability for a third-party breach needs a report within 3 working days of the bank's message (paragraph 6).
- **Banks' refusals can be challenged, but few would know how.** The burden of proving customer liability is on the bank (paragraph 12), and complaints must be resolved within 90 days (paragraph 10).

The scale is large: more than 65.89 lakh financial fraud complaints and more than Rs 55,050 crore reported on the national portal from 2021 to 2025. More than Rs 8,189 crore of that was marked as lien, which means held and not necessarily returned ([PIB, 21 July 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287039&reg=48&lang=2)).

### Why it gets more urgent on 1 January 2027

A person who shared an OTP can then claim compensation: 85% of the net loss, up to Rs 25,000, for gross losses up to Rs 50,000, once in a lifetime. But they must report to **both** their bank **and** the police route within **five calendar days** ([RBI directions, paragraph 76T](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0)). In the example above, calling only the bank could cost up to Rs 8,500.

### Target audience

- **Directly affected:** individuals and sole proprietors who lose up to Rs 50,000 to digital fraud, especially first-time victims who cannot read RBI directions or English.
- **Helpers:** the relatives, bank staff, cyber cell volunteers and legal aid workers who sit with victims.
- **Also served:** anyone whose bank has rejected a claim, and victims targeted again by fake recovery agents.

## Solution

### High-level overview

Other tools help you write a complaint. **Wapsi protects your compensation.**

Four simple questions lead to two live clocks, one for the bank and one for the police, with the rupees at stake between them and one clear next action. Wapsi applies the RBI rules that match the transaction date, in plain code, and checks the rule text live on RBI's own website. When a report is filed, it says what is still missing: "One report is not enough."

| What Wapsi does | How it helps |
|---|---|
| Two live clocks | Makes an invisible legal deadline visible |
| Rules chosen by date | Applies the 2017 circular or the 2027 directions correctly |
| Live Clause Check | Shows that each rule is still on RBI's page, right now |
| Rejection Decoder | Matches a bank's refusal to the RBI paragraph and writes the reply |
| Recovery-scam checker | Warns about fees, remote-access apps and fake officials |
| Filing Kit | Prepares details to the police portal's published requirements |
| Proof Pack and evidence fingerprints | Gives a tamper-evident record, without storing the files |
| Safety first | Blocks OTPs and sends a person on a scam call straight to "Hang up" |

Wapsi never files for the victim. The declaration, OTP, captcha and submit stay with the person, because a false complaint carries legal risk.

### How we differ

Based on the public materials we reviewed. Other tools may have changed.

| | Official portal and 1930 | Samarthan | CyberSaarthi | Wapsi |
|---|---|---|---|---|
| Report a fraud officially | Yes | No | No | No: hands over |
| Draft complaint help | Not reviewed | Yes | Yes | Yes |
| RBI compensation and deadline calculation | Not found | Not found | Not found | **Yes** |
| Tracks bank and police clocks together | Not found | Not found | Not found | **Yes** |
| Live check of RBI rule text | Not found | Not found | Not found | **Yes** |
| Answers a bank's rejection using RBI paragraphs | Not found | Not found | Not found | **Yes** |

Samarthan offers more languages and voice input than Wapsi does today, and the official portal is the only place to actually file. Wapsi works alongside these. It does not replace them.

### Technical architecture

Browser, then a Streamlit app, then a Safety Guard that blocks secrets and masks identifiers. An LLM agent reads the story and drafts text. A plain-code Rights Engine decides every deadline and amount, and a Fact Checker rejects any draft with an unsupported number or a promised result. A live checker fetches RBI and portal pages. Events go to a hash-chained log. The full diagram is in the README.

## Limits we state openly

- The 2027 rules are not yet in force, so the clock is labelled as a preview until then.
- Wapsi is a prototype, with no legal review or independent security audit. See `SECURITY.md`.
- The bank decides each claim. Wapsi shows what is possible, and it never promises money.
