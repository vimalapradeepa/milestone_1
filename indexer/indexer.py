import os
import math
import json
from collections import defaultdict, Counter
from bs4 import BeautifulSoup

PAGES_DIR = "pages"

# -----------------------------
# Extract visible text
# -----------------------------
def extract_visible_text(html):
    soup = BeautifulSoup(html, "lxml")

    # remove scripts & styles
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = " ".join(text.split())
    return text.lower()


# -----------------------------
# Tokenizer
# -----------------------------
def tokenize(text):
    tokens = []
    word = ""

    for ch in text:
        if ch.isalnum():
            word += ch
        else:
            if word:
                tokens.append(word)
                word = ""
    if word:
        tokens.append(word)

    return tokens


# -----------------------------
# Read HTML files + compute TF
# -----------------------------
documents = {}
tf_per_document = {}

print("\n Reading HTML files...\n")

for filename in os.listdir(PAGES_DIR):

    if not filename.endswith(".html"):
        continue

    path = os.path.join(PAGES_DIR, filename)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    text = extract_visible_text(html)
    tokens = tokenize(text)

    documents[filename] = tokens
    tf_per_document[filename] = Counter(tokens)

print(f"Loaded {len(documents)} documents")


# -----------------------------
# Build Inverted Index
# -----------------------------
inverted_index = defaultdict(list)

for doc_id, tf_dict in tf_per_document.items():
    for word, freq in tf_dict.items():
        inverted_index[word].append((doc_id, freq))


# -----------------------------
# Compute IDF values
# -----------------------------
idf = {}
N = len(documents)

for word, postings in inverted_index.items():
    df = len(postings)
    idf[word] = math.log10(N / (1 + df))


# -----------------------------
# Save Output
# -----------------------------
os.makedirs("indexer", exist_ok=True)

with open("indexer/inverted_index.json", "w") as f:
    json.dump(inverted_index, f, indent=2)

with open("indexer/idf.json", "w") as f:
    json.dump(idf, f, indent=2)

print("\n Indexing complete!")
print("inverted_index.json generated")
print("idf.json generated")
