# Events Aggregator Service

Асинхронный сервис агрегации событий на Python для сбора данных из внешнего API, обработки и сохранения в PostgreSQL.

## Overview

Проект реализует фоновый сбор событий из внешнего источника, их обработку и хранение в базе данных.  
Дополнительно настроен CI/CD пайплайн и деплой в Kubernetes.

---

## Features

- Async event collection from external API  
- Background worker for periodic data polling  
- Data persistence in PostgreSQL  
- Automated testing with pytest  
- Linting with Ruff  
- Dockerized application  
- CI/CD via GitHub Actions  
- Kubernetes deployment

---

## Tech Stack

### Backend
- Python
- FastAPI
- asyncio
- SQLAlchemy
- PostgreSQL

### Infrastructure
- Docker
- Kubernetes
- GitHub Actions

### Quality
- pytest
- Ruff

---

## Architecture

```text
External API
   ↓
Async Worker
   ↓
Processing Layer
   ↓
PostgreSQL

CI/CD Pipeline:
Lint → Tests → Build → Deploy
```

---

## Project Structure

```bash
app/
├── api/
├── workers/
├── services/
├── repositories/
├── models/
└── core/

tests/
.github/workflows/
```

---

## Local Run

Clone repository:

```bash
git clone https://github.com/Metridat/events-aggregator.git
cd events-aggregator
```

Run with Docker:

```bash
docker compose up --build
```

---

## Run Tests

```bash
pytest
```

Run linter:

```bash
ruff check .
```

---

## CI/CD

On push to main branch pipeline runs automatically:

- Ruff linting  
- Tests  
- Docker image build  
- Deployment to Kubernetes cluster

Implemented with GitHub Actions.

---

## What Was Practiced In This Project

This project was used to practice:

- asynchronous background workers  
- external API integrations  
- data aggregation patterns  
- containerization  
- Kubernetes deployment  
- CI/CD automation
