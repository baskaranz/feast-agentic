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

### 2. Autonomous Feature Engineering

- `process_feature_request()` checks if a custom feature service exists for the use case
- If no custom service exists, initiates autonomous feature engineering:
  - Determines entity type based on use case
  - Analyzes data sources (`_tool_analyze_data_source()`) for relevant features
  - Generates feature suggestions (`_tool_suggest_features_for_use_case()`)
  - Creates a custom feature service for the use case (`_tool_create_feature_service()`)
  - Logs each step in the action history

### 3. Agent Query Creation

- **Creates enhanced natural language query**: `_create_agent_query()`
- If custom service exists, includes service info in the query
- Adds query creation to action history
- **Invokes AI agent**: `agent.ainvoke({"input": query})`
- Adds agent invocation to action history

### 4. Agent Execution Flow

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

### 5. Response Processing

- **Process agent response**: `_process_agent_response()`
- Adds response processing to action history
- For specific use cases, calls:
  - **Recommendation**: `_handle_recommendation()`
  - **Fraud Detection**: `_handle_fraud_detection()`
  - **Segmentation**: `_handle_customer_segmentation()`

- Each handler checks if a custom feature service exists and uses it if available
- Uses LLMChain with specialized prompts for enhanced insights:
  - `recommendation_prompt`
  - `fraud_prompt`
  - `segmentation_prompt`
  - `feature_view_creation_prompt`
  - `feature_service_creation_prompt`

- Adds successful action to history
- Returns `FeatureResponse` with data enriched with AI insights

### 6. Backend to Frontend Response

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

### Automatic Feature Service Creation (Triggered by "Get Features")

When a user clicks "Get Features" in agentic mode:

1. System checks if a custom feature service exists for the use case
2. If not, it automatically:
   - Analyzes all available data sources (customer, product, transaction CSVs)
   - Suggests the most relevant features for the use case
   - Creates a custom feature service named `agentic_{action_type}_service`
   - Logs the entire process in the action history
3. The custom service is then used for feature retrieval
4. The agent is informed about the custom service in its query

### Manual Feature Management (via API)

The system also supports manual feature management through APIs:

#### 1. Data Source Analysis

- Analyze a data source using `_tool_analyze_data_source()`
- AI agent examines CSV files to identify potential features and entities
- Results stored and returned with AI analysis

#### 2. Feature View Creation

- Create a feature view using `_tool_create_feature_view()`
- AI agent identifies appropriate features and entity
- Stores new feature view in `custom_feature_views`
- Adds creation to action history

#### 3. Feature Service Creation

- Create a feature service using `_tool_create_feature_service()`
- AI agent selects relevant features for specific use case
- Stores new feature service in `custom_feature_services`
- Adds creation to action history

#### 4. Feature Suggestion

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
- `process_feature_request()` - Main method for processing feature requests with autonomous feature engineering
- `_create_agent_query()` - Creates natural language queries for the agent with service info
- `_process_agent_response()` - Processes the agent's response
- `_handle_recommendation()`, `_handle_fraud_detection()`, `_handle_customer_segmentation()` - Use case handlers that use custom services

## Example Flow: Product Recommendations in Agent Mode

1. User toggles "AI Agent" mode ON in the UI
2. User selects "Recommendation" tab and enters a customer ID
3. User clicks "Get Features" button
4. Frontend sends request to `/demo/recommendation` with customer ID
5. Backend checks if a custom feature service exists for recommendations
6. If not, it analyzes data sources and creates an `agentic_recommendation_service`
7. Backend creates enhanced natural language query with service info
8. Agent invoked to process query through Ollama LLM
9. Agent uses tools to retrieve customer features using the custom service
10. Features processed with LLM to generate enhanced recommendations with reasoning
11. Enhanced response sent back to frontend with AI insights
12. Frontend renders personalized recommendations with feature importance visualization

This autonomous flow enables the system to automatically create and use optimal feature views and services for each use case without requiring explicit user action beyond clicking "Get Features".