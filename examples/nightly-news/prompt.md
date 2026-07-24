Write a concise nightly AI and software-engineering news brief for a principal / customer-facing AI engineer.

Content goals:
- Most important public AI, developer-tools, and cloud-engineering news from roughly the last 24h (extend to ~48h only if thin).
- High-signal only: model releases, major open-source tools, Azure/AI platform changes, agent/harness tooling, security incidents for builders, practical production-AI patterns.
- Skip celebrity noise, stock speculation, and vague hype.

Research rules:
- Public web search/fetch only. Prefer primary sources (official blogs, GitHub releases/changelogs, vendor advisories).
- At most ~8 tool calls, then write the final-response file. Do not keep researching forever.
- Do NOT invoke skills (no daily-briefing, no deep-research). Do not read secondbrain/vault notes.
- Do not send local repo names, customer data, internal Microsoft details, or credentials to external search.
- Do not modify project code, create PRs, or install packages. The only allowed write is the final-response brief file path injected by the runner.

After the required marker line in the final-response file (under 3000 characters after the marker):
1. One-line headline for the day.
2. 4–7 bullets. Each: what happened, why it matters to a principal / customer-facing AI engineer, and one public source URL.
3. Optional "Watch next" with at most 2 follow-ups.

The final-response file is the Telegram body. Progress narration is not a final response.
