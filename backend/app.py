import os
from flask import Flask, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import requests

app = Flask(__name__)

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "docs_collection"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
LLAMA_MODEL = "llama3.1"

embedder = SentenceTransformer(EMBEDDING_MODEL)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
except Exception as e:
    collection = None

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

@app.route('/api/query', methods=['POST'])
def query_endpoint():
    if not collection:
        return jsonify({"error": "ChromaDB collection not loaded."}), 500

    data = request.json
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    query_embedding = embedder.encode([user_query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3
    )

    retrieved_docs = results['documents'][0] if results['documents'] else []
    
    if not retrieved_docs:
        context_text = "No relevant context found."
    else:
        context_text = "\n\n".join(retrieved_docs)

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
        "retrieved_context": retrieved_docs 
    })

if __name__ == '__main__':
    if not os.path.exists(CHROMA_PATH):
        print(f"WARNING: Directory {CHROMA_PATH} not found.")
    
    app.run(host='0.0.0.0', port=5000, debug=True)