import os
from flask import Flask, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import requests

app = Flask(__name__)

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "documents")
EMBEDDING_MODEL = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:8888/api/generate")
LLAMA_MODEL = os.environ.get("LLAMA_MODEL", "llama3.1:8b")

embedder = SentenceTransformer(EMBEDDING_MODEL)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

def _resolve_collection(client, preferred_name: str):
	# Try preferred, then common fallbacks, else create
	try:
		return client.get_collection(name=preferred_name)
	except Exception:
		pass
	for alt in [preferred_name, "documents", "docs_collection"]:
		try:
			return client.get_collection(name=alt)
		except Exception:
			continue
	try:
		return client.get_or_create_collection(name=preferred_name)
	except Exception:
		return None

collection = _resolve_collection(chroma_client, COLLECTION_NAME)

def call_ollama(prompt):
    payload = {
        "model": LLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "No response field in JSON.")
        else:
            return f"Error: Ollama returned status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}. Is it running?"

@app.route('/api/health', methods=['GET'])
def api_health():
	return jsonify({
		"status": "ok",
		"collection_loaded": bool(collection),
		"collection_name": getattr(collection, "name", None),
		"chroma_path": CHROMA_PATH
	})

@app.route('/', methods=['GET'])
def root():
	return jsonify({"ok": True, "try": ["/api/health", "/api/query?query=hello"]})

@app.errorhandler(404)
def not_found(_e):
	return jsonify({"error": "Not Found", "hint": "Check /api/health and /api/query"}), 404

@app.route('/api/query', methods=['POST', 'GET'])
def query_endpoint():
    if not collection:
        return jsonify({"error": "ChromaDB collection not loaded. Run preprocess.py first or check CHROMA_PATH/COLLECTION envs."}), 500

    if request.method == 'GET':
        user_query = request.args.get('query', '').strip()
        n_results = request.args.get('n', os.environ.get("N_RESULTS", "3"))
    else:
        data = request.json or {}
        user_query = (data.get('query') or '').strip()
        n_results = data.get('n_results', os.environ.get("N_RESULTS", "3"))

    if not user_query:
        return jsonify({"error": "No query provided. Supply ?query=... or JSON {'query': '...'}"}), 400

    try:
        n_results = int(n_results)
    except ValueError:
        n_results = 3

    query_embedding = embedder.encode([user_query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )

    retrieved_docs = results['documents'][0] if results.get('documents') else []

    context_text = "\n\n".join(retrieved_docs) if retrieved_docs else "No relevant context found."

    prompt = f"""
    You are a helpful assistant. Use the provided context to answer the question.
    If the answer is not in the context, say you don't know.

    Context:
    {context_text}

    Question:
    {user_query}

    Answer:
    """

    answer = call_ollama(prompt)

    return jsonify({
        "query": user_query,
        "answer": answer,
        "retrieved_context": retrieved_docs,
        "n_results": n_results
    })

if __name__ == '__main__':
    if not os.path.exists(CHROMA_PATH):
        print(f"WARNING: Directory {CHROMA_PATH} not found.")
    
    app.run(host='0.0.0.0', port=5000, debug=True)