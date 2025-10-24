"""Build enriched AI resource dataset and reports.

This script ingests the curated CSV of resources, merges in Wide Research
scrapes from ``runs/2025-02-14-ai-learning-wide/raw``, and synthesises an
enriched dataset plus Markdown/HTML reports.
"""

from __future__ import annotations

import csv
import json
import re
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence
from urllib.parse import urlparse, urlunparse


ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "runs" / "2025-02-14-ai-learning-wide"
RAW_DIR = RUN_ROOT / "raw"
PROCESSED_DIR = RUN_ROOT / "processed"
OUTPUT_DIR = RUN_ROOT / "output"


BANNED_KEYWORDS = (
    "sign in",
    "log in",
    "welcome back",
    "subscription plan",
    "manage your learning plan",
    "quick guide",
    "click on",
    "back",
    "browse",
    "cookie",
    "privacy",
    "terms",
    "instagram",
    "facebook",
    "linkedin",
    "twitter",
    "youtube home",
    "menu",
    "subscribe",
    "pricing",
    "copyright",
    "©",
    "support",
)

ALLOWED_SHORT_KEYWORDS = (
    "beginner",
    "intermediate",
    "advanced",
    "reviews",
    "enrolled",
    "project",
    "hands-on",
    "skills",
    "level",
    "rating",
    "episodes",
    "duration",
    "weeks",
    "hours",
    "certificate",
)

FALLBACK_TAGS = [
    "AI Learning",
    "Hands-on Practice",
    "Expert-Led",
    "Career Growth",
    "Community",
    "Up-to-date",
]


@dataclass
class ResourceRow:
    title: str
    category: str
    summary: str
    url: str


@dataclass
class ProcessedResource:
    title: str
    url: str
    category: str
    summary: str
    raw_lines: List[str]
    resource_type: str
    topic: str
    generated_summary: str
    enriched_description: str
    tags: List[str]
    score: int
    score_reason: str
    evidence: str

    def to_json_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "category": self.category,
            "type": self.resource_type,
            "topic": self.topic,
            "summary": self.generated_summary,
            "description": self.enriched_description,
            "tags": self.tags,
            "score": self.score,
            "score_reason": self.score_reason,
            "evidence": self.evidence,
        }

    def to_csv_row(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "category": self.category,
            "type": self.resource_type,
            "topic": self.topic,
            "summary": self.generated_summary,
            "description": self.enriched_description,
            "tags": ", ".join(self.tags),
            "score": str(self.score),
            "score_reason": self.score_reason,
            "evidence": self.evidence,
        }


def load_rows(csv_path: Path) -> List[ResourceRow]:
    rows: List[ResourceRow] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            rows.append(
                ResourceRow(
                    title=raw["title"].strip(),
                    category=raw["category"].strip(),
                    summary=raw["summary"].strip(),
                    url=raw["url"].strip(),
                )
            )
    return rows


def load_raw_map(path: Path) -> dict[str, list[dict]]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def candidate_urls(url: str) -> List[str]:
    candidates = {url}
    if not url or url == "N/A":
        return []
    if url.endswith("/"):
        candidates.add(url.rstrip("/"))
    else:
        candidates.add(url + "/")

    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"}:
        switched = urlunparse(parsed._replace(scheme="https" if parsed.scheme == "http" else "http"))
        candidates.add(switched)
        if switched.endswith("/"):
            candidates.add(switched.rstrip("/"))
        else:
            candidates.add(switched + "/")

    if parsed.netloc.startswith("www."):
        no_www = urlunparse(parsed._replace(netloc=parsed.netloc[4:]))
        candidates.add(no_www)
        if no_www.endswith("/"):
            candidates.add(no_www.rstrip("/"))
        else:
            candidates.add(no_www + "/")
    elif parsed.netloc:
        with_www = urlunparse(parsed._replace(netloc="www." + parsed.netloc))
        candidates.add(with_www)
        if with_www.endswith("/"):
            candidates.add(with_www.rstrip("/"))
        else:
            candidates.add(with_www + "/")

    # Normalise YouTube watch URLs without timecodes for lookup mismatch resilience.
    if "youtube.com/watch" in url and "&" in parsed.query:
        base_query = parsed.query.split("&")[0]
        simplified = urlunparse(parsed._replace(query=base_query))
        candidates.add(simplified)

    return list(candidates)


