"""Attach guardrail verdicts (Llama Guard, MD-Judge, Qwen3Guard) to hacking_safety.json.

Usage:
    python add_guardrails.py LABELS.jsonl [baseline.json] [hacking_safety.json]

LABELS.jsonl is guardrails/merged_labels.jsonl from the Epistemic-Injustice-in-LLM
repo: one row per sentence, keyed by (doc_id, sent_id) in the baseline dataset.
Records of hacking_safety.json are matched to baseline docs by URL.

Adds to every record a `guardrails` list with one entry per sentence that at least
one guard did not rate as safe (Qwen3Guard "Controversial" counts as not safe):
    {"sent": i, "llama_guard": {"label", "categories"}, "md_judge": {"label", "categories"},
     "qwen_guard": {"label", "categories"}}
The input file is rewritten in place.
"""
import json
import sys


def verdict(row):
    lg, md, qg = row["llama_guard"], row["md_judge"], row["qwen_guard"]
    return {
        "llama_guard": {"label": lg["label"], "categories": lg.get("category_names") or []},
        "md_judge": {"label": md["label"],
                     "categories": [md["category_name"]] if md.get("category_name") else []},
        "qwen_guard": {"label": qg["label"].lower(), "categories": qg.get("categories") or []},
    }


def not_safe(v):
    return any(v[g]["label"] != "safe" for g in ("llama_guard", "md_judge", "qwen_guard"))


def main(argv):
    labels = argv[0]
    baseline = argv[1] if len(argv) > 1 else "16_baseline.json"
    src = argv[2] if len(argv) > 2 else "hacking_safety.json"

    data = json.load(open(src, encoding="utf-8"))
    url2doc = {}
    for i, x in enumerate(json.load(open(baseline, encoding="utf-8"))):
        url2doc.setdefault(x.get("url"), i)
    doc2rec = {url2doc[x["url"]]: k for k, x in enumerate(data) if x["url"] in url2doc}

    guards = {k: {} for k in range(len(data))}
    with open(labels, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            k = doc2rec.get(int(row["doc_id"]))
            if k is None:
                continue
            v = verdict(row)
            if not_safe(v):
                guards[k][int(row["sent_id"])] = v

    for k, x in enumerate(data):
        x["guardrails"] = [{"sent": i, **v} for i, v in sorted(guards[k].items())]
    json.dump(data, open(src, "w", encoding="utf-8"), ensure_ascii=False)
    n = sum(len(g) for g in guards.values())
    print(f"{n} not-safe sentences in {sum(map(bool, guards.values()))} of {len(data)} records -> {src}")


if __name__ == "__main__":
    main(sys.argv[1:])
