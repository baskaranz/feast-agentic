# Traditional Mode Function Call Hierarchy

This document outlines the complete function call hierarchy when traditional (non-agentic) mode is used from the UI for a use case. It shows how a request flows through the system from frontend to backend when AI agent mode is disabled.

## Frontend to Backend Flow

### 1. User Interaction in Frontend

- User toggles traditional mode: `toggleAgentMode()` in [`FeatureStoreDashboard.jsx`](../frontend/src/components/FeatureStoreDashboard.jsx)
- User submits a request: `handleSubmit()` in [`FeatureStoreDashboard.jsx`](../frontend/src/components/FeatureStoreDashboard.jsx)

### 2. Mode Toggle Process

- `toggleAgentMode()` sends a POST request to `/agent/mode` endpoint
- Frontend API call: `axios.post(`${API_URL}/agent/mode`, { use_agent: false })`
- Backend receives request at `set_agent_mode()` in [`app.py`](../backend/app.py)
- Creates new `AgenticFeatureStore` instance with `use_agent=false`
- Adds mode change to action history

### 3. Feature Request Process

- `handleSubmit()` prepares request based on use case
- API endpoint chosen based on `activeTab`
- Frontend sends request to:
  - Recommendation: `/demo/recommendation`
  - Fraud Detection: `/demo/fraud-detection`
  - Segmentation: `/demo/customer-segmentation`

## Backend Processing Flow (Traditional Mode)

### 1. API Endpoint Reception

- Request arrives at appropriate demo endpoint in [`app.py`](../backend/app.py)
- Creates a `FeatureRequest` object with `entity_id` and `action_type`
- Calls `agentic_feature_store.process_feature_request(request)`

### 2. Traditional Mode Processing

- `process_feature_request()` checks if agent mode is disabled (`not self.use_agent`) 
- Since `use_agent` is false, enters the traditional mode processing path
- Adds process start to action history with "Traditional Mode" label
- Based on `action_type`, directly calls the appropriate handler:
  - Recommendation: `_handle_recommendation()`
  - Fraud Detection: `_handle_fraud_detection()`
  - Segmentation: `_handle_customer_segmentation()`
- No AI agent or LLM is involved in this flow

### 3. Direct Feature Retrieval

- For the specific handler (e.g., `_handle_recommendation()`):
  - Gets the appropriate feature service with `feature_store.get_feature_service()`
  - Retrieves features from the feature service
  - Gets online features with direct call to `feature_store.get_online_features()`
  - Features are retrieved directly from SQLite database without any AI processing

### 4. Standard Processing

- Processes features using predefined business logic
- No AI-enhanced insights are generated
- Generates standardized outputs based on rules:
  - Recommendations based on customer features
  - Fraud scores based on transaction features
  - Customer segments based on profile features
- Does not include advanced feature importance or confidence scores

### 5. Backend to Frontend Response

- Constructs a `FeatureResponse` with processed data
- Does NOT include AI-specific fields like `ai_insights`
- API endpoint returns the `FeatureResponse` to frontend
- Frontend receives response in `handleSubmit()` callback
- Updates UI state with received data
- Refreshes action history from `/features/history` endpoint

## Frontend Rendering

### 1. Result Display

- `renderResultContent()` renders the appropriate result based on `activeTab`
- Detects traditional mode via absence of `ai_insights` field
- Renders different components based on use case:
  - Recommendations (simplified version without AI insights)
  - Fraud Detection (simplified version without AI insights)
  - Segmentation (simplified version without AI insights)
- Does NOT display AI-specific sections that depend on `ai_insights`

### 2. Processing Flow Visualization

- [`ProcessingFlowDiagram.jsx`](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx) renders the flow diagram based on `isAgentMode`
- Traditional mode shows simplified flow with 4 nodes (vs. 7 in agent mode)
- The flow diagram shows:
  1. Feature Service Selection
  2. Feature Retrieval (from feature store)
  3. Data Processing (applying business logic)
  4. Final Results

## Feature Store Interaction

In traditional mode, the feature store interaction is direct and straightforward:

### 1. Feature Services

- Uses predefined feature services from the `FeatureService` class
- Cannot create new custom feature views or services (this is an agent-only feature)
- Retrieves standard feature lists for each use case

### 2. Feature Retrieval

- For online features: Directly queries the SQLite database tables
- For historical features: Directly reads from CSV files in the offline store
- No additional feature analysis or transformation is performed

### 3. Data Processing

- Features are processed using fixed business logic
- Simple rules determine outputs like recommendations or fraud scores
- No AI-based reasoning or confidence scores are applied

## Code References

### Frontend Components
- [`frontend/src/components/FeatureStoreDashboard.jsx`](../frontend/src/components/FeatureStoreDashboard.jsx) - Main dashboard component
- [`frontend/src/components/diagrams/ProcessingFlowDiagram.jsx`](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx) - Flow diagram visualization

### Backend Components
- [`backend/app.py`](../backend/app.py) - Main backend application with API endpoints and implementation

### Key Classes
- `AgenticFeatureStore` - Main class handling feature store operations (with `use_agent=false`)
- `FeatureStore` - Core class representing the feature store
- `FeatureService` - Class representing feature services

### Key Methods
- `process_feature_request()` - Main method for processing feature requests
- `_handle_recommendation()` - Handles product recommendation use case
- `_handle_fraud_detection()` - Handles fraud detection use case
- `_handle_customer_segmentation()` - Handles customer segmentation use case

## Example Flow: Product Recommendations in Traditional Mode

1. User toggles "Traditional" mode ON in the UI (disables AI Agent)
2. User selects "Recommendation" tab and enters a customer ID
3. User clicks "Get Features" button
4. Frontend sends request to `/demo/recommendation` with customer ID
5. Backend determines that agent mode is disabled
6. System directly calls `_handle_recommendation()` function
7. Function gets feature service and retrieves customer features from SQLite
8. Features are processed using predefined rules and logic
9. Standard recommendations are generated without AI reasoning
10. Response without `ai_insights` is sent back to frontend
11. Frontend renders simpler recommendation list without feature importance and reasoning

## Comparison with Agentic Mode

The traditional mode differs from agentic mode in several key ways:

| Traditional Mode | Agentic Mode |
|------------------|--------------|
| Direct function calls | Uses LLM agent |
| Predefined business logic | AI-based reasoning |
| Fixed feature sets | Can suggest and create new features |
| Standard outputs | Enhanced insights with confidence scores |
| Cannot create custom feature views | Can autonomously create feature views |
| Simpler processing flow (4 steps) | More complex flow (7 steps) |
| Lower latency | Higher latency due to LLM inference |
| Deterministic results | May vary based on LLM responses |
| No reasoning or explanations | Provides reasoning and explanations |