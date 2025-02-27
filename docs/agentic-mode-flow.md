# Agentic Mode Function Call Hierarchy

This document outlines the complete function call hierarchy when agentic mode is triggered from the UI for a use case. It shows how a request flows through the system from frontend to backend when AI agent mode is enabled.

## Frontend to Backend Flow

### 1. User Interaction in Frontend

- User toggles agentic mode: [`toggleAgentMode()`](../frontend/src/components/FeatureStoreDashboard.jsx#L129) in `FeatureStoreDashboard.jsx`
- User submits a request: [`handleSubmit()`](../frontend/src/components/FeatureStoreDashboard.jsx#L178) in `FeatureStoreDashboard.jsx`

### 2. Mode Toggle Process

- [`toggleAgentMode()`](../frontend/src/components/FeatureStoreDashboard.jsx#L129) sends a POST request to `/agent/mode` endpoint
- Frontend API call: `axios.post(`${API_URL}/agent/mode`, { use_agent: !useAgentMode })`
- Backend receives request at [`set_agent_mode()`](../backend/app.py#L940) in `app.py`
- Creates new `AgenticFeatureStore` instance with requested mode
- Adds mode change to action history

### 3. Feature Request Process

- [`handleSubmit()`](../frontend/src/components/FeatureStoreDashboard.jsx#L178) prepares request based on use case
- API endpoint chosen based on `activeTab` (lines 187-196)
- Frontend sends request to:
  - Recommendation: [`/demo/recommendation`](../backend/app.py#L1756)
  - Fraud Detection: [`/demo/fraud-detection`](../backend/app.py#L1765)
  - Segmentation: [`/demo/customer-segmentation`](../backend/app.py#L1774)

## Backend Processing Flow (Agentic Mode)

### 1. API Endpoint Reception

- Request arrives at appropriate demo endpoint in [`app.py`](../backend/app.py)
- Creates a `FeatureRequest` object with `entity_id` and `action_type`
- Calls [`agentic_feature_store.process_feature_request(request)`](../backend/app.py#L309)

### 2. Agentic Processing Flow

- [`process_feature_request()`](../backend/app.py#L309) handles feature request
- Adds process start to action history (line 371)
- **Creates natural language query**: [`_create_agent_query()`](../backend/app.py#L463)
- Adds query creation to action history (line 380)
- **Invokes AI agent**: [`agent.ainvoke({"input": query})`](../backend/app.py#L393)
- Adds agent invocation to action history (line 387)

### 3. Agent Execution Flow

- Agent uses LangChain tools to interact with feature store:
  - [`_tool_get_online_features()`](../backend/app.py#L976)
  - [`_tool_get_historical_features()`](../backend/app.py#L990)
  - [`_tool_get_feature_service()`](../backend/app.py#L1005)
  - [`_tool_create_feature_view()`](../backend/app.py#L1027)
  - [`_tool_create_feature_service()`](../backend/app.py#L1071)
  - [`_tool_analyze_data_source()`](../backend/app.py#L1183)
  - [`_tool_suggest_features_for_use_case()`](../backend/app.py#L1251)

- Agent processes query through `OllamaLLM` backend
- Adds agent response to action history (line 398)

### 4. Response Processing

- **Process agent response**: [`_process_agent_response()`](../backend/app.py#L474)
- Adds response processing to action history (line 438)
- For specific use cases, calls:
  - **Recommendation**: [`_handle_recommendation()`](../backend/app.py#L566)
  - **Fraud Detection**: [`_handle_fraud_detection()`](../backend/app.py#L670)
  - **Segmentation**: [`_handle_customer_segmentation()`](../backend/app.py#L743)

- Uses LLMChain with specialized prompts ([lines 659-747](../backend/app.py#L659)) for enhanced insights:
  - [`recommendation_prompt`](../backend/app.py#L659)
  - [`fraud_prompt`](../backend/app.py#L675)
  - [`segmentation_prompt`](../backend/app.py#L688)
  - [`feature_view_creation_prompt`](../backend/app.py#L702)
  - [`feature_service_creation_prompt`](../backend/app.py#L728)

- Adds successful action to history (line 447)
- Returns `FeatureResponse` with data enriched with AI insights

### 5. Backend to Frontend Response

- API endpoint returns the `FeatureResponse` to frontend
- Frontend receives response in [`handleSubmit()`](../frontend/src/components/FeatureStoreDashboard.jsx#L178) callback
- Updates UI state with received data
- Refreshes action history from `/features/history` endpoint

## Frontend Rendering

### 1. Result Display

- [`renderResultContent()`](../frontend/src/components/FeatureStoreDashboard.jsx#L433) renders the appropriate result based on `activeTab`
- Detects if agent mode was used via presence of `ai_insights` field (line 437)
- Renders different components based on use case:
  - [Recommendations](../frontend/src/components/FeatureStoreDashboard.jsx#L445)
  - [Fraud Detection](../frontend/src/components/FeatureStoreDashboard.jsx#L551)
  - [Segmentation](../frontend/src/components/FeatureStoreDashboard.jsx#L654)
- Displays AI-specific sections when agent mode was used

### 2. Processing Flow Visualization

- [`ProcessingFlowDiagram.jsx`](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx) renders the flow diagram based on `isAgentMode`
- Agent mode shows extended flow with 7 nodes ([line 80](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx#L80))
- Traditional mode shows simplified flow with 4 nodes ([line 249](../frontend/src/components/diagrams/ProcessingFlowDiagram.jsx#L249))

## Fallback Mechanisms

In case of AI agent failure:
1. Exception caught in [`process_feature_request()`](../backend/app.py#L404)
2. Logs fallback to action history (line 408)
3. Falls back to direct function calls ([lines 412-436](../backend/app.py#L412))

## Autonomous Feature Management Flow

When using the agentic mode for feature management:

### 1. Data Source Analysis

- Analyze a data source using [`_tool_analyze_data_source()`](../backend/app.py#L1183)
- AI agent examines CSV files to identify features and entities
- Results stored and returned with AI analysis

### 2. Feature View Creation

- Create a feature view using [`_tool_create_feature_view()`](../backend/app.py#L1027)
- AI agent identifies appropriate features and entity
- Stores new feature view in `custom_feature_views`
- Adds creation to action history

### 3. Feature Service Creation

- Create a feature service using [`_tool_create_feature_service()`](../backend/app.py#L1071)
- AI agent selects relevant features for specific use case
- Stores new feature service in `custom_feature_services`
- Adds creation to action history

### 4. Feature Suggestion

- Suggest features using [`_tool_suggest_features_for_use_case()`](../backend/app.py#L1251)
- AI agent analyzes available features to find relevant ones for use case
- Returns suggested features with reasoning

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