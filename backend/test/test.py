import os
import sys
import chromadb
from chromadb.utils import embedding_functions

def open_client(persist_dir: str):
	if not os.path.isdir(persist_dir):
		print(f"Chroma persist dir not found: {persist_dir}", file=sys.stderr)
		sys.exit(1)
	try:
		return chromadb.PersistentClient(path=persist_dir)
	except TypeError:
		# Older versions fallback
		return chromadb.Client(
			settings=chromadb.Settings(
				chroma_db_impl="duckdb+parquet",
				persist_directory=persist_dir
			)
		)

def get_collection_safe(client, name: str, embedding_fn):
	# Prefer get_collection to avoid creating empty collections by accident
	try:
		return client.get_collection(name=name, embedding_function=embedding_fn)
	except Exception:
		# Fallback: check list and then get_or_create
		try:
			names = {c.name for c in client.list_collections()}
			if name in names:
				return client.get_collection(name=name, embedding_function=embedding_fn)
		except Exception:
			pass
		return client.get_or_create_collection(name=name, embedding_function=embedding_fn)

def check_persisted_collection(client, collection_name: str, embedding_fn) -> bool:
	col = get_collection_safe(client, collection_name, embedding_fn)
	count = 0
	try:
		count = col.count()
	except Exception as e:
		print(f"Failed to read collection count: {e}", file=sys.stderr)
		return False

	print(f"Collection '{collection_name}' contains {count} chunks.")
	if count == 0:
		return False

	# Run a small query to validate retrieval
	try:
		q = "Test query about common topics."
		res = col.query(query_texts=[q], n_results=3)
		top_docs = (res.get("documents") or [[]])[0]
		top_ids = (res.get("ids") or [[]])[0]
		print("Top result ID:", top_ids[0] if top_ids else "N/A")
		print("Top snippet:", (top_docs[0][:200] + "...") if top_docs else "N/A")
		return True
	except Exception as e:
		print(f"Query failed: {e}", file=sys.stderr)
		return False

def smoke_test_new_collection(client, embedding_fn):
	name = "__smoke_test__"
	try:
		col = client.get_or_create_collection(name=name, embedding_function=embedding_fn)
		col.add(
			documents=[
				"Paris is the capital of France.",
				"Berlin is the capital of Germany.",
				"Madrid is the capital of Spain."
			],
			metadatas=[{"city": "Paris"}, {"city": "Berlin"}, {"city": "Madrid"}],
			ids=["p1", "b1", "m1"],
		)
		ok = col.count() == 3
		res = col.query(query_texts=["What is the capital of France?"], n_results=1)
		top = (res.get("documents") or [[]])[0]
		print("Smoke test top snippet:", (top[0] if top else "N/A"))
		return ok and bool(top) and "Paris" in top[0]
	finally:
		try:
			client.delete_collection(name)
		except Exception:
			pass

def main():
	# Paths and settings aligned with preprocess.py
	test_dir = os.path.dirname(os.path.abspath(__file__))
	backend_dir = os.path.dirname(test_dir)
	persist_dir = os.path.join(backend_dir, "chroma_db")
	collection_name = os.environ.get("CHROMA_COLLECTION", "documents")
	embed_model = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")

	client = open_client(persist_dir)
	embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embed_model)

	ok = check_persisted_collection(client, collection_name, embedding_fn)
	if not ok:
		print("Persisted collection empty or unavailable. Running smoke test...")
		ok = smoke_test_new_collection(client, embedding_fn)

	if not ok:
		print("ChromaDB test failed.", file=sys.stderr)
		sys.exit(1)

	print("ChromaDB test passed.")

if __name__ == "__main__":
	main()
