# Agentic Mode Function Call Hierarchy

This document outlines the complete function call hierarchy when agentic mode is triggered from the UI for a use case. It shows how a request flows through the system from frontend to backend when AI agent mode is enabled.

## Frontend to Backend Flow

### 1. User Interaction in Frontend

- User toggles agentic mode: `toggleAgentMode()` in [`FeatureStoreDashboard.jsx`](../frontend/src/components/FeatureStoreDashboard.jsx)
- User submits a request: `handleSubmit()` in [`FeatureStoreDashboard.jsx`](../frontend/src/components/FeatureStoreDashboard.jsx)

### 2. Mode Toggle Process

- `toggleAgentMode()` sends a POST request to `/agent/mode` endpoint
- Frontend API call: `axios.post(`${API_URL}/agent/mode`, { use_agent: !useAgentMode })`
- Backend receives request at `set_agent_mode()` in [`app.py`](../backend/app.py)
- Creates new `AgenticFeatureStore` instance with requested mode
- Adds mode change to action history

### 3. Feature Request Process

- `handleSubmit()` prepares request based on use case
- API endpoint chosen based on `activeTab`
- Frontend sends request to:
  - Recommendation: `/demo/recommendation`
  - Fraud Detection: `/demo/fraud-detection`
  - Segmentation: `/demo/customer-segmentation`

## Backend Processing Flow (Agentic Mode)

### 1. API Endpoint Reception

- Request arrives at appropriate demo endpoint in [`app.py`](../backend/app.py)
- Creates a `FeatureRequest` object with `entity_id` and `action_type`
- Calls `agentic_feature_store.process_feature_request(request)`

### 2. Agentic Processing Flow

- `process_feature_request()` handles feature request
- Adds process start to action history
- **Creates natural language query**: `_create_agent_query()`
- Adds query creation to action history
- **Invokes AI agent**: `agent.ainvoke({"input": query})`
- Adds agent invocation to action history

### 3. Agent Execution Flow

- Agent uses LangChain tools to interact with feature store:
  - `_tool_get_online_features()`
  - `_tool_get_historical_features()`
  - `_tool_get_feature_service()`
  - `_tool_create_feature_view()`
  - `_tool_create_feature_service()`
  - `_tool_analyze_data_source()`
  - `_tool_suggest_features_for_use_case()`

- Agent processes query through `OllamaLLM` backend
- Adds agent response to action history

### 4. Response Processing

- **Process agent response**: `_process_agent_response()`
- Adds response processing to action history
- For specific use cases, calls:
  - **Recommendation**: `_handle_recommendation()`
  - **Fraud Detection**: `_handle_fraud_detection()`
  - **Segmentation**: `_handle_customer_segmentation()`

- Uses LLMChain with specialized prompts for enhanced insights:
  - `recommendation_prompt`
  - `fraud_prompt`
  - `segmentation_prompt`
  - `feature_view_creation_prompt`
  - `feature_service_creation_prompt`

- Adds successful action to history
- Returns `FeatureResponse` with data enriched with AI insights

### 5. Backend to Frontend Response

- API endpoint returns the `FeatureResponse` to frontend
- Frontend receives response in `handleSubmit()` callback
- Updates UI state with received data
- Refreshes action history from `/features/history` endpoint

## Frontend Rendering

### 1. Result Display

- `renderResultContent()` renders the appropriate result based on `activeTab`
- Detects if agent mode was used via presence of `ai_insights` field
- Renders different components based on use case:
  - Recommendations
  - Fraud Detection
  - Segmentation
- Displays AI-specific sections when agent mode was used

### 2. Processing Flow Visualization

- [`ProcessingFlowDiagram.jsx`](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx) renders the flow diagram based on `isAgentMode`
- Agent mode shows extended flow with 7 nodes
- Traditional mode shows simplified flow with 4 nodes

## Fallback Mechanisms

In case of AI agent failure:
1. Exception caught in `process_feature_request()`
2. Logs fallback to action history
3. Falls back to direct function calls

## Autonomous Feature Management Flow

When using the agentic mode for feature management:

### 1. Data Source Analysis

- Analyze a data source using `_tool_analyze_data_source()`
- AI agent examines CSV files to identify potential features and entities
- Results stored and returned with AI analysis

### 2. Feature View Creation

- Create a feature view using `_tool_create_feature_view()`
- AI agent identifies appropriate features and entity
- Stores new feature view in `custom_feature_views`
- Adds creation to action history

### 3. Feature Service Creation

- Create a feature service using `_tool_create_feature_service()`
- AI agent selects relevant features for specific use case
- Stores new feature service in `custom_feature_services`
- Adds creation to action history

### 4. Feature Suggestion

- Suggest features using `_tool_suggest_features_for_use_case()`
- AI agent analyzes available features to find relevant ones for use case
- Returns suggested features with reasoning

## Code References

### Frontend Components
- [`frontend/src/components/FeatureStoreDashboard.jsx`](../frontend/src/components/FeatureStoreDashboard.jsx) - Main dashboard component
- [`frontend/src/components/diagrams/ProcessingFlowDiagram.jsx`](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx) - Flow diagram visualization

### Backend Components
- [`backend/app.py`](../backend/app.py) - Main backend application with API endpoints and implementation

### Key Classes
- `AgenticFeatureStore` - Main class handling agentic feature store operations
- `FeatureStore` - Core class representing the feature store
- `FeatureService` - Class representing feature services

### Key Methods
- `process_feature_request()` - Main method for processing feature requests
- `_create_agent_query()` - Creates natural language queries for the agent
- `_process_agent_response()` - Processes the agent's response
- `_handle_recommendation()`, `_handle_fraud_detection()`, `_handle_customer_segmentation()` - Use case handlers

## Example Flow: Product Recommendations in Agent Mode

1. User toggles "AI Agent" mode ON in the UI
2. User selects "Recommendation" tab and enters a customer ID
3. User clicks "Get Features" button
4. Frontend sends request to `/demo/recommendation` with customer ID
5. Backend creates natural language query: "Retrieve features for customer [ID] and provide product recommendations"
6. Agent invoked to process query through Ollama LLM
7. Agent uses tools to retrieve customer features
8. Features processed with LLM to generate enhanced recommendations with reasoning
9. Enhanced response sent back to frontend with AI insights
10. Frontend renders personalized recommendations with feature importance visualization