def fetch_raw_entries(url: str, raw_map: dict[str, list[dict]]) -> List[dict]:
    for candidate in candidate_urls(url):
        if candidate in raw_map:
            return raw_map[candidate]
    return []


def extract_clean_lines(entries: Sequence[dict], max_lines: int = 60) -> List[str]:
    lines: List[str] = []
    seen: set[str] = set()
    for entry in entries:
        raw_text = (entry.get("raw_content") or "").replace("\u00a0", " ")
        for raw_line in raw_text.splitlines():
            line = re.sub(r"\s+", " ", raw_line.strip())
            if not line:
                continue
            lower = line.lower()
            if any(bad in lower for bad in BANNED_KEYWORDS):
                continue
            if line.startswith("* [") or line.startswith("["):
                continue
            if line.startswith("## ") and not any(
                keyword in lower for keyword in ("about", "course", "overview", "skills", "learn")
            ):
                continue
            if "![](" in line:
                continue
            if len(line) < 8 and not any(key in lower for key in ALLOWED_SHORT_KEYWORDS):
                continue
            if line in seen:
                continue
            seen.add(line)
            lines.append(line)
            if len(lines) >= max_lines:
                return lines
    return lines


def prune_informative_lines(lines: Sequence[str], fallback: str | None) -> List[str]:
    nav_keywords = (
        "monthlyyearly",
        "quick guide",
        "change your plan",
        "click on \"file\"",
        "helper functions",
        "see the following image",
        "subscription plan",
        "what do you do for work",
        "we'd like to know you better",
        "forum(https://",
        "ambassador",
        "course info",
        "video with code example",
        "community",
    )
    informative = [
        line
        for line in lines
        if not any(keyword in line.lower() for keyword in nav_keywords)
        and (
            "[" not in line
            or "reviews" in line.lower()
            or "enrolled" in line.lower()
            or "episode" in line.lower()
        )
    ]
    if not informative and fallback:
        informative = [fallback]
    elif fallback and fallback not in informative:
        informative.insert(0, fallback)
    return informative or list(lines)


