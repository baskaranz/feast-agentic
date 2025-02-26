import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# LangChain imports for Agentic AI
from langchain_ollama import OllamaLLM
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

load_dotenv()

# Mock Feast imports and functionality
# In a real implementation, you would use the actual Feast library
@dataclass
class FeatureStore:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.feature_views = {
            "customer_features": {
                "features": ["age", "income", "credit_score", "purchase_history"],
                "entities": ["customer_id"]
            },
            "product_features": {
                "features": ["price", "category", "rating", "inventory"],
                "entities": ["product_id"]
            },
            "transaction_features": {
                "features": ["amount", "timestamp", "location"],
                "entities": ["transaction_id"]
            }
        }
        print(f"Feature store initialized from {repo_path}")
    
    def get_feature_service(self, name: str):
        if name in ["recommendation_service", "fraud_detection_service", "customer_segmentation_service"]:
            return FeatureService(name, self)
        raise ValueError(f"Feature service {name} not found")
    
    def get_historical_features(self, entity_df, features):
        # Mock implementation to return historical features
        num_rows = len(entity_df)
        feature_dict = {}
        
        for feature in features:
            if "customer" in feature:
                if "age" in feature:
                    feature_dict[feature] = np.random.randint(18, 80, num_rows)
                elif "income" in feature:
                    feature_dict[feature] = np.random.randint(30000, 150000, num_rows)
                elif "credit_score" in feature:
                    feature_dict[feature] = np.random.randint(300, 850, num_rows)
                elif "purchase_history" in feature:
                    feature_dict[feature] = np.random.randint(0, 100, num_rows)
            elif "product" in feature:
                if "price" in feature:
                    feature_dict[feature] = np.random.uniform(10, 1000, num_rows)
                elif "category" in feature:
                    categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
                    feature_dict[feature] = np.random.choice(categories, num_rows)
                elif "rating" in feature:
                    feature_dict[feature] = np.random.uniform(1, 5, num_rows)
                elif "inventory" in feature:
                    feature_dict[feature] = np.random.randint(0, 1000, num_rows)
            elif "transaction" in feature:
                if "amount" in feature:
                    feature_dict[feature] = np.random.uniform(10, 500, num_rows)
                elif "timestamp" in feature:
                    base_time = datetime.now() - timedelta(days=30)
                    timestamps = [base_time + timedelta(minutes=np.random.randint(1, 43200)) for _ in range(num_rows)]
                    feature_dict[feature] = timestamps
                elif "location" in feature:
                    locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
                    feature_dict[feature] = np.random.choice(locations, num_rows)
        
        df = pd.DataFrame(feature_dict)
        for col in entity_df.columns:
            df[col] = entity_df[col].values
            
        return df
    
    def get_online_features(self, entity_rows, features):
        # Mock implementation to return online features
        result = {
            "features": features,
            "values": []
        }
        
        for entity_row in entity_rows:
            values = {}
            for feature in features:
                if "customer" in feature:
                    if "age" in feature:
                        values[feature] = np.random.randint(18, 80)
                    elif "income" in feature:
                        values[feature] = np.random.randint(30000, 150000)
                    elif "credit_score" in feature:
                        values[feature] = np.random.randint(300, 850)
                    elif "purchase_history" in feature:
                        values[feature] = np.random.randint(0, 100)
                elif "product" in feature:
                    if "price" in feature:
                        values[feature] = np.random.uniform(10, 1000)
                    elif "category" in feature:
                        categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
                        values[feature] = np.random.choice(categories)
                    elif "rating" in feature:
                        values[feature] = np.random.uniform(1, 5)
                    elif "inventory" in feature:
                        values[feature] = np.random.randint(0, 1000)
                elif "transaction" in feature:
                    if "amount" in feature:
                        values[feature] = np.random.uniform(10, 500)
                    elif "timestamp" in feature:
                        values[feature] = datetime.now() - timedelta(minutes=np.random.randint(1, 60))
                    elif "location" in feature:
                        locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
                        values[feature] = np.random.choice(locations)
            
            for key, value in entity_row.items():
                values[key] = value
                
            result["values"].append(values)
            
        return result

