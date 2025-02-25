# Agentic AI with Feast Feature Store - Backend

This is the backend component of the Agentic AI with Feast Feature Store demo application. It provides a FastAPI-based API that simulates interactions between an AI agent and a Feast feature store.

## Features

- Mock implementation of a Feast feature store
- AI agent that can process various ML tasks
- REST API endpoints for feature store access and agent actions
- Demo endpoints for common ML use cases

## Setup

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the backend server:

```bash
python app.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Feature Store Endpoints

- `GET /feature-views`: Get all available feature views
- `GET /feature-view/{name}`: Get information about a specific feature view
- `GET /feature-services`: Get all available feature services
- `GET /feature-service/{name}`: Get information about a specific feature service

### Agent Endpoints

- `POST /agent/action`: Execute an agent action
- `GET /agent/history`: Get the agent's action history

### Demo Endpoints

- `POST /demo/recommendation`: Generate product recommendations for a customer
- `POST /demo/fraud-detection`: Detect fraud for a transaction
- `POST /demo/customer-segmentation`: Segment a customer based on their features

## Agent Actions

The agent can perform the following actions:

| Action Type | Description | Required Parameters |
|-------------|-------------|---------------------|
| `get_feature_info` | Get information about a feature view | `feature_view` |
| `get_online_features` | Get online features for entities | `entity_rows`, `features` |
| `get_historical_features` | Get historical features for entities | `entity_data`, `features` |
| `make_recommendation` | Generate product recommendations | `customer_id` |
| `detect_fraud` | Detect fraud for a transaction | `transaction_id` |
| `segment_customer` | Segment a customer | `customer_id` |

## Example Usage

### Making a Recommendation

```bash
curl -X 'POST' \
  'http://localhost:8000/demo/recommendation' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"customer_id": "CUST-1234"}'
```

### Detecting Fraud

```bash
curl -X 'POST' \
  'http://localhost:8000/demo/fraud-detection' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"transaction_id": "TRANS-5678"}'
```

### Segmenting a Customer

```bash
curl -X 'POST' \
  'http://localhost:8000/demo/customer-segmentation' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"customer_id": "CUST-1234"}'
```

## Notes for Production Use

This is a demonstration application with mock feature store functionality. For production use:

1. Replace the mock Feast implementation with a real Feast feature store connection
2. Add proper authentication and authorization
3. Implement more robust error handling and logging
4. Add monitoring and observability
5. Containerize the application for easier deployment