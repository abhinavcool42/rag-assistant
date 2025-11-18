# Mini RAG assistant
## Architecture
- Frontend: HTML, CSS, JavaScript
- API: Flask
- Vector Store: ChromaDB
- Embedding Model: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- LLM: [Llama 3.1 Instruct model](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) (served via Ollama)

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
  - Load: read `.txt` files from the `data/` directory.
  - Split: chunk the documents (using `langchain_text_splitters`)
  - Embed: use `all-MiniLM-L6-v2` to turn chunks into vectors
  - Store: save them all into your ChromaDB

## Setup

1.  **Clone the repository**

2.  **Backend Setup**
    - Navigate to the `backend` directory: `cd backend`
    - Install Python dependencies: `pip install -r requirements.txt`
    - **Set up Ollama**: Make sure you have Ollama running and have pulled the Llama 3.1 model:
      ```sh
      ollama pull llama3.1:8b
      ```
    - **Add Documents**: Place your `.txt` files into the `data/` directory.
    - **Run Ingestion**: Run the preprocessing script to build the vector database.
      ```sh
      python preprocess.py
      ```

## Running the Application

1.  **Start the Backend Server**:
    - From the `backend` directory, run:
      ```sh
      flask run
      ```
    - The API will be available at `http://127.0.0.1:5000`.

2.  **Open the Frontend**:
    - Open the `frontend/index.html` file in your web browser.
    - You can now ask questions through the interface.

## Additional features to implement
- More document formats (excel, word, json, csv etc)
- Web scraping
- Streaming answer
- Allowing Users to submit documents
- Chat history
- Reranking Model

## API endpoints
- `GET /api/health`
  - Description: Checks the health of the backend service and ChromaDB connection.
- `POST /api/query` (also supports `GET`)
  - Description: Submits a query to the RAG assistant.
  - Body: `{"query": "What is the project objective?", "n_results": 3}`

## Challenges and Learnings

### 1. CORS (Cross-Origin Resource Sharing) Errors
- **Challenge**: The frontend JavaScript, served from a `file://` protocol, was blocked from making requests to the Flask backend API (`http://127.0.0.1:5000`) due to browser security policies.
- **Resolution**: The `flask-cors` extension was added to the Flask application to explicitly allow requests from any origin (`*`) to the `/api/*` routes. This is a common and necessary step for web applications where the frontend and backend are served from different origins.

### 2. Vector Database Initialization and Access
- **Challenge**: Ensuring the ChromaDB collection was created by the `preprocess.py` script and then correctly accessed by the `app.py` server without crashing if the database didn't exist.
- **Resolution**:
  - A persistent ChromaDB client was used, storing the database on disk.
  - The `app.py` includes a health check endpoint (`/api/health`) and a robust `_resolve_collection` function that gracefully handles cases where the collection might not be immediately found, preventing the app from failing on startup.
  - Clear instructions were added to run the ingestion script before starting the server.

### 3. Efficient Document Processing
- **Challenge**: Processing large documents could be memory-intensive and slow, especially when adding thousands of chunks to the vector database.
- **Resolution**: The `preprocess.py` script was designed to handle this efficiently by:
  - Using a `batched` function to add documents, metadatas, and IDs to ChromaDB in manageable chunks, reducing memory overhead.
  - Generating deterministic MD5-based IDs for each chunk, which allows for idempotent updates and prevents duplication.

### 4. LLM Integration and Prompting
- **Challenge**: Getting the LLM to reliably use the provided context and avoid hallucinating answers.
- **Resolution**: A structured prompt was engineered in `app.py`. It clearly delineates the `Context` and the `Question`, and explicitly instructs the model to state "I don't know" if the answer is not found in the context. This significantly improves the factuality of the responses.

### Key Learnings
- **Modularity**: Separating the data ingestion (`preprocess.py`) from the serving API (`app.py`) is a clean architecture. It keeps the API lightweight and focused on querying.
- **Configuration**: Using environment variables for critical settings (model names, paths, URLs) makes the application flexible and easy to deploy in different environments without code changes.
- **Error Handling**: Providing clear error messages from the backend (e.g., "ChromaDB collection not loaded") and handling them on the frontend is essential for debugging and usability.

## Requirements
- Python 3.11
- Ollama
