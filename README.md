# **TheLab – Crisis & Resilience AI**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**TheLab** is a comprehensive AI-powered platform for crisis planning and resilience engineering, specifically designed for small islands, coastal territories, and fragile states. It integrates advanced AI models, geospatial tools, satellite imagery analysis, social media monitoring, and disaster recovery frameworks to provide strategic planning and real-time insights for crisis management.

## 🌟 Overview

TheLab combines multiple technologies to deliver an intelligent assistant for:
- **Post-disaster damage assessment** and impact mapping
- **Multi-sector resilience engineering** and infrastructure recovery
- **Critical infrastructure prioritization** (power, water, health, telecom, transport)
- **Humanitarian logistics** and supply-chain restoration
- **GIS-informed planning** and geospatial reasoning
- **Climate risk modeling** and long-term adaptation
- **Economic and financial reconstruction** strategies
- **Community resilience** and social welfare analysis

The platform leverages Retrieval-Augmented Generation (RAG), large language models (LLMs), and specialized tools to provide context-aware responses based on local documents, real-time data, and expert knowledge.

## 🚀 Key Features

- **AI-Powered Chat Interface**: Interactive conversation with advanced reasoning models (Mistral, Claude)
- **Geospatial Analysis**: Integration with OpenStreetMap, climate data, and satellite imagery
- **Vector Database**: Qdrant-powered semantic search over disaster recovery documents
- **MCP Server**: Model Context Protocol for tool integration
- **Satellite Imagery Processing**: ML-based vulnerability assessment and change detection
- **Social Media Monitoring**: Real-time analysis of crisis-related social media data
- **WhatsApp Integration**: Direct communication channels for field updates
- **Automated Pipelines**: Docker-based deployment for easy scaling
- **Cloud and Local Deployment**: Flexible hosting options

## 🏗️ Architecture

TheLab follows a modular microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI       │    │   MCP Server    │
│   (Frontend)    │◄──►│   Backend       │◄──►│   (Tools)       │
│                 │    │   (RAG + LLM)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Qdrant        │    │   External APIs │    │   Satellite     │
│   Vector DB     │    │   (Climate, OSM)│    │   Imagery ML    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                            ┌─────────────────┐
                                            │   Social Media  │
                                            │   Analysis      │
                                            └─────────────────┘
