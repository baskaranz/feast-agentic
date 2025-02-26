# Agentic AI with Feast Feature Store

![Project Demo](./docs/demo.md)

## Overview

This project demonstrates an Agentic AI system for interacting with a Feast feature store. The AI agent can retrieve and process features from the feature store to perform machine learning tasks like recommendations, fraud detection, and customer segmentation.

### AI Agent vs Traditional Mode

The system supports two processing modes that can be toggled via the UI:

#### AI Agent Mode
- Uses an AI agent to intelligently interact with the feature store
- Provides detailed reasoning and analysis of feature data
- Shows feature importance metrics and confidence scores
- Generates enhanced insights and more nuanced recommendations
- Offers explanations of how features influenced the outcomes

#### Traditional Mode
- Uses direct feature retrieval and processing without AI agent
- Provides standard feature-based outputs with simpler processing
- Delivers a streamlined experience with focused results
- Offers consistent performance with deterministic outcomes

## Architecture

The application consists of three main components:

1. **Feature Store (Feast)**: Stores and serves ML features
2. **Agentic Feature Store Service**: Uses AI to intelligently interact with the feature store, retrieve features, and generate insights
3. **Frontend Dashboard**: Visualizes the feature data, AI insights, and allows toggling between agent and traditional modes

![Architecture Diagram](./docs/architecture.md)

## Feature Store Workflow

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

### 2. Feature Retrieval

Features are retrieved using:
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

### 3. Feature Processing

Retrieved features are processed for specific use cases through:
1. **Feature Selection**: Select relevant features for the task
2. **Feature Transformation**: Apply necessary transformations
3. **Output Generation**: Generate appropriate outputs or predictions

```python
def process_feature_request(self, request: FeatureRequest) -> FeatureResponse:
    # Get feature service for the requested action type
    service = self.feature_store.get_feature_service(request.action_type)
    features = service.get_features()
    
    # Get online features
    online_features = self.feature_store.get_online_features(
        entity_rows=[{entity_id_key: request.entity_id}],
        features=features
    )
    
    # Process features based on the action type
    if request.action_type == "recommendation":
        result = self._process_recommendation(request.entity_id, online_features)
    elif request.action_type == "fraud_detection":
        result = self._process_fraud_detection(request.entity_id, online_features)
    elif request.action_type == "segmentation":
        result = self._process_customer_segmentation(request.entity_id, online_features)
    
    # Record the action in history
    self.add_to_history(action_type=f"get_{request.action_type}_features", 
                        description=f"Retrieved features for {entity_id_key} {request.entity_id}")
    
    return result
```

### 4. Result Presentation

Results are structured as `FeatureResponse` objects containing:
- Status information
- Processed data
- Recommendations or predictions

```python
return FeatureResponse(
    message=f"Retrieved features and generated product recommendations for customer {customer_id}",
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

### Feature Processing Implementation

The feature processing service handles:
- Retrieving relevant features for specific use cases
- Applying business logic to process the features
- Generating predictions or recommendations based on features
- Maintaining a history of feature retrieval operations

### Error Handling

The system implements robust error handling:
- If feature retrieval fails, uses defaults or cached values
- All errors are recorded in the feature history

### Feature Processing History

The service maintains a chronological history of all feature operations:
```python
def add_to_history(self, action_type: str, description: str, status: str = "success"):
    history_action = ActionHistory(
        timestamp=datetime.utcnow().isoformat(),
        action=action_type,
        description=description,
        status=status
    )
    self.action_history.insert(0, history_action)
```

## Use Cases

### Product Recommendations

1. Customer features are retrieved (age, income, purchase history)
2. Features are processed to determine customer preferences
3. Personalized product recommendations are generated
4. Recommendations are ranked by relevance score

### Fraud Detection

1. Transaction features and customer credit profile are retrieved
2. Features are analyzed for suspicious patterns
3. A fraud risk score is calculated
4. Risk factors are identified and explained

### Customer Segmentation

1. Comprehensive customer features are retrieved
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
```

## Technical Implementation Notes

### API Endpoints

- `/feature-views`: List all available feature views
- `/feature-services`: List all available feature services
- `/features/process`: Process a feature request
- `/features/history`: View feature retrieval history
- `/demo/recommendation`: Generate product recommendations from features
- `/demo/fraud-detection`: Analyze transaction features for fraud
- `/demo/customer-segmentation`: Segment a customer using their features

### Integration Points

- **Backend ↔ Feature Store**: Feature retrieval and storage
- **Frontend ↔ Backend**: API calls for feature requests
- **Frontend ↔ User**: Visualization and interaction

## Extending the System

### Adding New Feature Views
1. Define new feature views in the feature store
2. Register the features with appropriate metadata
3. Create feature services for specific use cases

### Adding New Feature Services
1. Implement a new feature service in the feature store
2. Create a new processing function for the service
3. Update the endpoints to support the new service
4. Update the UI to display the new service

### Connecting to Real Data Sources
1. Replace the mock feature store with a real Feast instance
2. Configure offline and online stores
3. Set up data ingestion pipelines
4. Update feature retrieval code as needed

## Conclusion

This feature store system demonstrates how to leverage a Feast feature store for machine learning tasks. By providing a unified interface for feature access and processing, the system enables consistent feature management for various ML applications.