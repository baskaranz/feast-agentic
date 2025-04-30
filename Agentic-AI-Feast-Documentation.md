# Agentic AI with Feast Feature Store

![Project Demo](./docs/demo.md)

## Overview

This project demonstrates an enhanced Agentic AI system for interacting with a Feast feature store. The system combines offline file storage and SQLite online storage with AI agent capabilities for autonomous feature engineering, feature selection, and model scoring.

### AI Agent vs Traditional Mode

The system supports two processing modes that can be toggled via the UI:

#### AI Agent Mode
- Uses an AI agent to intelligently interact with the feature store
- Provides detailed reasoning and analysis of feature data
- Shows feature importance metrics and confidence scores
- Generates enhanced insights and more nuanced recommendations
- Offers explanations of how features influenced the outcomes
- **Automatically creates feature services when user clicks "Get Features"**
- **Analyzes data sources to identify potential features for each use case**
- **Autonomously selects the most relevant features for specific use cases**
- **Creates optimal feature views and services without requiring explicit user action**

#### Traditional Mode
- Uses direct feature retrieval and processing without AI agent
- Provides standard feature-based outputs with simpler processing
- Delivers a streamlined experience with focused results
- Offers consistent performance with deterministic outcomes

## Architecture

The application consists of four main components:

1. **Offline Store**: CSV files for historical feature data, stored in the `backend/offline_store` directory
2. **Online Store**: SQLite database for low-latency feature serving, stored in `backend/feature_store.db`
3. **Agentic Feature Store Service**: Uses AI to intelligently interact with the feature store, retrieve features, and generate insights
4. **Frontend Dashboard**: Visualizes the feature data, AI insights, and allows toggling between agent and traditional modes

![Architecture Diagram](./docs/architecture.md)

## Feature Store Workflow

### 1. Feature Registration and Storage

#### Offline Store (CSV Files)
Features are stored in CSV files in the `backend/offline_store` directory. Each feature view has its own CSV file:
- `customer_features.csv`: Customer-related features
- `product_features.csv`: Product-related features
- `transaction_features.csv`: Transaction-related features

#### Online Store (SQLite)
Features are stored in a SQLite database (`backend/feature_store.db`) for low-latency serving, with tables for each feature view:
- `customer_features`: Customer-related features
- `product_features`: Product-related features
- `transaction_features`: Transaction-related features

#### Feature Views and Services
Features are registered in the Feast feature store with appropriate metadata:
- **Feature Views**: Define logical groupings of features (e.g., customer_features, product_features)
- **Feature Services**: Define collections of features for specific use cases
- **Entity**: Define the keys used to retrieve features (e.g., customer_id, product_id)

### 2. Autonomous Feature Engineering (Agentic Mode Only)

When a user clicks "Get Features" in Agent Mode, the system automatically:
1. **Analyze Data Sources**: Examines CSV files to identify potential features for the use case
2. **Generate Feature Suggestions**: Determines the most relevant features for the specific use case
3. **Create Feature Service**: Builds a custom feature service tailored to the use case
4. **Use Custom Service**: Retrieves features using the newly created service
5. **Track Process**: Logs each step in the action history for transparency

All of this happens automatically without requiring any additional user action beyond clicking "Get Features". The system creates a custom service named `agentic_{use_case}_service` and uses it for future requests of the same type.

### 3. Feature Retrieval

Features are retrieved using:
- **Online Features**: Real-time feature values from SQLite for current predictions
- **Historical Features**: Past feature values from CSV files for training or analysis

### 4. Feature Processing

Retrieved features are processed for specific use cases through:
1. **Feature Selection**: Select relevant features for the task
2. **Feature Transformation**: Apply necessary transformations
3. **Output Generation**: Generate appropriate outputs or predictions

### 5. Result Presentation

Results are structured as `FeatureResponse` objects containing:
- Status information
- Processed data
- Recommendations or predictions
- AI-generated insights (in Agent Mode)

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

## New Feature Store Capabilities

### Offline File Store
- CSV-based storage for historical feature data
- Easy to inspect and modify feature values
- Scalable for large datasets
- Perfect for demonstration and development

### SQLite Online Store
- Low-latency feature serving for real-time model scoring
- Persistent storage across application restarts
- Familiar SQL interface for queries
- No external dependencies

### Autonomous Feature Management
- **One-Click Feature Engineering**: Automatically creates feature services when user clicks "Get Features"
- **Data Source Analysis**: Analyzes CSV files to identify the most relevant features for each use case
- **Intelligent Feature Selection**: Selects optimal features based on the specific use case requirements
- **Custom Service Creation**: Creates and uses custom feature services without explicit user action
- **Transparent Process**: Logs each step of the autonomous process in the action history for visibility

## API Endpoints

### Feature Store Management
- `GET /feature-views`: Get all available feature views
- `GET /feature-view/{name}`: Get details of a specific feature view
- `GET /feature-services`: Get all available feature services
- `GET /feature-service/{name}`: Get details of a specific feature service

### Agentic Feature Store Capabilities
- `POST /feature-views/create`: Create a new feature view
- `POST /feature-services/create`: Create a new feature service
- `POST /data-source/analyze`: Analyze a data source for potential features
- `POST /features/suggest`: Suggest features for a specific use case
- `GET /stores/info`: Get information about offline and online stores

### Feature Retrieval and Use Cases
- `POST /features/process`: Process feature requests
- `POST /demo/recommendation`: Generate product recommendations
- `POST /demo/fraud-detection`: Detect fraudulent transactions
- `POST /demo/customer-segmentation`: Segment customers

### Agent Management
- `GET /agent/mode`: Get current agent mode
- `POST /agent/mode`: Set agent mode (traditional vs. agentic)
- `GET /features/history`: Get feature processing history

## Running the Application

### Docker Setup
```bash
# Development mode with local files
docker-compose up

# Production mode with pre-built images
docker-compose -f docker-compose.prod.yml up
```

### Quick Try with Docker Compose
You can build and run the Docker images locally with Docker Compose:

```bash
# Build and run the Docker images with the flow diagram feature
git checkout feature/processing-flow-diagram  # Make sure you're on the feature branch
docker-compose up --build
```

The application will be available at http://localhost:3000. The flow diagram visualization feature will be included in the built Docker images.

### Manual Setup
```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm install reactflow  # Required for the flow diagram feature
npm start

# Ollama (required for LLM)
ollama run mistral
```

## Extending the System

### Adding New Data Sources
1. Add new CSV files to the `backend/offline_store` directory
2. Toggle AI Agent mode ON in the UI
3. Select your use case and click "Get Features"
4. The system will automatically analyze the new data source and create appropriate feature services

You can also manually manage data sources and feature views using the API:
1. Analyze a data source: `POST /data-source/analyze`
2. Create a feature view: `POST /feature-views/create`
3. Create a feature service: `POST /feature-services/create`
4. Get feature suggestions: `POST /features/suggest`

### Connecting to Real Feast
To connect to a real Feast instance:
1. Replace the mock feature store implementation with the real Feast client
2. Update the offline and online store configurations
3. Implement the feature view and feature service registration

## Conclusion

This enhanced Feast feature store system demonstrates how to leverage offline file storage, SQLite online storage, and Agentic AI for autonomous feature engineering and model scoring. By combining the simplicity of file-based storage with the low-latency of SQLite and the intelligence of AI agents, the system enables powerful yet accessible feature management for various ML applications.