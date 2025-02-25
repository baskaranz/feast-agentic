# Agentic AI with Feast Feature Store

![Project Demo](./docs/demo.md)

## Overview

This project demonstrates an Agentic AI system that interacts with a Feast feature store to perform machine learning tasks. The AI agent can retrieve features, process them, and make intelligent decisions for use cases like recommendations, fraud detection, and customer segmentation.

## Architecture

The application consists of three main components:

1. **Feature Store (Feast)**: Stores and serves ML features
2. **Agentic AI System**: Retrieves features and makes decisions
3. **Frontend Dashboard**: Visualizes the workflow and results

![Architecture Diagram](./docs/architecture.md)

## Agentic AI Workflow

### 1. Feature Registration and Storage

Features are registered in the Feast feature store with appropriate metadata:
- **Feature Views**: Define logical groupings of features (e.g., customer_features, product_features)
- **Feature Services**: Define collections of features for specific use cases
- **Entity**: Define the keys used to retrieve features (e.g., customer_id, product_id)

Example feature registration:
```python
customer_features = FeatureView(
    name="customer_features",
    entities=["customer_id"],
    features=[
        Feature("age", ValueType.INT64),
        Feature("income", ValueType.FLOAT),
        Feature("credit_score", ValueType.INT64),
        Feature("purchase_history", ValueType.INT64)
    ],
    batch_source=file_source
)
```

### 2. AI Agent Initialization

The AI agent is initialized with:
- Access to the feature store
- A set of tools for specific tasks
- A LLM for natural language reasoning
- Memory to retain context

```python
class AIAgent:
    def __init__(self, feature_store: FeatureStore):
        self.feature_store = feature_store
        self.llm = OllamaLLM(model="mistral", temperature=0.7)
        self.memory = ConversationBufferMemory(return_messages=True)
        self.tools = [
            Tool(name="recommend_products", func=self._handle_recommendation),
            Tool(name="detect_fraud", func=self._handle_fraud_detection),
            # ... more tools
        ]
        self.agent = initialize_agent(tools=self.tools, llm=self.llm, 
                                     agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                                     memory=self.memory)
```

### 3. Feature Retrieval

The agent retrieves features using:
- **Online Features**: Real-time feature values for current predictions
- **Historical Features**: Past feature values for training or analysis

```python
# Online feature retrieval
online_features = feature_store.get_online_features(
    entity_rows=[{"customer_id": customer_id}],
    features=["customer_features:age", "customer_features:income"]
)

# Historical feature retrieval
entity_df = pd.DataFrame({"customer_id": [customer_id]})
historical_features = feature_store.get_historical_features(
    entity_df=entity_df,
    features=["customer_features:age", "customer_features:income"]
)
```

### 4. Feature Processing & Decision Making

The agent processes features through:
1. **Task Identification**: Determine the type of task (recommendation, fraud detection, etc.)
2. **Feature Selection**: Select relevant features for the task
3. **LLM Reasoning**: Use LLM to reason about the features
4. **Output Generation**: Generate appropriate outputs or predictions

```python
async def process_action(self, action: AgentAction) -> AgentResponse:
    # Convert action to a natural language query
    query = self._create_agent_query(action)
    
    # Run the agent with the query
    agent_response = await self.agent.ainvoke({"input": query})
    
    # Process the agent's response
    response = self._process_agent_response(action, agent_response)
    
    # Record the action in history
    self.add_to_history(action_type=action.action_type, description=action.description)
    
    return response
```

### 5. Result Presentation

Results are structured as `AgentResponse` objects containing:
- Status information
- Processed data
- Explanations or recommendations

```python
return AgentResponse(
    message=f"Generated product recommendations for customer {customer_id}",
    status="success",
    data={
        "customer_id": customer_id,
        "customer_features": customer_features,
        "recommendations": recommendations
    }
)
```

## Implementation Details

### Feature Store Implementation

In this demo, we use a mock Feast implementation that simulates:
- Feature registration through feature views and services
- Online feature retrieval for real-time serving
- Historical feature retrieval for analysis

In a production setting, you would replace this with a real Feast instance connected to data sources.

### AI Agent Implementation

The AI agent uses LangChain with the following components:
- **LLM**: Ollama running Mistral for reasoning
- **Tools**: Specialized functions for different tasks
- **Memory**: Conversation buffer for context retention
- **Agent**: REACT-style agent for reasoning and tool selection

### Fallback Mechanisms

The system implements robust error handling:
- If the LLM is unavailable, falls back to direct function calls
- If feature retrieval fails, uses defaults or cached values
- All errors are recorded in the agent history

### Agent History

The agent maintains a chronological history of all actions:
```python
def add_to_history(self, action_type: str, description: str, status: str = "success"):
    history_action = AgentHistoryAction(
        timestamp=datetime.utcnow().isoformat(),
        action=action_type,
        description=description,
        status=status
    )
    self.action_history.insert(0, history_action)
```

## Use Cases

### Product Recommendations

1. Agent retrieves customer features (age, income, purchase history)
2. Features are processed to determine customer preferences
3. Agent generates personalized product recommendations
4. Recommendations are ranked by match score

### Fraud Detection

1. Agent retrieves transaction features and customer credit profile
2. Features are analyzed for suspicious patterns
3. A fraud risk score is calculated
4. Risk factors are identified and explained

### Customer Segmentation

1. Agent retrieves comprehensive customer features
2. Features are analyzed to determine customer value and behavior
3. Customer is assigned to a segment (VIP, High Value, etc.)
4. Tailored strategies are recommended for the segment

## Running the Application

### Docker Setup
```bash
docker-compose up
```

### Manual Setup
```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm start

# Ollama (required for LLM)
ollama run mistral
```

## Technical Implementation Notes

### API Endpoints

- `/agent/action`: Process an agent action
- `/demo/recommendation`: Generate product recommendations
- `/demo/fraud-detection`: Analyze transaction for fraud
- `/demo/customer-segmentation`: Segment a customer

### Integration Points

- **Backend ↔ Feature Store**: Feature retrieval and storage
- **Backend ↔ LLM**: Natural language reasoning
- **Frontend ↔ Backend**: API calls for agent actions
- **Frontend ↔ User**: Visualization and interaction

## Extending the System

### Adding New Feature Views
1. Define new feature views in the feature store
2. Register the features with appropriate metadata
3. Create feature services for specific use cases

### Adding New Agent Capabilities
1. Implement a new handler function
2. Add the function as a tool in the agent initialization
3. Update the agent query creation for the new action type
4. Add appropriate prompt templates if needed

### Connecting to Real Data Sources
1. Replace the mock feature store with a real Feast instance
2. Configure offline and online stores
3. Set up data ingestion pipelines
4. Update feature retrieval code as needed

## Conclusion

This agentic AI system demonstrates how AI agents can leverage feature stores for machine learning tasks. By combining structured feature data with LLM reasoning capabilities, the system can provide intelligent insights and recommendations in a variety of use cases.