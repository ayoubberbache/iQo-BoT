"""Optional: pull ONE small public text file from Hugging Face into knowledge/ for retrieval.
Capped and filtered; review the output (some datasets are LLM-generated).
  python ingest_hf.py --repo CJJones/LLM_Electrical_Engineering_Educational_Synthetic_Dialog --file circuit_conversations_Sample.txt"""
import argparse, os, re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", default=os.path.join("knowledge", "ingested.md"))
    ap.add_argument("--max-chunks", type=int, default=3000)
    a = ap.parse_args()
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(a.repo, a.file, repo_type="dataset")
    text = open(path, encoding="utf-8", errors="ignore").read()
    chunks, seen = [], set()
    for c in re.split(r"\n\s*\n", text):
        c = " ".join(c.split())
        if 25 <= len(c.split()) <= 160 and c not in seen:
            seen.add(c)
            chunks.append(c)
        if len(chunks) >= a.max_chunks:
            break
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n\n".join(chunks))
    print(f"wrote {len(chunks)} chunks to {a.out}")


if __name__ == "__main__":
    main()
