# Flask Application

A Flask-based blog application with web interface, RESTful API, Redis caching, PostgreSQL database, and Prometheus metrics.

## Features

- Web interface for blog management
- RESTful API endpoints for blog posts and users
- User authentication and authorization
- Redis caching for improved performance
- PostgreSQL database for data persistence
- Prometheus metrics for monitoring
- Health check endpoints

## Web Interface

Access the web interface at <http://localhost:5001>:

- User registration and login
- Create, read, update, and delete blog posts
- User profile management
- Responsive design for all devices

## API Endpoints

### Posts

```bash
GET /api/posts?page=1&per_page=10
GET /api/posts/<id>
POST /api/posts
{
    "body": "Post content",
    "user_id": 1
}
PUT /api/posts/<id>
{
    "body": "Updated content"
}
DELETE /api/posts/<id>
```

### Users

```bash
GET /api/users
GET /api/users/<id>
```

### System

```bash
GET /api/health
GET /api/metrics
GET /api/ready
GET /api/cache/info
POST /api/cache/clear
```

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- PostgreSQL
- Redis

### Development Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
```

### Docker Setup

```bash
docker-compose up --build
```

Access the application:

- Web Interface: <http://localhost:5001>
- API: <http://localhost:5001/api>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000>

## Configuration

- Development: `config.DevelopmentConfig`
- Production: `config.ProductionConfig`

Key configuration options:

- `SQLALCHEMY_DATABASE_URI`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Flask secret key
- `CACHE_TYPE`: Cache type (Redis)
- `CACHE_REDIS_URL`: Redis URL for caching

## Monitoring

- Prometheus metrics endpoint
- Health check endpoint
- System metrics (if psutil is available)
- Cache statistics

## Caching

Redis is used for:

- API response caching
- Session storage
- Rate limiting
- Web page caching

## Database

PostgreSQL is used for:

- User management
- Post management
- User authentication

## License

MIT License
