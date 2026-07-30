from pathlib import Path

from runwisp_jobs.report import ReportPolicy, main

PROMPT_PATH = Path(__file__).with_name("prompt.md")
POLICY = ReportPolicy(
    task_name="nightly-news-brief",
    header="📰 nightly-news-brief",
    marker="===NIGHTLY_NEWS_BRIEF===",
    validator="news",
    min_bullets=4,
    min_urls=4,
    min_chars=120,
    max_chars=3000,
    max_autopilot_continues=25,
    no_custom_instructions=True,
)

if __name__ == "__main__":
    raise SystemExit(main(POLICY, PROMPT_PATH))