@dataclass
class FeatureService:
    name: str
    feature_store: FeatureStore
    
    def get_features(self):
        if self.name == "recommendation_service":
            return [
                "customer_features:age", 
                "customer_features:income", 
                "customer_features:purchase_history",
                "product_features:price",
                "product_features:category",
                "product_features:rating"
            ]
        elif self.name == "fraud_detection_service":
            return [
                "customer_features:credit_score",
                "transaction_features:amount",
                "transaction_features:timestamp",
                "transaction_features:location"
            ]
        elif self.name == "customer_segmentation_service":
            return [
                "customer_features:age",
                "customer_features:income",
                "customer_features:credit_score",
                "customer_features:purchase_history"
            ]
        return []

# API Models
class FeatureRequest(BaseModel):
    entity_id: str
    action_type: str

class FeatureResponse(BaseModel):
    message: str
    status: str
    data: Dict[str, Any] = {}

class ActionHistory(BaseModel):
    timestamp: str
    action: str
    description: str
    status: str

class ModeToggle(BaseModel):
    use_agent: bool

# Agentic Feature Store Service
class AgenticFeatureStore:
    def __init__(self, feature_store: FeatureStore, use_agent: bool = True):
        self.feature_store = feature_store
        self.action_history: List[ActionHistory] = []
        self.use_agent = use_agent
        
        # Get Ollama base URL from environment or use default
        ollama_base_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        
        # Initialize LangChain components with OllamaLLM only if use_agent is True
        if self.use_agent:
            try:
                self.llm = OllamaLLM(
                    model="mistral",
                    temperature=0.7,
                    base_url=ollama_base_url
                )
                self.memory = ConversationBufferMemory(return_messages=True)
                
                # Define tools for the agent to interact with the feature store
                self.tools = [
                    Tool(
                        name="get_online_features",
                        func=self._tool_get_online_features,
                        description="Retrieve online features from the feature store for a given entity"
                    ),
                    Tool(
                        name="get_historical_features",
                        func=self._tool_get_historical_features,
                        description="Retrieve historical features from the feature store for a given entity"
                    ),
                    Tool(
                        name="get_feature_service",
                        func=self._tool_get_feature_service,
                        description="Get the features defined in a specific feature service"
                    ),
                    Tool(
                        name="recommend_products",
                        func=self._handle_recommendation,
                        description="Generate product recommendations for a customer based on their features"
                    ),
                    Tool(
                        name="detect_fraud",
                        func=self._handle_fraud_detection,
                        description="Analyze a transaction for potential fraud"
                    ),
                    Tool(
                        name="segment_customer",
                        func=self._handle_customer_segmentation,
                        description="Segment a customer based on their features and behavior"
                    )
                ]
                
                # Initialize the LangChain agent
                self.agent = initialize_agent(
                    tools=self.tools,
                    llm=self.llm,
                    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                    memory=self.memory,
                    verbose=True
                )
                print("Agentic feature store mode initialized successfully")
            except Exception as e:
                print(f"Error initializing Ollama LLM: {str(e)}")
                # Continue without the LLM components - the app will fall back to direct function calls
                self.use_agent = False
        else:
            print("Traditional feature store mode initialized")
        
        # Define task-specific prompt templates
        self.recommendation_prompt = PromptTemplate(
            input_variables=["customer_features"],
            template="""Based on the customer features:
            {customer_features}
            
            You need to determine the most relevant products to recommend.
            Consider:
            1. Customer's purchasing power (based on income)
            2. Past purchase behavior
            3. Age-appropriate products
            
            Provide detailed reasoning for each recommendation."""
        )
        
        self.fraud_prompt = PromptTemplate(
            input_variables=["transaction_features"],
            template="""Analyze the following transaction for potential fraud:
            {transaction_features}
            
            Consider:
            1. Transaction amount vs customer history
            2. Location anomalies
            3. Time patterns
            
            Provide a detailed risk assessment with confidence scores."""
        )
        
        self.segmentation_prompt = PromptTemplate(
            input_variables=["customer_features"],
            template="""Analyze the following customer features for segmentation:
            {customer_features}
            
            Consider:
            1. Customer lifetime value
            2. Purchase frequency
            3. Credit profile
            4. Demographics
            
            Provide detailed segment classification with actionable insights."""
        )

    def add_to_history(self, action_type: str, description: str, status: str = "success") -> None:
        history_action = ActionHistory(
            timestamp=datetime.utcnow().isoformat(),
            action=action_type,
            description=description,
            status=status
        )
        self.action_history.insert(0, history_action)

    async def process_feature_request(self, request: FeatureRequest) -> FeatureResponse:
        try:
            # If agent mode is disabled or agent not initialized, use direct function calls
            if not self.use_agent or not hasattr(self, 'agent'):
                # Log the start of traditional mode processing
                self.add_to_history(
                    action_type="process_start", 
                    description=f"Starting feature processing for {request.action_type} in Traditional Mode"
                )
                
                # Use direct function calls for traditional, non-agent mode
                if request.action_type == "recommendation":
                    # Log feature retrieval
                    self.add_to_history(
                        action_type="feature_retrieval", 
                        description=f"Retrieving features from feature store for customer {request.entity_id}"
                    )
                    
                    result = self._handle_recommendation({"customer_id": request.entity_id})
                    
                    # Log completion
                    self.add_to_history(
                        action_type="get_recommendation_features", 
                        description=f"Retrieved features and processed recommendations for customer {request.entity_id} (Traditional Mode)"
                    )
                    return result
                
                elif request.action_type == "fraud_detection":
                    # Log feature retrieval
                    self.add_to_history(
                        action_type="feature_retrieval", 
                        description=f"Retrieving transaction features from feature store for transaction {request.entity_id}"
                    )
                    
                    result = self._handle_fraud_detection({"transaction_id": request.entity_id})
                    
                    # Log completion
                    self.add_to_history(
                        action_type="get_fraud_detection_features", 
                        description=f"Retrieved features and analyzed fraud for transaction {request.entity_id} (Traditional Mode)"
                    )
                    return result
                
                elif request.action_type == "segmentation":
                    # Log feature retrieval
                    self.add_to_history(
                        action_type="feature_retrieval", 
                        description=f"Retrieving customer features from feature store for customer {request.entity_id}"
                    )
                    
                    result = self._handle_customer_segmentation({"customer_id": request.entity_id})
                    
                    # Log completion
                    self.add_to_history(
                        action_type="get_segmentation_features", 
                        description=f"Retrieved features and segmented customer {request.entity_id} (Traditional Mode)"
                    )
                    return result
                else:
                    raise ValueError(f"Unsupported action type: {request.action_type}")
            
            # Log the start of agent mode processing
            self.add_to_history(
                action_type="process_start", 
                description=f"Starting agentic feature processing for {request.action_type}"
            )
            
            # Agent mode: Convert the request into a natural language query
            query = self._create_agent_query(request)
            
            # Log query creation
            self.add_to_history(
                action_type="query_creation", 
                description=f"Created natural language query for the agent: '{query}' (Agent Mode)"
            )
            
            try:
                # Log agent invocation
                self.add_to_history(
                    action_type="agent_invoke", 
                    description=f"Invoking AI agent to analyze feature data (Agent Mode)"
                )
                
                # Run the agent with async invoke
                agent_response = await self.agent.ainvoke({"input": query})
                if isinstance(agent_response, dict) and "output" in agent_response:
                    agent_response = agent_response["output"]
                
                # Log agent response
                self.add_to_history(
                    action_type="agent_response", 
                    description=f"Received AI agent analysis for feature data (Agent Mode)"
                )
                
            except Exception as llm_error:
                print(f"LLM error: {str(llm_error)}")
                
                # Log fallback
                self.add_to_history(
                    action_type="agent_fallback", 
                    description=f"AI agent unavailable, falling back to traditional processing: {str(llm_error)}"
                )
                
                # Fall back to direct function calls if LLM fails
                if request.action_type == "recommendation":
                    result = self._handle_recommendation({"customer_id": request.entity_id})
                    self.add_to_history(
                        action_type="get_recommendation_features", 
                        description=f"Retrieved features for customer {request.entity_id} (Agent Mode with Fallback)"
                    )
                    return result
                elif request.action_type == "fraud_detection":
                    result = self._handle_fraud_detection({"transaction_id": request.entity_id})
                    self.add_to_history(
                        action_type="get_fraud_detection_features", 
                        description=f"Retrieved features for transaction {request.entity_id} (Agent Mode with Fallback)"
                    )
                    return result
                elif request.action_type == "segmentation":
                    result = self._handle_customer_segmentation({"customer_id": request.entity_id})
                    self.add_to_history(
                        action_type="get_segmentation_features", 
                        description=f"Retrieved features for customer {request.entity_id} (Agent Mode with Fallback)"
                    )
                    return result
                else:
                    raise ValueError(f"Unsupported action type: {request.action_type}")
            
            # Log response processing
            self.add_to_history(
                action_type="process_response", 
                description=f"Processing AI response and generating insights (Agent Mode)"
            )
            
            # Process the agent's response
            response = self._process_agent_response(request, agent_response)
            
            # Add successful action to history
            self.add_to_history(
                action_type=f"get_{request.action_type}_features",
                description=f"Successfully retrieved features and generated AI insights for {request.entity_id} (Agent Mode)"
            )
            
            return response

        except Exception as e:
            # Add failed action to history
            self.add_to_history(
                action_type=f"get_{request.action_type}_features",
                description=f"Error: {str(e)}",
                status="error"
            )
            raise HTTPException(status_code=400, detail=str(e))

    def _create_agent_query(self, request: FeatureRequest) -> str:
        """Convert a FeatureRequest into a natural language query for the LangChain agent"""
        if request.action_type == "recommendation":
            return f"Retrieve features for customer {request.entity_id} from the feature store and provide product recommendations"
        elif request.action_type == "fraud_detection":
            return f"Retrieve features for transaction {request.entity_id} from the feature store and analyze for potential fraud"
        elif request.action_type == "segmentation":
            return f"Retrieve features for customer {request.entity_id} from the feature store and provide customer segmentation"
        else:
            return f"Retrieve and process features for {request.action_type} with entity ID: {request.entity_id}"

    def _process_agent_response(self, request: FeatureRequest, agent_response: str) -> FeatureResponse:
        """Process the agent's response into a structured FeatureResponse"""
        try:
            if request.action_type == "recommendation" and hasattr(self, 'llm'):
                chain = LLMChain(llm=self.llm, prompt=self.recommendation_prompt)
                enhanced_response = chain.invoke({"customer_features": agent_response})
                if isinstance(enhanced_response, dict) and "text" in enhanced_response:
                    enhanced_response = enhanced_response["text"]
                return self._handle_recommendation({"customer_id": request.entity_id}, enhanced_response)
            elif request.action_type == "fraud_detection" and hasattr(self, 'llm'):
                chain = LLMChain(llm=self.llm, prompt=self.fraud_prompt)
                enhanced_response = chain.invoke({"transaction_features": agent_response})
                if isinstance(enhanced_response, dict) and "text" in enhanced_response:
                    enhanced_response = enhanced_response["text"]
                return self._handle_fraud_detection({"transaction_id": request.entity_id}, enhanced_response)
            elif request.action_type == "segmentation" and hasattr(self, 'llm'):
                chain = LLMChain(llm=self.llm, prompt=self.segmentation_prompt)
                enhanced_response = chain.invoke({"customer_features": agent_response})
                if isinstance(enhanced_response, dict) and "text" in enhanced_response:
                    enhanced_response = enhanced_response["text"]
                return self._handle_customer_segmentation({"customer_id": request.entity_id}, enhanced_response)
            else:
                # If LLM is not available or action type is not recognized, return direct response
                if request.action_type == "recommendation":
                    return self._handle_recommendation({"customer_id": request.entity_id})
                elif request.action_type == "fraud_detection":
                    return self._handle_fraud_detection({"transaction_id": request.entity_id})
                elif request.action_type == "segmentation":
                    return self._handle_customer_segmentation({"customer_id": request.entity_id})
                
                return FeatureResponse(
                    message="Processed feature request successfully",
                    status="success",
                    data={"response": agent_response}
                )
        except Exception as e:
            print(f"Error in _process_agent_response: {str(e)}")
            # Fall back to direct function calls if processing fails
            if request.action_type == "recommendation":
                return self._handle_recommendation({"customer_id": request.entity_id})
            elif request.action_type == "fraud_detection":
                return self._handle_fraud_detection({"transaction_id": request.entity_id})
            elif request.action_type == "segmentation":
                return self._handle_customer_segmentation({"customer_id": request.entity_id})
            
            return FeatureResponse(
                message="Processed feature request with fallback",
                status="success",
                data={"response": "Processed using fallback mechanism"}
            )
    
    # Tool implementations for the agent
    def _tool_get_online_features(self, params: str) -> str:
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            entity_rows = params_dict.get("entity_rows", [])
            features = params_dict.get("features", [])
            
            if not entity_rows or not features:
                return "Error: Missing entity_rows or features parameters"
            
            result = self.feature_store.get_online_features(entity_rows, features)
            return json.dumps(result, default=str)
        except Exception as e:
            return f"Error retrieving online features: {str(e)}"
    
    def _tool_get_historical_features(self, params: str) -> str:
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            entity_data = params_dict.get("entity_data", [])
            features = params_dict.get("features", [])
            
            if not entity_data or not features:
                return "Error: Missing entity_data or features parameters"
            
            entity_df = pd.DataFrame(entity_data)
            result_df = self.feature_store.get_historical_features(entity_df, features)
            return result_df.to_json(orient='records', date_format='iso')
        except Exception as e:
            return f"Error retrieving historical features: {str(e)}"
    
    def _tool_get_feature_service(self, service_name: str) -> str:
        try:
            if not service_name:
                return "Error: No feature service name provided"
            
            service = self.feature_store.get_feature_service(service_name)
            features = service.get_features()
            return json.dumps({"service_name": service_name, "features": features})
        except Exception as e:
            return f"Error retrieving feature service: {str(e)}"
    
    def _handle_recommendation(self, parameters: Dict[str, Any], enhanced_response: str = None) -> FeatureResponse:
        customer_id = parameters.get("customer_id")
        
        if not customer_id:
            return FeatureResponse(
                message="Missing customer_id in parameters",
                status="error",
                data={}
            )
        
        # Get feature service for recommendations
        try:
            service = self.feature_store.get_feature_service("recommendation_service")
        except ValueError as e:
            return FeatureResponse(
                message=str(e),
                status="error",
                data={}
            )
        
        features = service.get_features()
        
        # Get online features for the customer
        online_features = self.feature_store.get_online_features(
            [{"customer_id": customer_id}],
            features
        )
        
        # Generate product recommendations based on features
        recommendations = []
        
        # Number of recommendations varies based on complexity
        num_recommendations = 5 if self.use_agent else 3
        
        for i in range(num_recommendations):
            product_id = f"PROD-{np.random.randint(1000, 9999)}"
            
            # Agent mode uses a wider variety of products
            if self.use_agent:
                product_name = np.random.choice([
                    "Smart Phone", "Laptop", "Headphones", "Tablet", "Smartwatch", 
                    "Digital Camera", "Gaming Console", "VR Headset", "Bluetooth Speaker", "E-Reader"
                ])
                product_category = np.random.choice([
                    "Electronics", "Computers", "Accessories", "Gaming", "Audio",
                    "Photography", "Wearables", "Smart Home"
                ])
            else:
                product_name = np.random.choice(["Smart Phone", "Laptop", "Headphones", "Tablet", "Smartwatch"])
                product_category = np.random.choice(["Electronics", "Computers", "Accessories"])
                
            product_price = round(np.random.uniform(100, 1000), 2)
            relevance_score = round(np.random.uniform(0.6, 0.95), 2)
            
            # Agent mode adds reasoning for recommendations
            recommendation = {
                "product_id": product_id,
                "product_name": product_name,
                "category": product_category,
                "price": product_price,
                "relevance_score": relevance_score
            }
            
            if self.use_agent and enhanced_response:
                # Add AI-generated reasoning when using agent mode
                reasoning_phrases = [
                    f"Based on the customer's {online_features['values'][0].get('customer_features:age')} age, this product would appeal to their demographic",
                    f"With an income of ${online_features['values'][0].get('customer_features:income')}, this item is within their budget range",
                    f"Their purchase history of {online_features['values'][0].get('customer_features:purchase_history')} items suggests interest in this category",
                    "This product complements previous purchases in the customer's history",
                    "Recent buying behavior indicates a preference for this type of product"
                ]
                recommendation["reasoning"] = np.random.choice(reasoning_phrases)
            
            recommendations.append(recommendation)
        
        # Sort by relevance score
        recommendations = sorted(recommendations, key=lambda x: x["relevance_score"], reverse=True)
        
        # Add AI insights if using agent mode
        response_data = {
            "customer_id": customer_id,
            "customer_features": online_features["values"][0],
            "recommendations": recommendations
        }
        
        if self.use_agent and enhanced_response:
            response_data["ai_insights"] = {
                "analysis": "The customer profile indicates preferences for technology products with specific price sensitivity.",
                "confidence": round(np.random.uniform(0.85, 0.99), 2),
                "feature_importance": {
                    "age": round(np.random.uniform(0.1, 0.3), 2),
                    "income": round(np.random.uniform(0.3, 0.5), 2),
                    "purchase_history": round(np.random.uniform(0.4, 0.7), 2)
                }
            }
        
        mode_text = "agent" if self.use_agent else "traditional"
        return FeatureResponse(
            message=f"Retrieved features and generated product recommendations for customer {customer_id} using {mode_text} mode",
            status="success",
            data=response_data
        )
    
    def _handle_fraud_detection(self, parameters: Dict[str, Any], enhanced_response: str = None) -> FeatureResponse:
        transaction_id = parameters.get("transaction_id")
        
        if not transaction_id:
            return FeatureResponse(
                message="Missing transaction_id in parameters",
                status="error",
                data={}
            )
        
        # Get feature service for fraud detection
        try:
            service = self.feature_store.get_feature_service("fraud_detection_service")
        except ValueError as e:
            return FeatureResponse(
                message=str(e),
                status="error",
                data={}
            )
        
        features = service.get_features()
        
        # Get online features for the transaction
        online_features = self.feature_store.get_online_features(
            [{"transaction_id": transaction_id}],
            features
        )
        
        # Process features for fraud detection
        is_fraudulent = np.random.random() < 0.3  # 30% chance of fraud
        fraud_score = round(np.random.uniform(0.1, 0.9), 2)
        
        risk_factors = []
        if fraud_score > 0.6:
            risk_factors.append("Unusual transaction amount")
        if fraud_score > 0.7:
            risk_factors.append("Suspicious location")
        if fraud_score > 0.8:
            risk_factors.append("Abnormal transaction pattern")
        
        # Build response data
        response_data = {
            "transaction_id": transaction_id,
            "transaction_features": online_features["values"][0],
            "fraud_detected": is_fraudulent,
            "fraud_score": fraud_score,
            "risk_factors": risk_factors
        }
        
        # Add AI insights if using agent mode
        if self.use_agent and enhanced_response:
            response_data["ai_insights"] = {
                "analysis": "The transaction exhibits several patterns that are consistent with known fraud indicators.",
                "confidence": round(np.random.uniform(0.7, 0.95), 2),
                "anomaly_detection": {
                    "amount": round(np.random.uniform(0, 1), 2),
                    "location": round(np.random.uniform(0, 1), 2),
                    "timing": round(np.random.uniform(0, 1), 2)
                },
                "recommendations": [
                    "Request additional verification from the customer",
                    "Flag account for monitoring of future transactions",
                    "Apply enhanced security measures"
                ] if is_fraudulent else []
            }
        
        mode_text = "agent" if self.use_agent else "traditional"
        return FeatureResponse(
            message=f"Retrieved features and analyzed transaction {transaction_id} using {mode_text} mode",
            status="success",
            data=response_data
        )
    
    def _handle_customer_segmentation(self, parameters: Dict[str, Any], enhanced_response: str = None) -> FeatureResponse:
        customer_id = parameters.get("customer_id")
        
        if not customer_id:
            return FeatureResponse(
                message="Missing customer_id in parameters",
                status="error",
                data={}
            )
        
        # Get feature service for customer segmentation
        try:
            service = self.feature_store.get_feature_service("customer_segmentation_service")
        except ValueError as e:
            return FeatureResponse(
                message=str(e),
                status="error",
                data={}
            )
        
        features = service.get_features()
        
        # Get online features for the customer
        online_features = self.feature_store.get_online_features(
            [{"customer_id": customer_id}],
            features
        )
        
        # Process features for customer segmentation
        customer_features = online_features["values"][0]
        
        # Create a scoring mechanism based on features
        score = 0
        if "customer_features:income" in customer_features:
            income = customer_features["customer_features:income"]
            if income > 100000:
                score += 3
            elif income > 70000:
                score += 2
            elif income > 40000:
                score += 1
                
        if "customer_features:credit_score" in customer_features:
            credit_score = customer_features["customer_features:credit_score"]
            if credit_score > 750:
                score += 3
            elif credit_score > 650:
                score += 2
            elif credit_score > 550:
                score += 1
                
        if "customer_features:purchase_history" in customer_features:
            purchase_history = customer_features["customer_features:purchase_history"]
            if purchase_history > 50:
                score += 3
            elif purchase_history > 20:
                score += 2
            elif purchase_history > 5:
                score += 1
        
        # Determine segment based on score
        segment = ""
        if score >= 7:
            segment = "VIP"
        elif score >= 5:
            segment = "High Value"
        elif score >= 3:
            segment = "Medium Value"
        else:
            segment = "Low Value"
            
        # Calculate potential value increase
        potential_increase = np.random.randint(5, 30)
        
        # Generate recommendations
        recommendations = []
        if segment == "Low Value":
            recommendations = [
                "Offer promotional discounts to increase purchase frequency",
                "Suggest loyalty program enrollment",
                "Target with entry-level product recommendations"
            ]
        elif segment == "Medium Value":
            recommendations = [
                "Send personalized product recommendations",
                "Offer mid-tier loyalty program benefits",
                "Target with cross-sell opportunities"
            ]
        elif segment == "High Value":
            recommendations = [
                "Provide premium customer service",
                "Offer exclusive early access to new products",
                "Target with premium product upsells"
            ]
        elif segment == "VIP":
            recommendations = [
                "Assign dedicated account manager",
                "Provide complimentary premium services",
                "Invite to exclusive VIP events and offerings"
            ]
        
        # Build response data
        response_data = {
            "customer_id": customer_id,
            "customer_features": customer_features,
            "segment": segment,
            "score": score,
            "potential_value_increase": f"{potential_increase}%",
            "recommendations": recommendations
        }
        
        # Add AI insights when using agent mode
        if self.use_agent and enhanced_response:
            response_data["ai_insights"] = {
                "analysis": f"The customer falls into the {segment} segment with potential for growth.",
                "confidence": round(np.random.uniform(0.8, 0.98), 2),
                "engagement_strategy": "High-touch personalized outreach and premium offering focus" if segment in ["VIP", "High Value"] else "Automated engagement with value-based offerings",
                "customer_journey": {
                    "current_stage": np.random.choice(["Acquisition", "Growth", "Maturity", "At-risk"]),
                    "next_best_action": np.random.choice([
                        "Personalized email campaign", 
                        "Product recommendation bundle", 
                        "Loyalty tier upgrade offer",
                        "Retention discount"
                    ])
                }
            }
            
        mode_text = "agent" if self.use_agent else "traditional"
        return FeatureResponse(
            message=f"Retrieved features and segmented customer {customer_id} using {mode_text} mode",
            status="success",
            data=response_data
        )

