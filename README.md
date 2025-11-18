# Mini RAG assistant
## Architecture
- Frontend: Nodejs
- API: Flask
- Vector Store: FAISS (or ChromaDB)
- Embedding Model: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- LLM: [Llama 3.1 Instruct model](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)

## Data Flow
- Query Input from Frontend (can expand to users selecting documents)
- Api call on Flask backend
- Get relevant chunks from RAG using FAISS 
- Add relevant context to the LLM in the prompt itself
- Response will be sent back to the frontend