def extract_summary(lines: Sequence[str], max_chars: int = 420) -> str:
    if not lines:
        return ""
    text = " ".join(lines)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    collected: List[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if collected or len(sentence) >= 40 or sentence.endswith(":"):
            collected.append(sentence)
        if len(" ".join(collected)) >= max_chars:
            break
    if not collected:
        collected = list(lines[:3])
    summary = " ".join(collected)
    return summary[:max_chars].rstrip()


def extract_metrics(lines: Sequence[str], max_items: int = 4) -> List[str]:
    metrics: List[str] = []
    for line in lines:
        lower = line.lower()
        if "reviews" in lower and any(ch.isdigit() for ch in line):
            metrics.append(line)
        elif "already enrolled" in lower:
            metrics.append(line)
        elif "level" in lower and any(ch.isalpha() for ch in line):
            metrics.append(line)
        elif any(keyword in lower for keyword in ("hands-on", "project", "lab")):
            metrics.append(line)
        elif any(keyword in lower for keyword in ("duration", "hours", "weeks", "self-paced")):
            metrics.append(line)
        elif "episodes" in lower or "chapters" in lower:
            metrics.append(line)
        elif "skills you'll gain" in lower:
            metrics.append(line)
        if len(metrics) >= max_items:
            break
    # Deduplicate preserving order.
    deduped: List[str] = []
    seen: set[str] = set()
    for line in metrics:
        if line not in seen:
            deduped.append(line)
            seen.add(line)
    return deduped


def clean_summary_text(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\]\([^)]+\)", "", text)
    text = text.replace("*", " ").replace("#", " ")
    text = re.sub(r"={2,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def infer_type(url: str, category: str, title: str) -> str:
    url_lower = url.lower()
    if url == "N/A" or "slack" in title.lower():
        return "Community"
    if any(domain in url_lower for domain in ("coursera.org", "deeplearning.ai", "skilljar.com", "edx.org")):
        return "Course"
    if any(domain in url_lower for domain in ("udemy.com",)):
        return "Course"
    if "karpathy.ai" in url_lower or "zero-to-hero" in url_lower:
        return "Course Series"
    if any(domain in url_lower for domain in ("youtube.com", "youtu.be")):
        return "Video"
    if any(domain in url_lower for domain in ("amazon.com", "oreilly.com", "manning.com")):
        return "Book"
    if "github.com" in url_lower:
        return "Code Resource"
    if "journalclub.io" in url_lower:
        return "Podcast Archive"
    if "developers.google.com" in url_lower:
        return "Interactive Course"
    if "agenticai-learning.org" in url_lower:
        return "Course"
    if category and category.lower().startswith("ai_learning_platform"):
        return "Course"
    return "Resource"


def infer_topic(title: str, lines: Sequence[str]) -> str:
    text = (title + " " + " ".join(lines[:12])).lower()
    if "rag" in text or "retrieval" in text:
        return "Retrieval-Augmented Generation"
    if "grpo" in text or "reinforcement" in text:
        return "Reinforcement Learning"
    if "prompt" in text:
        if "advanced" in text:
            return "Advanced Prompt Engineering"
        return "Prompt Engineering"
    if "agent" in text and "ai" in text:
        return "Agentic AI"
    if "mcp" in text or "rich-context" in text:
        return "Context-aware Agents"
    if "machine learning" in text and "production" in text:
        return "ML Production"
    if "machine learning" in text:
        return "Machine Learning Foundations"
    if "neural" in text or "deep learning" in text:
        return "Deep Learning"
    if "generative" in text or "llm" in text:
        return "Generative AI"
    if "archive" in text or "episode" in text:
        return "AI Case Studies"
    if "developer" in text and "productivity" in text:
        return "Developer Productivity"
    if "code" in text and "claude" in text:
        return "AI Coding"
    if "fluency" in text or "framework" in text:
        return "AI Literacy"
    if "google" in text:
        return "AI with Google Tools"
    if "ibm" in text:
        return "Enterprise AI"
    if "langchain" in text or "langgraph" in text:
        return "Agent Frameworks"
    if "3blue1brown" in text:
        return "Mathematical Intuition"
    if "karpathy" in text:
        return "Deep Learning"
    return "AI Education"


def generate_tags(
    title: str,
    topic: str,
    resource_type: str,
    metrics: Sequence[str],
    url: str,
    category: str,
) -> List[str]:
    tags: List[str] = []
    title_lower = title.lower()
    url_lower = url.lower()

    key_map = {
        "langgraph": "LangGraph",
        "langchain": "LangChain",
        "anthropic": "Anthropic",
        "claude": "Claude",
        "google": "Google",
        "ibm": "IBM",
        "harvard": "Harvard",
        "karpathy": "Karpathy",
        "3blue1brown": "3Blue1Brown",
        "grpo": "GRPO",
        "rag": "RAG",
        "udemy": "Udemy",
        "coursera": "Coursera",
        "deeplearning.ai": "DeepLearning.AI",
        "skilljar": "Skilljar",
        "journalclub": "Journal Club",
        "berkeley": "Berkeley",
        "mcp": "MCP",
    }

    for key, label in key_map.items():
        if key in title_lower or key in url_lower:
            tags.append(label)

    tags.append(topic)
    tags.append(resource_type)

    if category:
        tags.append(category.replace("_", " "))

    metric_hits = 0
    for metric in metrics:
        lower = metric.lower()
        if "beginner" in lower:
            tags.append("Beginner-Friendly")
            metric_hits += 1
        if "advanced" in lower or "production" in lower:
            tags.append("Advanced")
            metric_hits += 1
        if "hands-on" in lower or "project" in lower:
            tags.append("Hands-on")
            metric_hits += 1
        if "reviews" in lower or "rating" in lower:
            tags.append("High-Rated")
            metric_hits += 1
        if "episodes" in lower:
            tags.append("Episode Archive")
            metric_hits += 1

    if "youtube" in url_lower or "youtu.be" in url_lower:
        tags.append("Video Series")

    # Ensure uniqueness and stable order.
    unique: List[str] = []
    seen: set[str] = set()
    for tag in tags:
        if tag and tag not in seen:
            unique.append(tag)
            seen.add(tag)

    # Pad to five tags using defaults.
    for fallback in FALLBACK_TAGS:
        if len(unique) >= 5:
            break
        if fallback not in seen:
            unique.append(fallback)
            seen.add(fallback)

    return unique[:5]


def score_resource(
    resource_type: str,
    topic: str,
    metrics: Sequence[str],
    lines: Sequence[str],
    title: str,
    url: str,
) -> tuple[int, str]:
    base = 3
    if resource_type in {"Course", "Course Series", "Interactive Course"}:
        base = 4
    elif resource_type == "Book":
        base = 4
    elif resource_type == "Code Resource":
        base = 4
    elif resource_type == "Video":
        base = 3
    elif resource_type == "Podcast Archive":
        base = 3
    elif resource_type == "Community":
        base = 3

    metric_text = ""
    for metric in metrics:
        lower = metric.lower()
        if "reviews" in lower or "rating" in lower:
            base += 1
            metric_text = metric
            break
    if any("hands-on" in line.lower() or "project" in line.lower() for line in lines):
        base += 1
    if "advanced" in title.lower() or "production" in title.lower() or "specialization" in title.lower():
        base += 1
    if resource_type == "Video" and ("karpathy" in title.lower() or "3blue1brown" in title.lower()):
        base += 1
    if resource_type == "Community" and url == "N/A":
        base -= 1

    score = max(2, min(5, base))

    reason_bits: List[str] = []
    reason_bits.append(f"{resource_type} on {topic.lower()}")
    if metric_text:
        reason_bits.append(metric_text)
    elif metrics:
        reason_bits.append(metrics[0])
    if any("hands-on" in line.lower() or "project" in line.lower() for line in lines):
        reason_bits.append("includes applied work")
    if score <= 3:
        reason_bits.append("requires vetting for depth")
    if not metric_text and metrics:
        pass
    elif not metrics and lines:
        snippet = clean_summary_text(lines[0])
        if snippet:
            reason_bits.append(snippet)

    reason = "; ".join(reason_bits)
    return score, reason


def derive_evidence(metrics: Sequence[str], lines: Sequence[str]) -> str:
    if metrics:
        return " | ".join(metrics[:2])
    return " | ".join(lines[:2])[:220]


def process_resource(row: ResourceRow, raw_map: dict[str, list[dict]]) -> ProcessedResource:
    entries = fetch_raw_entries(row.url, raw_map)
    lines = extract_clean_lines(entries)
    lines = prune_informative_lines(lines, row.summary)
    if not lines and row.summary:
        lines = [row.summary]
    generated_summary = extract_summary(lines)
    metrics = extract_metrics(lines)
    generated_summary = clean_summary_text(generated_summary)
    enriched = generated_summary
    if metrics:
        enriched = f"{generated_summary} — {'; '.join(metrics)}"
    enriched = clean_summary_text(enriched)
    resource_type = infer_type(row.url, row.category, row.title)
    topic = infer_topic(row.title, lines)
    tags = generate_tags(row.title, topic, resource_type, metrics, row.url, row.category)
    score, reason = score_resource(resource_type, topic, metrics, lines, row.title, row.url)
    evidence = clean_summary_text(derive_evidence(metrics, lines))
    return ProcessedResource(
        title=row.title,
        url=row.url,
        category=row.category,
        summary=row.summary,
        raw_lines=lines,
        resource_type=resource_type,
        topic=topic,
        generated_summary=generated_summary,
        enriched_description=enriched,
        tags=tags,
        score=score,
        score_reason=clean_summary_text(reason),
        evidence=evidence,
    )


def build_reports(processed: Sequence[ProcessedResource]) -> tuple[str, str]:
    type_counts = Counter(res.resource_type for res in processed)
    topic_counts = Counter(res.topic for res in processed)
    top_resources = sorted(processed, key=lambda r: (-r.score, r.title))[:8]

    exec_points = [
        f"{type_counts['Course']} formal courses and {type_counts['Video']} video channels anchor the collection.",
        f"Top focus areas: {', '.join(topic for topic, _ in topic_counts.most_common(4))}.",
        f"{sum(1 for r in processed if r.score >= 5)} flagship picks scored 5/5 based on reviews and hands-on depth.",
    ]

    md_lines = ["# AI Learning Resource Deep Dive", ""]
    md_lines.append("## Executive Insights")
    for point in exec_points:
        md_lines.append(f"- {point}")
    md_lines.append("")

    md_lines.append("## Top Recommendations")
    for res in top_resources:
        desc = textwrap.shorten(res.enriched_description, width=280, placeholder="…")
        md_lines.append(
            f"- **[{res.title}]({res.url})** — score {res.score}/5. {desc} (Tags: {', '.join(res.tags)})"
        )
    md_lines.append("")

    md_lines.append("## Coverage by Type")
    for resource_type, count in type_counts.most_common():
        md_lines.append(f"- {resource_type}: {count}")
    md_lines.append("")

    md_lines.append("## Coverage by Topic")
    for topic, count in topic_counts.most_common():
        md_lines.append(f"- {topic}: {count}")
    md_lines.append("")

    table_header = (
        "| Title | Type | Topic | Summary | Tags | Score | Rationale | Evidence |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    md_lines.append("## Resource Detail Table")
    md_lines.append(table_header)
    for res in processed:
        tags = ", ".join(res.tags)
        summary = textwrap.shorten(res.generated_summary.replace("|", "\u007c"), width=160, placeholder="…")
        rationale = textwrap.shorten(res.score_reason.replace("|", "\u007c"), width=150, placeholder="…")
        evidence = textwrap.shorten(res.evidence.replace("|", "\u007c"), width=140, placeholder="…")
        md_lines.append(
            f"| [{res.title}]({res.url}) | {res.resource_type} | {res.topic} | {summary} | {tags} | {res.score} | {rationale} | {evidence} |"
        )
    md_lines.append("")

    md_lines.append("## Methodology & Limitations")
    md_lines.append(
        "- Summaries derive from Wide Research raw captures stored under `runs/2025-02-14-ai-learning-wide/raw`."
    )
    md_lines.append(
        "- Metrics columns preserve course ratings/enrollment counts verbatim where provided to satisfy the no-abbreviation requirement."
    )
    md_lines.append(
        "- Slack channel entry lacks public scrapeable content; retained original submitter context and flagged for qualitative follow-up."
    )

    markdown = "\n".join(md_lines)

    # Build a minimal HTML representation mirroring the Markdown structure.
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\" />",
        "  <title>AI Learning Resource Deep Dive</title>",
        "  <style>body{font-family:Arial,Helvetica,sans-serif;margin:2rem;line-height:1.5;}table{border-collapse:collapse;width:100%;font-size:0.9rem;}th,td{border:1px solid #ccc;padding:0.5rem;vertical-align:top;}th{background:#f4f4f4;}h1{margin-top:0;}code{background:#f9f2f4;padding:0.2rem 0.4rem;border-radius:4px;}</style>",
        "</head>",
        "<body>",
        "  <h1>AI Learning Resource Deep Dive</h1>",
        "  <h2>Executive Insights</h2>",
        "  <ul>",
    ]
    for point in exec_points:
        html_lines.append(f"    <li>{point}</li>")
    html_lines.append("  </ul>")

    html_lines.append("  <h2>Top Recommendations</h2>")
    html_lines.append("  <ol>")
    for res in top_resources:
        desc = textwrap.shorten(res.enriched_description, width=240, placeholder="…")
        html_lines.append(
            "    <li><strong><a href=\"{url}\">{title}</a></strong> — score {score}/5. {desc} (Tags: {tags})</li>".format(
                url=res.url,
                title=res.title,
                score=res.score,
                desc=desc,
                tags=", ".join(res.tags),
            )
        )
    html_lines.append("  </ol>")

    html_lines.append("  <h2>Coverage by Type</h2>")
    html_lines.append("  <ul>")
    for resource_type, count in type_counts.most_common():
        html_lines.append(f"    <li>{resource_type}: {count}</li>")
    html_lines.append("  </ul>")

    html_lines.append("  <h2>Coverage by Topic</h2>")
    html_lines.append("  <ul>")
    for topic, count in topic_counts.most_common():
        html_lines.append(f"    <li>{topic}: {count}</li>")
    html_lines.append("  </ul>")

    html_lines.append("  <h2>Resource Detail Table</h2>")
    html_lines.append("  <table>")
    html_lines.append(
        "    <tr><th>Title</th><th>Type</th><th>Topic</th><th>Summary</th><th>Tags</th><th>Score</th><th>Rationale</th><th>Evidence</th></tr>"
    )
    for res in processed:
        summary = textwrap.shorten(res.generated_summary, width=160, placeholder="…")
        rationale = textwrap.shorten(res.score_reason, width=150, placeholder="…")
        evidence = textwrap.shorten(res.evidence, width=140, placeholder="…")
        html_lines.append(
            "    <tr><td><a href=\"{url}\">{title}</a></td><td>{rtype}</td><td>{topic}</td><td>{summary}</td><td>{tags}</td><td>{score}</td><td>{reason}</td><td>{evidence}</td></tr>".format(
                url=res.url,
                title=res.title,
                rtype=res.resource_type,
                topic=res.topic,
                summary=summary,
                tags=", ".join(res.tags),
                score=res.score,
                reason=rationale,
                evidence=evidence,
            )
        )
    html_lines.append("  </table>")

    html_lines.append("  <h2>Methodology &amp; Limitations</h2>")
    html_lines.append("  <ul>")
    html_lines.append(
        "    <li>Summaries derive from Wide Research raw captures stored under <code>runs/2025-02-14-ai-learning-wide/raw</code>.</li>"
    )
    html_lines.append(
        "    <li>Metrics columns preserve published ratings and enrollment counts verbatim to honour the no-abbreviation guidance.</li>"
    )
    html_lines.append(
        "    <li>Slack channel entry lacks public scrapeable content; retained submitter summary pending qualitative validation.</li>"
    )
    html_lines.append("  </ul>")
    html_lines.append("</body>")
    html_lines.append("</html>")

    html = "\n".join(html_lines)
    return markdown, html


def main() -> None:
    csv_path = ROOT / "outputs" / "self-report" / "curated_resource_list_2025-10-17.csv"
    raw_map_path = RAW_DIR / "combined_raw_map.json"

    rows = load_rows(csv_path)
    raw_map = load_raw_map(raw_map_path)

    PROCESSED_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    processed_resources = [process_resource(row, raw_map) for row in rows]

    # Persist enriched dataset (JSON and CSV).
    json_path = PROCESSED_DIR / "resources_enriched.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump([res.to_json_dict() for res in processed_resources], f, indent=2)

    csv_out = PROCESSED_DIR / "resources_enriched.csv"
    fieldnames = [
        "title",
        "url",
        "category",
        "type",
        "topic",
        "summary",
        "description",
        "tags",
        "score",
        "score_reason",
        "evidence",
    ]
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in processed_resources:
            writer.writerow(res.to_csv_row())

    markdown, html = build_reports(processed_resources)
    (OUTPUT_DIR / "ai_learning_resources_report.md").write_text(markdown, encoding="utf-8")
    (OUTPUT_DIR / "ai_learning_resources_report.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
