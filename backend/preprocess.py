import os
import sys
import hashlib
from typing import List, Iterable, Tuple, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

def get_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 200) -> "RecursiveCharacterTextSplitter":
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

def _read_text_file(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None

def load_document(path: str) -> Optional[str]:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".txt"}:
        return _read_text_file(path)
    return _read_text_file(path)

def iter_files(root: str, exts: Optional[set] = None) -> Iterable[str]:
    if exts is not None:
        exts = {e.lower() for e in exts}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if exts is None:
                yield path
            else:
                if os.path.splitext(name)[1].lower() in exts:
                    yield path

def batched(iterable: List, n: int) -> Iterable[List]:
    if n <= 0:
        n = 64
    for i in range(0, len(iterable), n):
        yield iterable[i : i + n]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(base_dir, "..", "data"))
    persist_dir = os.path.join(base_dir, "chroma_db")
    os.makedirs(persist_dir, exist_ok=True)

    allow_exts = {".txt"}

    files = sorted(iter_files(data_dir, allow_exts))
    if not files:
        print(f"No documents found under {data_dir}", file=sys.stderr)
        return

    print(f"Found {len(files)} files. Loading and chunking...")

    documents: List[str] = []
    metadatas: List[dict] = []
    ids: List[str] = []

    chunk_size = int(os.environ.get("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "200"))
    text_splitter = get_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for fpath in files:
        text = load_document(fpath)
        if not text or not text.strip():
            continue
        chunks = text_splitter.split_text(text)
        rel_path = os.path.relpath(fpath, data_dir)
        for idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({"source": rel_path, "chunk_index": idx})
            uid = hashlib.md5((rel_path + "::" + str(idx)).encode("utf-8")).hexdigest()
            ids.append(f"{uid}")

    if not documents:
        print("No text content to index.", file=sys.stderr)
        return

    print(f"Prepared {len(documents)} chunks. Initializing Chroma + embeddings...")

    embed_model = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embed_model)

    try:
        client = chromadb.PersistentClient(path=persist_dir)
    except TypeError:
        client = chromadb.Client(settings=chromadb.Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))

    collection_name = os.environ.get("CHROMA_COLLECTION", "documents")
    try:
        collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)
    except TypeError:
        collection = client.get_or_create_collection(name=collection_name)

    if os.environ.get("RESET_COLLECTION", "0") in {"1", "true", "True"}:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
        collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)
        print(f"Reset collection '{collection_name}'.")

    batch_size = int(os.environ.get("BATCH_SIZE", "128"))
    total = len(documents)
    added = 0
    for docs_batch, metas_batch, ids_batch in zip(
        batched(documents, batch_size),
        batched(metadatas, batch_size),
        batched(ids, batch_size),
    ):
        collection.add(documents=docs_batch, metadatas=metas_batch, ids=ids_batch)
        added += len(docs_batch)
        if added % (batch_size * 5) == 0 or added == total:
            print(f"Indexed {added}/{total} chunks...")

    try:
        if hasattr(client, "persist"):
            client.persist()
    except Exception:
        pass

    print(f"Done. Persisted {added} chunks to '{persist_dir}' in collection '{collection_name}' using model '{embed_model}'.")

if __name__ == "__main__":
    main()