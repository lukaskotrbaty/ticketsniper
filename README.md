# Ticket Sniper

A free service to monitor sold-out RegioJet tickets and notify users when seats become available.

**Live application:** [ticketsniper.eu](https://ticketsniper.eu)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Running the Project

1. **Clone the repository**
   ```bash
   git clone https://github.com/lukaskotrbaty/ticketsniper.git
   cd ticketsniper
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - SQL Admin: http://localhost:8000/admin
   - Flower (Celery monitoring): http://localhost:5555

## Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview production build
```

### Backend Development
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload  # Development server
```

### Testing
```bash
# Backend tests (from backend/ directory)
poetry run pytest                         # Run all tests
poetry run pytest -v                      # Verbose output
poetry run pytest tests/worker/test_tasks.py -v  # Specific test file
```

### Database & Redis
```bash
docker-compose up -d db redis             # Start dependencies only
```

# Application Architecture: Ticket Sniper

## 1. Document Purpose

This document describes the architecture of a web application designed to monitor ticket availability for sold-out Regiojet bus routes. The goal is to provide users with email notifications as soon as seats become available on routes they are monitoring.

The document is intended for developers, architects, and anyone who needs to understand the technical design and functionality of the application.

## 2. Architecture Overview

The application uses modern web technologies and is designed with scalability and separation of concerns in mind. It consists of the following main components:

*   **Frontend (FE):** Single-page application (SPA) built on **Vue.js**, serving as the user interface.
*   **Backend (BE):** API server built on **Python FastAPI**, handling requests from the frontend, managing users, monitored routes, and communicating with other system components.
*   **Database (DB):** Relational database **PostgreSQL** for persistent storage of user data, routes, and their relationships.
*   **Asynchronous Worker:** System for background task processing using **Celery** with **Redis** as a message broker. The worker handles periodic Regiojet API polling and sending email notifications.
*   **Email Service:** Component using `smtplib` for sending confirmation emails and ticket availability notifications.

## 3. Technology Stack

*   **Frontend:** Vue.js 3 (Composition API), Pinia (State Management), Axios (HTTP Client), CSS Framework (e.g., Tailwind CSS or Vuetify)
*   **Backend:** Python 3.10+, FastAPI, Uvicorn (ASGI Server), SQLAlchemy (ORM), Pydantic (Data Validation), python-jose (JWT), Celery, Flower (Celery Monitoring UI - optional)
*   **Database:** PostgreSQL (version 13+)
*   **Message Broker:** Redis (for Celery)
*   **Email:** Python `smtplib`, `email` module
*   **Containerization:** Docker, Docker Compose

## 4. Documentation Structure

This documentation is divided into the following files, all located in the docs folder:

*   `architecture_overview.md`: High-level view of components and their interactions.
*   `frontend.md`: Detailed description of the frontend application.
*   `backend_api.md`: Detailed description of the backend API and its modules.
*   `database_schema.md`: Description of the PostgreSQL database schema.
*   `async_worker.md`: Description of Celery workers and task functionality.

## 5. How to Use This Documentation

To understand the overall design, start with the `architecture_overview.md` file. For details about specific parts of the system, refer to the relevant files. Mermaid diagrams are included to visualize key concepts.

## Disclaimer

Ticket Sniper is an independent service not officially operated by or affiliated with RegioJet a.s. or any other carrier. The application only monitors publicly available information about RegioJet connections. Ticket purchases are conducted exclusively on the official carrier websites.