```

### Core Components:
- **Frontend**: Streamlit-based chat interface
- **Backend**: FastAPI with LangGraph for agent orchestration
- **Vector Store**: Qdrant for document embeddings and retrieval
- **LLMs**: Mistral for reasoning, Claude for synthesis
- **Tools**: Climate forecasting, OSM data, Earth Engine integration
- **Data Processing**: Satellite imagery ML pipelines, social media streams

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- API keys for external services (Qdrant, Anthropic, Mistral, etc.)

## 🛠️ Setup and Installation

### Quick Start with Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd TheLab_resilienceai
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Launch the entire stack**:
   ```bash
   docker compose up --build
   ```

   This starts all services automatically:
   - **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
   - **FastAPI Backend**: [http://localhost:8080](http://localhost:8080)
   - **Qdrant Vector DB**: [http://localhost:6333](http://localhost:6333)
   - **MCP Server**: [http://localhost:8000](http://localhost:8000)

### Manual Setup (Development)

1. **Install dependencies**:
   ```bash
   # Backend
   cd app
   pip install -r requirements.txt

   # Frontend
   cd ../front
   pip install -r requirements.txt

   # MCP Server
   cd ../mcp_server
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   export QDRANT_URL="your-qdrant-url"
   export QDRANT_API_KEY="your-qdrant-api-key"
   export CLAUDE_API_KEY="your-claude-key"
   export MISTRAL_API_KEY="your-mistral-key"
   # ... other required keys
   ```

3. **Build vectorstore** (if needed):
   ```bash
   cd app
   python build_vectorstore.py
   ```

4. **Run services**:
   ```bash
   # Terminal 1: FastAPI backend
   uvicorn main:app --reload --port 8080

   # Terminal 2: Streamlit frontend
   cd front
   streamlit run demo.py

   # Terminal 3: MCP Server
   cd mcp_server
   python main.py
   ```

## 📁 Directory Structure

```
TheLab_resilienceai/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Main application container
├── README.md                   # This file
├── additional_docs/            # Research papers and reports on disaster recovery
│   ├── coastal_processes_JMSE_2019.pdf
│   ├── Disaster Recovery Guidance Series-*.pdf
│   └── ... (various PDF documents)
├── app/                        # FastAPI backend application
│   ├── main.py                 # Main FastAPI app with LangGraph agents
│   ├── build_vectorstore.py    # Vectorstore builder for Qdrant
│   ├── requirements.txt        # Python dependencies
│   ├── start.sh                # Startup script
│   ├── docs/                   # Source documents for RAG
│   ├── models/                 # Local ML models
│   └── tools/                  # Custom tools (climate, OSM)
├── config/                     # Configuration files
│   └── .cdsapirc               # CDS API credentials
├── docs/                       # Generated geodata and exports
├── exports/                    # Exported results and reports
├── front/                      # Streamlit frontend
│   ├── demo.py                 # Main Streamlit app
│   └── requirements.txt        # Frontend dependencies
├── mcp_server/                # Model Context Protocol server
│   ├── main.py                 # MCP server with tool registration
│   ├── requirements.txt        # MCP dependencies
│   ├── Dockerfile              # MCP container
│   ├── docs/                   # MCP documentation
│   └── tools/                  # MCP-compatible tools
├── models/                     # Pre-trained ML models
│   └── all-MiniLM-L6-v2/       # Sentence transformer model
├── pages/                      # Additional Streamlit pages
├── satellite_imagery/          # Satellite image processing pipeline
│   ├── ml_training_inference.py # ML model for disaster assessment
│   ├── change_vulnerability_features.py
│   ├── display_in_gee_map.py
│   ├── export_training_chips.py
│   ├── preprocess_vizualisation.py
│   ├── requirements.txt
│   └── cache/                  # Cached satellite data
├── social_media/               # Social media analysis tools
│   ├── data/                   # Social media datasets
│   └── kafka/                  # Kafka integration for streaming
├── tests/                      # Unit and integration tests
│   ├── test_climate.py
│   ├── test_earth_engine.py
│   ├── test_osm.py
│   └── docs/
└── whatsapp_server/           # WhatsApp integration server
```

## 🔧 Usage

### Chat Interface

1. Open the Streamlit UI at [http://localhost:8501](http://localhost:8501)
2. Ask questions about crisis planning, resilience strategies, or specific disaster scenarios
3. The AI will provide structured responses based on:
   - Retrieved documents from the vector store
   - Real-time tool calls (climate data, geospatial info)
   - Expert reasoning and planning frameworks

### API Endpoints

The FastAPI backend provides several endpoints:

- `POST /chat/mistral-claude`: Main chat endpoint with full pipeline
- `POST /agent/mistral`: Mistral-only reasoning
- `POST /mistral_node`: Intermediate reasoning output

Example API call:
```bash
curl -X POST "http://localhost:8080/chat/mistral-claude" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the resilience priorities for Saint-Martin after Hurricane Irma?"}'
```

### Satellite Imagery Analysis

Use the satellite_imagery module for ML-based disaster assessment:

```bash
cd satellite_imagery
python ml_training_inference.py  # Train/infer on satellite chips
```

### Social Media Monitoring

The social_media module processes real-time crisis data from various platforms.

## 🌐 Deployment

### Local Development
Follow the manual setup instructions above.

### Cloud Deployment
- **Streamlit Cloud**: [https://resilienceai.streamlit.app/](https://resilienceai.streamlit.app/)
- **Docker**: Use the provided docker-compose.yml for containerized deployment
- **Kubernetes**: Adapt the Docker setup for K8s orchestration

### Environment Variables

Required environment variables:
- `QDRANT_URL`: Qdrant database URL
- `QDRANT_API_KEY`: Qdrant API key
- `CLAUDE_API_KEY`: Anthropic Claude API key
- `MISTRAL_API_KEY`: Mistral AI API key
- `HF_TOKEN`: Hugging Face token
- `PORT`: Application port (default: 8080)

## 🧪 Testing

Run the test suite:
```bash
cd tests
python -m pytest
```

Individual test files:
- `test_climate.py`: Climate tool tests
- `test_earth_engine.py`: Earth Engine integration tests
- `test_osm.py`: OpenStreetMap tool tests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run tests: `python -m pytest`
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to new functions
- Update documentation for API changes
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on open-source libraries: FastAPI, LangChain, Qdrant, Streamlit
- Research papers and datasets from various disaster recovery studies
- Community contributions and expert domain knowledge

## 📞 Support

For questions or support:
- Open an issue on GitHub
- Contact the development team
- Check the documentation in `additional_docs/` for detailed research papers

---

**TheLab** - Empowering resilience through AI-driven crisis planning.

