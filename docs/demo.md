# Agentic AI with Feast Feature Store - Demo Interface

```mermaid
%%{init: {'theme': 'forest', 'themeVariables': { 'primaryColor': '#5D8AA8', 'primaryTextColor': '#fff', 'primaryBorderColor': '#1A5276', 'lineColor': '#1A5276', 'secondaryColor': '#A9CCE3', 'tertiaryColor': '#D4E6F1' }}}%%

graph TB
    subgraph Dashboard["Agentic AI Dashboard"]
        subgraph TabsSection["Tab Navigation"]
            Tab1["Product Recommendations"]
            Tab2["Fraud Detection"]
            Tab3["Customer Segmentation"]
        end
        
        subgraph InputsSection["User Inputs"]
            CustomerID["Customer ID: CUST-1234"]
            TransactionID["Transaction ID: TX-5678"]
            RunButton["Run Agent"]
        end
        
        subgraph ResultsSection["Results Panel"]
            subgraph CustomerInfo["Customer Information"]
                Age["Age: 34"]
                Income["Income: $85,000"]
                CreditScore["Credit Score: 720"]
                PurchaseHistory["Purchase History: 28 items"]
            end
            
            subgraph RecommendationResults["Recommendations"]
                Rec1["MacBook Pro - 92% match"]
                Rec2["AirPods Pro - 87% match"]
                Rec3["iPad Air - 79% match"]
            end
            
            subgraph VisualizationSection["Visualization"]
                MatchChart["Product Match Score Chart"]
            end
        end
        
        subgraph SidebarSection["Sidebar"]
            subgraph AgentActivity["Agent Activity"]
                Activity1["10:23:45 - make_recommendation - success"]
                Activity2["10:22:30 - get_feature_info - success"]
                Activity3["10:21:15 - detect_fraud - success"]
            end
            
            subgraph FeatureStoreInfo["Feature Store Information"]
                FeatureViews["Feature Views:
                - customer_features
                - product_features
                - transaction_features"]
                
                FeatureServices["Feature Services:
                - recommendation_service
                - fraud_detection_service
                - segmentation_service"]
            end
        end
    end
    
    TabsSection --> InputsSection
    InputsSection --> ResultsSection
    
    classDef primary fill:#E1F5FE,stroke:#01579B,stroke-width:2px
    classDef section fill:#F5F5F5,stroke:#9E9E9E,stroke-width:1px
    classDef button fill:#2196F3,stroke:#0D47A1,color:white,stroke-width:1px
    classDef results fill:#E8F5E9,stroke:#2E7D32,stroke-width:1px
    classDef activity fill:#FFF3E0,stroke:#E65100,stroke-width:1px
    
    class Dashboard primary
    class TabsSection,InputsSection,SidebarSection section
    class RunButton button
    class ResultsSection,CustomerInfo,RecommendationResults,VisualizationSection results
    class AgentActivity,Activity1,Activity2,Activity3 activity
```

## Dashboard Components

### 1. Tab Navigation
Users can select different AI agent capabilities:
- Product Recommendations
- Fraud Detection
- Customer Segmentation

### 2. User Inputs
- Customer ID input for recommendations and segmentation
- Transaction ID input for fraud detection
- Run Agent button to execute the selected agent action

### 3. Results Panel
Dynamic content based on the selected tab:

**For Recommendations:**
- Customer information (age, income, purchase history)
- Product recommendations sorted by match score
- Visualization of match scores

**For Fraud Detection:**
- Transaction details
- Fraud risk assessment with score
- Risk factors identified

**For Customer Segmentation:**
- Comprehensive customer profile
- Segment assignment with explanation
- Recommended strategies for the segment

### 4. Sidebar
- **Agent Activity Log**: Chronological history of agent actions
- **Feature Store Information**: Available feature views and services