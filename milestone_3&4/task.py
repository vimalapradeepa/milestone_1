import os
import math
import json
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request


PAGES_DIR = "pages"
INDEX_PATH = "inverted_index.json"
IDF_PATH = "idf.json"


# -----------------------------
# Extract clean text from HTML
# -----------------------------
def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return " ".join(text.split()).lower()


# -----------------------------
# Tokenize
# -----------------------------
def tokenize(text):
    word = ""
    tokens = []

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
# Build index (runs once)
# -----------------------------
def build_index():
    print("\n Reading HTML files from pages/ ...\n")

    documents = {}
    tf_docs = {}

    for filename in os.listdir(PAGES_DIR):
        if not filename.endswith(".html"):
            continue

        path = os.path.join(PAGES_DIR, filename)

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        text = extract_text(html)
        tokens = tokenize(text)

        documents[filename] = tokens
        tf_docs[filename] = Counter(tokens)

    print(f" Loaded {len(documents)} documents")

    inverted_index = defaultdict(list)

    for doc, tf in tf_docs.items():
        for word, freq in tf.items():
            inverted_index[word].append((doc, freq))

    idf = {}
    N = len(documents)

    for word, postings in inverted_index.items():
        df = len(postings)
        idf[word] = math.log10(N / (1 + df))

    with open(INDEX_PATH, "w") as f:
        json.dump(inverted_index, f, indent=2)

    with open(IDF_PATH, "w") as f:
        json.dump(idf, f, indent=2)

    print("\n Index created successfully")
    print(" inverted_index.json")
    print(" idf.json\n")


# -----------------------------
# Load index from disk
# -----------------------------
def load_index():
    with open(INDEX_PATH) as f:
        index = json.load(f)

    with open(IDF_PATH) as f:
        idf = json.load(f)

    return index, idf


# -----------------------------
# Search (TF-IDF)
# -----------------------------
def search(query, index, idf, top_k=5):
    scores = {}
    tokens = tokenize(query)

    for word in tokens:
        if word not in index:
            continue

        for doc, tf in index[word]:
            score = tf * idf.get(word, 0)
            scores[doc] = scores.get(doc, 0) + score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]


# -----------------------------
# Flask UI Template
# -----------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>WebScour Search Engine</title>
<style>
body { font-family: Arial; background:#eef3f6 }
.container { width:700px; margin:60px auto; background:white; padding:25px; border-radius:8px }
input { width:80%; padding:10px }
button { padding:10px 18px }
</style>
</head>
<body>
<div class="container">
<h2>🔍 WebScour Search Engine</h2>

<form method="POST">
<input name="query" value="{{query}}" placeholder="search..." required>
<button type="submit">Search</button>
</form>

{% if results %}
<h3>Results</h3>
<ul>
{% for doc,score in results %}
<li>{{doc}} — Score: {{ "%.4f"|format(score) }}</li>
{% endfor %}
</ul>
{% endif %}

</div>
</body>
</html>
"""


# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

# Build index ONLY IF NOT ALREADY CREATED
if not (os.path.exists(INDEX_PATH) and os.path.exists(IDF_PATH)):
    build_index()

# Load index once
inverted_index, idf = load_index()


@app.route("/", methods=["GET", "POST"])
def home():
    query = ""
    results = []

    if request.method == "POST":
        query = request.form["query"]
        results = search(query, inverted_index, idf)

    return render_template_string(HTML_PAGE, query=query, results=results)


# -----------------------------
# Start server (no reload loop)
# -----------------------------
if __name__ == "__main__":
    print("\n Starting WebScour Search Engine...")
    print(" Open in browser: http://127.0.0.1:5000\n")

    app.run(debug=False)
