# Tanzania Climate Prediction Dashboard

Interactive web-based dashboard system for climate insights, ML model monitoring, insurance triggers, and risk management.

## Project Structure

```
dashboard/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration and database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── main.py      # Application entry point
│   ├── alembic/         # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Dashboard pages
│   │   ├── types/       # TypeScript types
│   │   ├── config/      # Configuration
│   │   └── main.tsx     # Application entry point
│   ├── package.json
│   └── Dockerfile
├── docker-compose.dev.yml   # Development environment
├── docker-compose.prod.yml  # Production environment
└── README.md
```

## Quick Start (Development)

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Using Docker Compose (Recommended)

1. Copy environment file:
```bash
cp .env.example .env
```

2. Start all services:
```bash
docker-compose -f docker-compose.dev.yml up
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development (Without Docker)

#### Backend

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
uvicorn app.main:app --reload
```

#### Frontend

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start development server:
```bash
npm run dev
```

## Database Setup

The application uses PostgreSQL. When using Docker Compose, the database is automatically created and configured.

For manual setup:

1. Create database:
```sql
CREATE DATABASE climate_dev;
CREATE USER user WITH PASSWORD 'pass';
GRANT ALL PRIVILEGES ON DATABASE climate_dev TO user;
```

2. Run migrations:
```bash
cd backend
alembic upgrade head
```

## Production Deployment

1. Set up environment variables in `.env` file

2. Build and start services:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. Check service health:
```bash
docker-compose -f docker-compose.prod.yml ps
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Features

- **Executive Dashboard**: High-level KPIs, trigger rates, loss ratios, sustainability metrics
- **Model Performance**: ML model monitoring, comparison, feature importance, drift detection
- **Triggers Dashboard**: Historical trigger events, forecasts, early warnings
- **Climate Insights**: Time series visualization, anomaly detection, correlation analysis
- **Risk Management**: Portfolio metrics, scenario analysis, recommendations

## Technology Stack

**Backend:**
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- Alembic (migrations)

**Frontend:**
- React 18
- TypeScript
- Material-UI (MUI)
- Plotly.js
- Axios
- Vite

**Deployment:**
- Docker
- Docker Compose
- Nginx

## License

Proprietary - Tanzania Climate Prediction Project
