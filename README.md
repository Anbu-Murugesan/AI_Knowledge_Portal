# Internal AI Knowledge Portal

A comprehensive AI-powered knowledge portal that aggregates and searches through AI/ML news, blogs, research papers, and events (hackathons, conferences, workshops).

## Features

- **💬 Chat Interface**: Search AI news and blog articles with intelligent summarization
- **📄 Research Papers**: Search and retrieve papers from arXiv with AI-powered summaries
- **🎯 Events**: Browse AI/ML hackathons, conferences, and workshops
- **🔄 Auto-Rebuild**: Automatic vector store rebuilding every 7 days
- **📊 Comprehensive Logging**: Detailed logs for debugging and monitoring

## Architecture

- **Frontend**: Streamlit web application
- **Vector Store**: FAISS for semantic search
- **LLM**: Groq API for summarization
- **Web Search**: Tavily API for event discovery

## Quick Start

### Prerequisites

**Required:**
- Python 3.11+ (tested with 3.11)
- API Keys:
  - Groq API key (for LLM operations)
  - Tavily API key (for event discovery)

**Optional (for containerized deployment only):**
- Docker or Podman (both are containerization tools - choose one if you want to run in containers)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI_Intelligence_Knowledge_Hub
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start frontend**
   ```bash
   streamlit run app.py
   ```

5. **Access the application**
   - Frontend: http://localhost:8501

## Project Structure

```
AI_Intelligence_Knowledge_Hub/
├── app.py                 # Streamlit frontend entry point
├── core/                  # Core functionality
│   ├── workflows/         # Main workflow logic
│   ├── vector_store/      # FAISS vector store management
│   ├── llm/              # LLM integration
│   ├── blog_crawlers/     # Blog crawlers for different sources
│   ├── rss/              # RSS feed processing
│   ├── text_processing/   # Text processing utilities
│   ├── rebuild_manager.py # Auto-rebuild logic
│   └── logging_config.py  # Logging configuration
├── ui/                    # Frontend UI components
│   ├── tabs/             # Tab implementations (chat, research, events)
│   └── api_client.py     # Direct function client (no backend API)
├── events/                # Event collection (hackathons, conferences, workshops)
├── research/              # Research paper retrieval from arXiv
├── logs/                  # Application logs
├── Dockerfile             # Dockerfile for containerized deployment
├── .env.example           # Environment variables template
└── requirements.txt       # Python dependencies
```

## Configuration

### Environment Variables

See `.env.example` for all required variables:

- `GROQ_API_KEY`: Groq API key for LLM operations
- `TAVILY_API_KEY`: Tavily API key for web search

### Vector Stores

The application uses FAISS vector stores for semantic search:
- `faiss_index_local/`: RSS feed articles
- `kdnuggets_faiss/`: KDnuggets blog articles
- `faiss_blogs/`: Other blog sources (Analytics Vidhya, ML Mastery)

Vector stores are automatically rebuilt every 7 days.

## API Usage Notes

This application relies on external APIs:

- **Groq API** – Used for LLM summarization
- **Tavily API** – Used for discovering AI-related events

Be aware of:
- API rate limits
- Usage quotas depending on your API plan

## Logging

All logs are written to the `logs/` directory:
- `logs/frontend.log`: Frontend application logs
- `logs/rebuild.log`: Vector store rebuild logs
- `logs/errors.log`: Error logs (aggregated)

## Deployment

### Production Deployment

1. Set up environment variables securely
2. Build and run the Docker/Podman container with appropriate resource limits
3. Set up reverse proxy (nginx/traefik) for HTTPS
4. Configure log rotation
5. Set up monitoring and alerting

## Troubleshooting

### Application not starting
- Check logs: `logs/frontend.log` (local) or `podman logs <container-name>` / `docker logs <container-name>` (containerized)
- Verify environment variables are set correctly
- Check port 8501 availability
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Vector stores not found
- Vector stores are built automatically on first use when `build_if_missing=True`
- Check `rebuild_status.json` for rebuild status
- Manual rebuild: Trigger from UI footer or set `build_if_missing=True` in workflow

### Getting fewer results than expected
- Check retriever configuration in `core/workflows/__init__.py` (default `k=6`)
- Verify vector stores are properly indexed
- Check logs for retrieval errors

## Support

For issues and questions, check:
1. Logs in `logs/` directory:
   - `logs/frontend.log` - Application logs
   - `logs/rebuild.log` - Vector store rebuild logs
   - `logs/errors.log` - Error logs
2. Container logs: `podman logs <container-name>` or `docker logs <container-name>` (if using containers)
3. Streamlit health endpoint: `http://localhost:8501/_stcore/health`
4. Verify environment variables are correctly set in `.env` file

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key_here
export TAVILY_API_KEY=your_key_here

# Run the application
streamlit run app.py
```

### Building and Running with Docker/Podman

```bash
# Build the image
docker build -t ai-knowledge-hub .
# Or with Podman:
podman build -t ai-knowledge-hub .

# Run the container (simple - without volume mounts)
docker run -d \
  --name ai-knowledge-hub \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  ai-knowledge-hub

# Or with Podman (simple - without volume mounts):
podman run -d \
  --name ai-knowledge-hub \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  ai-knowledge-hub

# Run the container (with volume mounts for data persistence)
docker run -d \
  --name ai-knowledge-hub \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/faiss_index_local:/app/faiss_index_local \
  -v $(pwd)/kdnuggets_faiss:/app/kdnuggets_faiss \
  -v $(pwd)/faiss_blogs:/app/faiss_blogs \
  -v $(pwd)/events_cache.json:/app/events_cache.json \
  -v $(pwd)/rebuild_status.json:/app/rebuild_status.json \
  ai-knowledge-hub

# Or with Podman (with volume mounts for data persistence):
podman run -d \
  --name ai-knowledge-hub \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/faiss_index_local:/app/faiss_index_local \
  -v $(pwd)/kdnuggets_faiss:/app/kdnuggets_faiss \
  -v $(pwd)/faiss_blogs:/app/faiss_blogs \
  -v $(pwd)/events_cache.json:/app/events_cache.json \
  -v $(pwd)/rebuild_status.json:/app/rebuild_status.json \
  ai-knowledge-hub

# View logs
docker logs -f ai-knowledge-hub
# Or with Podman:
podman logs -f ai-knowledge-hub
```

## Notes

Thank you for using the Internal AI Knowledge Portal.

If you have any questions regarding setup, deployment, or usage, please feel free to reach out.