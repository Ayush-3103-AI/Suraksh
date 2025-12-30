# Suraksh Intelligence Platform

**Team: Arth**

High-security intelligence platform with GraphRAG capabilities for intelligence analysis and knowledge graph visualization.

## Architecture

This is a monorepo containing:
- **Backend**: FastAPI application (Python 3.11+)
- **Frontend**: Next.js 15 application (TypeScript)
- **Infrastructure**: Docker Compose setup for all services

## Phase 1: The Foundation

### Setup Instructions

1. **Clone and navigate to the repository**
   ```bash
   cd Suraksh
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres redis neo4j qdrant minio
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Services

- **Backend API**: Port 8000
- **Frontend**: Port 3000 (to be implemented)
- **PostgreSQL**: Port 5432
- **Redis**: Port 6379
- **Neo4j**: Ports 7474 (HTTP), 7687 (Bolt)
- **Qdrant**: Port 6333
- **MinIO**: Ports 9000 (API), 9001 (Console)

## Development

See `PRD's/06_PHASED_IMPLEMENTATION.md` for the complete implementation roadmap.

## Security

- Zero Trust architecture
- Post-Quantum Cryptography (PQC) support
- JWT-based authentication
- Client-side file encryption before upload

