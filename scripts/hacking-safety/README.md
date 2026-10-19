# Hacking safety scripts

Generate the `hacking-safety/` section of the site from the hacking safety dataset.
The data files are not in this repository.

- `add_guardrails.py` — attaches guardrail verdicts (Llama Guard, MD-Judge, Qwen3Guard)
  from [`guardrails/merged_labels.jsonl`](https://github.com/marcostranisci/Epistemic-Injustice-in-LLM/blob/main/guardrails/merged_labels.jsonl)
  to `hacking_safety.json` (records are matched to `16_baseline.json` by URL).
  A sentence is "not safe" if any guard did not rate it safe, Qwen "controversial" included.
- `render_posts.py` — standalone HTML pages for every record (local browsing);
  also provides the post-body rendering used by `build_site.py`.
- `build_site.py` — writes `hacking-safety/` (index, one page per post, random redirect)
  using the header/footer of `about.html`. By default only posts with at most 35% of
  their sentences flagged are published; `--all` publishes every post.

From the folder holding the data:

```bash
python add_guardrails.py merged_labels.jsonl 16_baseline.json hacking_safety.json
python build_site.py path/to/disharm-project.github.io hacking_safety.json   # add --all to skip the filter
```
