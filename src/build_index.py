"""
Tool 3: Document Q&A bot (step 1 of 2) - build the search index.
Splits company documents into chunks, turns each chunk into an embedding
(a list of numbers that captures its meaning), and saves them to a file.
"""
import os
import json
import glob
from dotenv import load_dotenv
from google import genai
from llm_client import with_retry

load_dotenv()
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-2")
DOCS_DIR = "docs"
INDEX_PATH = "data/doc_index.json"

client = genai.Client()


def split_into_chunks(path):
    """Split a markdown document into one chunk per '## ' section."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    doc_title = text.splitlines()[0].lstrip("# ").strip()
    chunks = []
    for section in text.split("\n## ")[1:]:
        heading, _, body = section.partition("\n")
        chunks.append({
            "source": os.path.basename(path),
            "section": heading.strip(),
            "text": f"{doc_title} - {heading.strip()}\n{body.strip()}",
        })
    return chunks


def embed(text, is_query=False):
    """Turn text into an embedding vector using Gemini."""
    prefix = "task: question answering | query: " if is_query else "title: none | text: "
    result = with_retry(
        lambda: client.models.embed_content(model=EMBED_MODEL, contents=prefix + text)
    )
    return result.embeddings[0].values


if __name__ == "__main__":
    all_chunks = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        chunks = split_into_chunks(path)
        print(f"{os.path.basename(path)}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\nEmbedding {len(all_chunks)} chunks with {EMBED_MODEL}...")
    for chunk in all_chunks:
        chunk["embedding"] = list(embed(chunk["text"]))

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f)
    print(f"Saved index to {INDEX_PATH} ({len(all_chunks[0]['embedding'])} numbers per chunk)")