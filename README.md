# ElderComp - Elderly Companion System

A comprehensive AI-powered companion system designed to support elderly individuals through natural language processing, memory management, and caregiver integration.

## 🏗️ Architecture Overview

ElderComp consists of four main modules working together to provide intelligent elderly care support:

### Module 1: Natural Language to JSON
- **Purpose**: Converts free-form elderly conversation into structured JSON
- **Features**: 
  - Singlish code-switching support
  - Speech-to-text error correction
  - Entity extraction (NER/POS tagging)
  - Temporal expression normalization

### Module 2: Memory Router
- **Purpose**: Intelligently routes information to appropriate memory stores
- **Features**:
  - Question vs statement classification
  - Hybrid routing (rule-based + LLM)
  - Vector embedding generation
  - Multi-database targeting (STM/LTM/HCM)

### Module 3: RAG Architecture
- **Purpose**: Retrieval-Augmented Generation for context-aware responses
- **Features**:
  - PostgreSQL with pgvector for semantic search
  - Hybrid retrieval (ANN + BM25)
  - Reranking and deduplication
  - Context packaging for SLM

### Module 4: Caregiver Interface
- **Purpose**: Web interface for caregivers to manage elderly information
- **Features**:
  - Role-based authentication
  - Real-time data updates
  - Medical information management
  - Family communication tools

## 📁 Project Structure

```
eldercomp/
├── database/                    # Database schemas and configuration
│   ├── schemas/                # SQL schema files
│   ├── config/                 # Database configuration
│   ├── migrations/             # Database migrations
│   ├── seeds/                  # Sample data
│   ├── docker-compose.yml      # PostgreSQL + pgvector setup
│   └── init.sql               # Database initialization
├── rag_system/                 # AI/ML processing system (Modules 1-3)
│   ├── modules/
│   │   ├── nlp_processor/     # Module 1: NL to JSON
│   │   ├── memory_router/     # Module 2: Memory routing
│   │   └── retrieval_engine/  # Module 3: RAG core
│   ├── shared/
│   │   ├── schemas/           # Pydantic models
│   │   ├── config/            # LLM and system config
│   │   └── utils/             # Utility functions
│   ├── api/                   # FastAPI endpoints
│   └── requirements.txt       # Python dependencies
└── caregiver_interface/        # Module 4: Web application
    ├── backend/               # FastAPI backend
    └── frontend/              # React frontend
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose
- PostgreSQL with pgvector extension

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eldercomp
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file in root directory
   cp .env.example .env
   
   # Required environment variables:
   GEMINI_API_KEY=your_gemini_api_key
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=eldercomp
   DB_USER=postgres
   DB_PASSWORD=password
   ENCRYPTION_KEY=your_encryption_key_change_in_production
   ```

3. **Start the database**
   ```bash
   cd database
   docker-compose up -d
   ```

4. **Install RAG system dependencies**
   ```bash
   cd rag_system
   pip install -r requirements.txt
   
   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

5. **Install caregiver interface dependencies**
   ```bash
   # Backend
   cd caregiver_interface/backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

### Running the System

1. **Start the RAG system API**
   ```bash
   cd rag_system
   uvicorn api.main:app --reload --port 8000
   ```

2. **Start the caregiver interface backend**
   ```bash
   cd caregiver_interface/backend
   uvicorn app.main:app --reload --port 8001
   ```

3. **Start the caregiver interface frontend**
   ```bash
   cd caregiver_interface/frontend
   npm start
   ```

4. **Access the applications**
   - RAG System API: http://localhost:8000
   - Caregiver Interface: http://localhost:3000
   - Database Admin (pgAdmin): http://localhost:8080

## 🔧 Configuration

### Database Configuration

The system uses PostgreSQL with the pgvector extension for semantic search capabilities. Key configuration files:

- `database/docker-compose.yml`: Database container setup
- `database/config/database.py`: Connection management
- `database/init.sql`: Schema initialization

### LLM Configuration

The system integrates with Google's Gemini API for natural language processing:

- `rag_system/shared/config/llm_config.py`: LLM client configuration
- Environment variable `GEMINI_API_KEY` required

### Memory Databases

Three specialized memory stores:

1. **Short-Term Memory (STM)**: Recent conversations, tasks (7-day expiration)
2. **Long-Term Memory (LTM)**: Personal information, family, preferences
3. **Healthcare Memory (HCM)**: Medical information with encryption

## 🧪 Testing

### Unit Tests
```bash
# RAG system tests
cd rag_system
pytest tests/ -v

# Caregiver interface tests
cd caregiver_interface/backend
pytest tests/ -v
```

### Integration Tests
```bash
# Full system integration test
python scripts/integration_test.py
```

### API Testing
```bash
# Test RAG system endpoints
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "I want to cook ABC soup tomorrow"}]}'
```

## 📊 Monitoring and Logging

### Health Checks
- Database: `GET /health/database`
- RAG System: `GET /health/rag`
- Caregiver Interface: `GET /health/api`

### Logging
- Structured logging with `structlog`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log files stored in `logs/` directory

### Metrics
- Prometheus metrics available at `/metrics`
- Key metrics: processing time, error rates, memory usage

## 🔒 Security

### Data Protection
- Healthcare data encrypted using pgcrypto
- Role-based access control for caregiver interface
- API key authentication for external services

### Privacy Considerations
- Personal information handling compliant with privacy regulations
- Data retention policies for different memory types
- Audit logging for sensitive operations

## 🛠️ Development

### Code Style
```bash
# Format code
black rag_system/
isort rag_system/

# Lint code
flake8 rag_system/
mypy rag_system/
```

### Adding New Features

1. **New NLP Processors**: Add to `rag_system/modules/nlp_processor/`
2. **New Memory Types**: Update database schemas and routing logic
3. **New API Endpoints**: Add to `rag_system/api/endpoints/`
4. **New UI Components**: Add to `caregiver_interface/frontend/src/components/`

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 📈 Performance Optimization

### Database Optimization
- Vector indexes using ivfflat for similarity search
- Composite indexes for common query patterns
- Connection pooling for concurrent requests

### Caching
- LLM response caching for repeated queries
- Entity extraction result caching
- Database query result caching

### Scaling Considerations
- Horizontal scaling with load balancers
- Database read replicas for query distribution
- Microservice architecture for independent scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write comprehensive tests for new features
- Update documentation for API changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- API Documentation: http://localhost:8000/docs (when running)
- Database Schema: See `database/schemas/` directory
- Frontend Components: See `caregiver_interface/frontend/src/`

### Common Issues

1. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Check environment variables
   - Verify pgvector extension is installed

2. **LLM API Issues**
   - Verify GEMINI_API_KEY is set correctly
   - Check API rate limits
   - Monitor API usage quotas

3. **Frontend Build Issues**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify environment variables

### Getting Help
- Create an issue on GitHub
- Check existing documentation
- Review logs for error details

## 🔮 Roadmap

### Phase 1 (Current)
- ✅ Core architecture implementation
- ✅ Basic NLP processing
- ✅ Database schema design
- ✅ Caregiver interface foundation

### Phase 2 (Planned)
- [ ] Advanced emotion detection
- [ ] Voice input/output integration
- [ ] Mobile application
- [ ] Multi-language support

### Phase 3 (Future)
- [ ] IoT device integration
- [ ] Predictive health analytics
- [ ] Family member notifications
- [ ] AI-powered care recommendations

---

**ElderComp** - Empowering elderly care through intelligent technology 🏠💙
