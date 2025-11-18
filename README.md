# Mini RAG assistant
## Architecture
- Frontend: Nodejs
- API: Flask
- Vector Store: ChromaDB
- Embedding Model: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- LLM: [Llama 3.1 Instruct model](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)

## Data Flow
- Query Input from Frontend (can expand to users selecting documents)
- Recieve query on Flask backend API
- Query is embedded
- Get relevant chunks from RAG using ChromaDB 
- Add relevant context to the LLM in the prompt itself and build it
- Call the LLM model with the prompt
- Send the final answer to Frontend

## Ingestion/Preprocessing
- Script for preprocessing documents and building the vector database
  - Load: read the PDFs, TXT, etc. (using PyPDFLoader)
  - Split: chunk the documents (using LangChain)
  - Embed: use all-MiniLM-L6-v2 to turn chunks into vectors
  - Store: save them all into your ChromaDB

## Additional features to implement
- More document formats (excel, word, json, csv etc)
- Web scraping
- Streaming answer
- Allowing Users to submit documents
- Chat history
- Reranking Model

## API endpoints
- ```POST /api/query```
  - Description: Submits a query to the RAG assistant
  - Body: ```{"query": "What is the project objective?"}```

## Requirements
- Python 3.11
