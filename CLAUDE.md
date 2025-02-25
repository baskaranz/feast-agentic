# Feast Agentic AI Project Guide

## Build/Run Commands
- **Run Backend**: `cd backend && python app.py` or `uvicorn app:app --host 0.0.0.0 --port 8000 --reload`
- **Run Frontend**: `cd frontend && npm start`
- **Docker Compose**: `docker-compose up` (runs backend, frontend, and Ollama)
- **Run Tests**: `cd backend && pytest` or `cd frontend && npm test`
- **Single Test (Backend)**: `pytest backend/tests/test_file.py::test_name`
- **Single Test (Frontend)**: `cd frontend && npm test -- -t "test name"`
- **Lint Backend**: `flake8 backend`
- **Lint Frontend**: `cd frontend && npm run lint`

## Code Style Guidelines
- **Python**: Use type hints, follow PEP 8 standards, docstrings for functions/classes
- **JavaScript**: Use ES6+ features, JSX for React components, functional components preferred
- **Imports**: Group imports (stdlib, third-party, local) with a blank line between groups
- **Error Handling**: Use try/except with specific exceptions, handle errors gracefully
- **Naming**: snake_case for Python variables/functions, camelCase for JavaScript
- **API Responses**: Follow consistent response format (message, status, data)
- **Components**: One component per file, use Tailwind for styling
- **Asynchronous**: Use async/await pattern for asynchronous operations