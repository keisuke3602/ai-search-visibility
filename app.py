from flask import Flask, request, render_template_string, redirect, url_for
import pandas as pd
import os, json, datetime
from dotenv import load_dotenv

# ==========================================================================

from chatgpt_visibility.py import (
    ensure_client, query_openai_one, parse_model_output, detect_brands
)

load_dotenv()
app = Flask(__name__)

# ==========================================================================

DEFAULT_JSONL = "data/runs/web_ui.jsonl"
os.makedirs(os.path.dirname(DEFAULT_JSONL), exist_ok=True)

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>AI Search Visibility – Runner</title>
    <link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  </head>
  <body class="p-4">
    <div class="container">
      <h1 class="mb-3">AI Search Visibility – Runner</h1>
      <form method="post" class="mb-4">
        <div class="mb-3">
          <label class="form-label">Prompts (1 line = 1 prompt, up to ~5 lines)</label>
          <textarea name="prompts" rows="8" class="form-control"
            placeholder="What services allow you to share highlights of web pages?
Which apps can import highlights from Instapaper?">{{ prompts or "" }}</textarea>
        </div>

        <div class="row g-3">
          <div class="col-md-3">
            <label class="form-label">Per-Query Runs</label>
            <input type="number" class="form-control" name="runs" min="1" max="50"
                   value="{{ runs or 3 }}">
          </div>
          <div class="col-md-3">
            <label class="form-label">Temperature</label>
            <input type="number" step="0.1" class="form-control" name="temperature"
                   value="{{ temperature or 0.7 }}">
          </div>
          <div class="col-md-6">
            <label class="form-label">JSONL Output Path</label>
            <input type="text" class="form-control" name="jsonl_path"
                   value="{{ jsonl_path or 'data/runs/web_ui.jsonl' }}">
          </div>
        </div>

        <div class="mt-3">
          <button class="btn btn-primary" type="submit">Run</button>
          <a class="btn btn-outline-secondary" href="{{ url_for('index') }}">Reset</a>
        </div>
      </form>

      {% if summary %}
        <h3 class="mt-4">Summary (brand hit-rate per prompt)</h3>
        <table class="table table-striped">
          <thead>
            <tr><th>#</th><th>Prompt</th>
              {% for b in brands %}<th>{{ b }}</th>{% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in summary %}
              <tr>
                <td>{{ loop.index }}</td>
                <td style="max-width:520px">{{ row.prompt }}</td>
                {% for b in brands %}
                  <td>{{ "%.2f"|format(row.hitrate.get(b, 0.0)) }}</td>
                {% endfor %}
              </tr>
            {% endfor %}
          </tbody>
        </table>

        <div class="alert alert-info">
          Saved <strong>{{ total_records }}</strong> runs to
          <code>{{ jsonl_path }}</code>.
        </div>
      {% endif %}
    </div>
  </body>
</html>
"""

BRANDS = [
    "glasp", "hypothesis", "notion", "evernote", "weava",
    "diigo", "mem", "web highlights", "readwise", "raindrop"
]


def append_jsonl(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML, brands=BRANDS)
    
    prompts_raw = request.form.get("prompts", "")
    runs = int(request.form.get("runs", "3") or 3)
    temperature = float(request.form.get("temperature", "0.7") or 0.7)
    jsonl_path = request.form.get("jsonl_path", DEFAULT_JSONL) or DEFAULT_JSONL

    prompts = [ln.strip() for ln in prompts_raw.splitlines() if ln.strip()]

    if not prompts:
        return render_template_string(
            HTML, brands=BRANDS, prompts=prompts_raw, runs=runs,
            temperature=temperature, jsonl_path=jsonl_path
        )

    client = ensure_client()
    total_records = 0
    per_prompt_hits = []

    for prompt_text in prompts:
        counts = {b: 0 for b in BRANDS}
        n = 0

        for run_idx in range(runs):
            raw = query_openai_one(client, prompt_text)
            parsed = parse_model_output(raw)
            brands_detected = detect_brands(parsed["answer"], [s["URL"] for s in parsed["sources"]])

            rec = {
                "ts": datetime.datetime.now().isoformat(),
                "prompt": prompt_text,
                "run_index": run_idx,
                "model": "gpt-4o-mini",
                "temperature": temperature,
                "answer": parsed["answer"],
                "sources": [s["URL"] for s in parsed["sources"]],
                "brands": brands_detected
            }
            append_jsonl(jsonl_path, rec)
            total_records += 1
            n += 1

            for b, hit in brands_detected.items():
                if b in counts:
                    counts[b] += int(bool(hit))
        
        hitrate = {b: (counts[b] / n if n > 0 else 0.0) for b in BRANDS}
        per_prompt_hits.append({"prompt": prompt_text, "hitrate": hitrate})
    
    return render_template_string(
        HTML,
        brands=BRANDS,
        prompts="\n".join(prompts),
        runs=runs,
        temperature=temperature,
        jsonl_path=jsonl_path,
        summary=per_prompt_hits,
        total_records=total_records
    )

if __name__ == "__main__":
    app.run(debug=True)