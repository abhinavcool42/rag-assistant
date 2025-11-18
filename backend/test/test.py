import os
import sys
import chromadb
from chromadb.utils import embedding_functions

def open_client(persist_dir: str):
	if not os.path.isdir(persist_dir):
		print(f"Chroma persist dir not found: {persist_dir}", file=sys.stderr)
		sys.exit(1)
		return chromadb.PersistentClient(path=persist_dir)

def _print_results(res: dict):
	doc_lists = res.get("documents") or []
	id_lists = res.get("ids") or []
	meta_lists = res.get("metadatas") or []
	dist_lists = res.get("distances") or []
	if not doc_lists:
		print("No results.")
		return
	docs = doc_lists[0]
	ids = id_lists[0]
	metas = meta_lists[0] if meta_lists else [{}] * len(docs)
	dists = dist_lists[0] if dist_lists else [None] * len(docs)
	for i, (doc, _id, meta, dist) in enumerate(zip(docs, ids, metas, dists), start=1):
		snippet = (doc[:200] + ("..." if len(doc) > 200 else ""))
		print(f"[{i}] id={_id} distance={dist:.4f}" if dist is not None else f"[{i}] id={_id}")
		if meta:
			print(f"    metadata: {meta}")
		print(f"    snippet: {snippet}")

def main():
	backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	persist_dir = os.path.join(backend_dir, "chroma_db")
	collection_name = os.environ.get("CHROMA_COLLECTION", "documents")
	embed_model = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")

	client = open_client(persist_dir)
	embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embed_model)

	try:
		collection = client.get_collection(name=collection_name, embedding_function=embedding_fn)
	except Exception:
		collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)

	try:
		count = collection.count()
	except Exception as e:
		print(f"Failed to read collection: {e}", file=sys.stderr)
		sys.exit(1)

	print(f"Loaded collection '{collection_name}' (model '{embed_model}') with {count} chunks.")
	if count == 0:
		print("Collection empty. Run preprocess.py first.")
		sys.exit(0)

	while True:
		query = input("\nEnter query (blank to exit): ").strip()
		if not query:
			print("Exit.")
			break
		try:
			res = collection.query(query_texts=[query], n_results=int(os.environ.get("N_RESULTS", "5")))
			_print_results(res)
		except Exception as e:
			print(f"Query error: {e}", file=sys.stderr)

if __name__ == "__main__":
	main()