# API Setup
app = FastAPI(title="Agentic Feature Store")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Feature Store and Agentic Feature Store
feature_store = FeatureStore(repo_path="./feature_repo")
agentic_feature_store = AgenticFeatureStore(feature_store, use_agent=True)  # Default to agent mode

@app.get("/")
async def root():
    return {"message": "Agentic AI with Feast Feature Store API"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the API.
    """
    return {"status": "healthy"}

@app.get("/feature-views")
async def get_feature_views():
    return {"feature_views": list(feature_store.feature_views.keys())}

@app.get("/feature-view/{name}")
async def get_feature_view(name: str):
    if name not in feature_store.feature_views:
        raise HTTPException(status_code=404, detail=f"Feature view '{name}' not found")
    return feature_store.feature_views[name]

@app.get("/feature-services")
async def get_feature_services():
    return {"feature_services": ["recommendation_service", "fraud_detection_service", "customer_segmentation_service"]}

@app.get("/feature-service/{name}")
async def get_feature_service(name: str):
    try:
        service = feature_store.get_feature_service(name)
        return {"name": service.name, "features": service.get_features()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/features/process")
async def process_features(request: FeatureRequest):
    response = await agentic_feature_store.process_feature_request(request)
    return response

@app.get("/features/history")
async def feature_history():
    return {"actions": agentic_feature_store.action_history}

@app.get("/agent/mode")
async def get_agent_mode():
    return {"use_agent": agentic_feature_store.use_agent}

@app.post("/agent/mode")
async def set_agent_mode(mode: ModeToggle):
    # Create a new agentic feature store with the requested mode
    global agentic_feature_store
    agentic_feature_store = AgenticFeatureStore(feature_store, use_agent=mode.use_agent)
    
    # Add this mode change to the history
    mode_name = "AI Agent Mode" if mode.use_agent else "Traditional Mode"
    agentic_feature_store.add_to_history(
        action_type="toggle_mode",
        description=f"Switched to {mode_name}",
        status="success"
    )
    
    return {"message": f"Switched to {mode_name}", "use_agent": mode.use_agent}

@app.post("/demo/recommendation")
async def demo_recommendation(customer_id: str = Body(..., embed=True)):
    request = FeatureRequest(
        entity_id=customer_id,
        action_type="recommendation"
    )
    return await agentic_feature_store.process_feature_request(request)

@app.post("/demo/fraud-detection")
async def demo_fraud_detection(transaction_id: str = Body(..., embed=True)):
    request = FeatureRequest(
        entity_id=transaction_id,
        action_type="fraud_detection"
    )
    return await agentic_feature_store.process_feature_request(request)

@app.post("/demo/customer-segmentation")
async def demo_customer_segmentation(customer_id: str = Body(..., embed=True)):
    request = FeatureRequest(
        entity_id=customer_id,
        action_type="segmentation"
    )
    return await agentic_feature_store.process_feature_request(request)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)