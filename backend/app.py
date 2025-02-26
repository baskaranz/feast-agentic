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

# Updated imports for LangChain
from langchain_ollama import OllamaLLM
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory  # Keep using from langchain.memory
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

# Agentic AI Components
class AgentAction(BaseModel):
    action_type: str
    parameters: Dict[str, Any]
    description: str

class AgentResponse(BaseModel):
    message: str
    status: str
    data: Dict[str, Any] = {}

class AgentHistoryAction(BaseModel):
    timestamp: str
    action: str
    description: str
    status: str

class AIAgent:
    def __init__(self, feature_store: FeatureStore, use_agent: bool = True):
        self.feature_store = feature_store
        self.action_history: List[AgentHistoryAction] = []
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
                
                # Define tools for the agent
                self.tools = [
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
                    ),
                    Tool(
                        name="get_feature_info",
                        func=self._handle_feature_info,
                        description="Get information about available features for a specific feature view"
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
                print("Agent mode initialized successfully")
            except Exception as e:
                print(f"Error initializing Ollama LLM: {str(e)}")
                # Continue without the LLM components - the app will fall back to direct function calls
                self.use_agent = False
        else:
            print("Traditional mode initialized (not using AI agent)")
        
        # Define action-specific prompt templates
        self.recommendation_prompt = PromptTemplate(
            input_variables=["customer_features"],
            template="""Based on the following customer features:
            {customer_features}
            
            Generate personalized product recommendations considering:
            1. Customer's purchasing power (based on income)
            2. Past purchase behavior
            3. Age-appropriate products
            4. Current trends
            
            Provide detailed reasoning for each recommendation."""
        )
        
        self.fraud_prompt = PromptTemplate(
            input_variables=["transaction_features"],
            template="""Analyze the following transaction for potential fraud:
            {transaction_features}
            
            Consider these risk factors:
            1. Transaction amount vs customer history
            2. Location anomalies
            3. Time patterns
            4. Customer's typical behavior
            
            Provide a detailed risk assessment with confidence scores."""
        )
        
        self.segmentation_prompt = PromptTemplate(
            input_variables=["customer_features"],
            template="""Analyze the following customer features for segmentation:
            {customer_features}
            
            Consider these factors:
            1. Customer lifetime value
            2. Purchase frequency and recency
            3. Credit profile
            4. Demographics
            
            Provide detailed segment classification with actionable insights."""
        )

    def add_to_history(self, action_type: str, description: str, status: str = "success") -> None:
        history_action = AgentHistoryAction(
            timestamp=datetime.utcnow().isoformat(),
            action=action_type,
            description=description,
            status=status
        )
        self.action_history.insert(0, history_action)

    async def process_action(self, action: AgentAction) -> AgentResponse:
        try:
            # If agent mode is disabled or agent not initialized, use direct function calls
            if not self.use_agent or not hasattr(self, 'agent'):
                # Use direct function calls for traditional, non-agent mode
                if action.action_type == "make_recommendation":
                    result = self._handle_recommendation(action.parameters)
                    self.add_to_history(
                        action_type=action.action_type, 
                        description=f"{action.description} (Traditional Mode)"
                    )
                    return result
                elif action.action_type == "detect_fraud":
                    result = self._handle_fraud_detection(action.parameters)
                    self.add_to_history(
                        action_type=action.action_type, 
                        description=f"{action.description} (Traditional Mode)"
                    )
                    return result
                elif action.action_type == "segment_customer":
                    result = self._handle_customer_segmentation(action.parameters)
                    self.add_to_history(
                        action_type=action.action_type, 
                        description=f"{action.description} (Traditional Mode)"
                    )
                    return result
                else:
                    raise ValueError(f"Unsupported action type: {action.action_type}")
            
            # Agent mode: Convert the action into a natural language query
            query = self._create_agent_query(action)
            
            try:
                # Run the agent with async invoke
                agent_response = await self.agent.ainvoke({"input": query})
                if isinstance(agent_response, dict) and "output" in agent_response:
                    agent_response = agent_response["output"]
            except Exception as llm_error:
                print(f"LLM error: {str(llm_error)}")
                # Fall back to direct function calls if LLM fails
                if action.action_type == "make_recommendation":
                    result = self._handle_recommendation(action.parameters)
                    self.add_to_history(
                        action_type=action.action_type, 
                        description=f"{action.description} (Agent Mode with Fallback)"
                    )
                    return result
                elif action.action_type == "detect_fraud":
                    result = self._handle_fraud_detection(action.parameters)
                    self.add_to_history(
                        action_type=action.action_type, 
                        description=f"{action.description} (Agent Mode with Fallback)"
                    )
                    return result
                elif action.action_type == "segment_customer":
                    result = self._handle_customer_segmentation(action.parameters)
                    self.add_to_history(
                        action_type=action.action_type, 
                        description=f"{action.description} (Agent Mode with Fallback)"
                    )
                    return result
                else:
                    raise ValueError(f"Unsupported action type: {action.action_type}")
            
            # Process the agent's response
            response = self._process_agent_response(action, agent_response)
            
            # Add successful action to history
            self.add_to_history(
                action_type=action.action_type,
                description=f"{action.description} (Agent Mode)"
            )
            
            return response

        except Exception as e:
            # Add failed action to history
            self.add_to_history(
                action_type=action.action_type,
                description=f"Error: {str(e)}",
                status="error"
            )
            raise HTTPException(status_code=400, detail=str(e))

    def _create_agent_query(self, action: AgentAction) -> str:
        """Convert an AgentAction into a natural language query for the LangChain agent"""
        if action.action_type == "make_recommendation":
            return f"Analyze customer {action.parameters['customer_id']} and provide product recommendations"
        elif action.action_type == "detect_fraud":
            return f"Analyze transaction {action.parameters['transaction_id']} for potential fraud"
        elif action.action_type == "segment_customer":
            return f"Analyze and segment customer {action.parameters['customer_id']}"
        else:
            return f"Process {action.action_type} with parameters: {json.dumps(action.parameters)}"

    def _process_agent_response(self, action: AgentAction, agent_response: str) -> AgentResponse:
        """Process the agent's response into a structured AgentResponse"""
        try:
            if action.action_type == "make_recommendation" and hasattr(self, 'llm'):
                chain = LLMChain(llm=self.llm, prompt=self.recommendation_prompt)
                enhanced_response = chain.invoke({"customer_features": agent_response})
                if isinstance(enhanced_response, dict) and "text" in enhanced_response:
                    enhanced_response = enhanced_response["text"]
                return self._handle_recommendation(action.parameters, enhanced_response)
            elif action.action_type == "detect_fraud" and hasattr(self, 'llm'):
                chain = LLMChain(llm=self.llm, prompt=self.fraud_prompt)
                enhanced_response = chain.invoke({"transaction_features": agent_response})
                if isinstance(enhanced_response, dict) and "text" in enhanced_response:
                    enhanced_response = enhanced_response["text"]
                return self._handle_fraud_detection(action.parameters, enhanced_response)
            elif action.action_type == "segment_customer" and hasattr(self, 'llm'):
                chain = LLMChain(llm=self.llm, prompt=self.segmentation_prompt)
                enhanced_response = chain.invoke({"customer_features": agent_response})
                if isinstance(enhanced_response, dict) and "text" in enhanced_response:
                    enhanced_response = enhanced_response["text"]
                return self._handle_customer_segmentation(action.parameters, enhanced_response)
            else:
                # If LLM is not available or action type is not recognized, return direct response
                if action.action_type == "make_recommendation":
                    return self._handle_recommendation(action.parameters)
                elif action.action_type == "detect_fraud":
                    return self._handle_fraud_detection(action.parameters)
                elif action.action_type == "segment_customer":
                    return self._handle_customer_segmentation(action.parameters)
                
                return AgentResponse(
                    message="Processed action successfully",
                    status="success",
                    data={"response": agent_response}
                )
        except Exception as e:
            print(f"Error in _process_agent_response: {str(e)}")
            # Fall back to direct function calls if processing fails
            if action.action_type == "make_recommendation":
                return self._handle_recommendation(action.parameters)
            elif action.action_type == "detect_fraud":
                return self._handle_fraud_detection(action.parameters)
            elif action.action_type == "segment_customer":
                return self._handle_customer_segmentation(action.parameters)
            
            return AgentResponse(
                message="Processed action with fallback",
                status="success",
                data={"response": "Processed using fallback mechanism"}
            )

    def _handle_feature_info(self, action: AgentAction) -> AgentResponse:
        feature_view_name = action.parameters.get("feature_view", "")
        
        if not feature_view_name or feature_view_name not in self.feature_store.feature_views:
            return AgentResponse(
                message=f"Feature view '{feature_view_name}' not found",
                status="error",
                data={}
            )
        
        return AgentResponse(
            message=f"Retrieved information for feature view: {feature_view_name}",
            status="success",
            data=self.feature_store.feature_views[feature_view_name]
        )
    
    def _handle_online_features(self, action: AgentAction) -> AgentResponse:
        entity_rows = action.parameters.get("entity_rows", [])
        features = action.parameters.get("features", [])
        
        if not entity_rows or not features:
            return AgentResponse(
                message="Missing entity_rows or features in parameters",
                status="error",
                data={}
            )
        
        result = self.feature_store.get_online_features(entity_rows, features)
        
        return AgentResponse(
            message=f"Retrieved online features for {len(entity_rows)} entities",
            status="success",
            data=result
        )
    
    def _handle_historical_features(self, action: AgentAction) -> AgentResponse:
        entity_data = action.parameters.get("entity_data", [])
        features = action.parameters.get("features", [])
        
        if not entity_data or not features:
            return AgentResponse(
                message="Missing entity_data or features in parameters",
                status="error",
                data={}
            )
        
        entity_df = pd.DataFrame(entity_data)
        result_df = self.feature_store.get_historical_features(entity_df, features)
        
        return AgentResponse(
            message=f"Retrieved historical features for {len(entity_data)} entities",
            status="success",
            data=result_df.to_dict(orient='records')
        )
    
    def _handle_recommendation(self, parameters: Dict[str, Any], enhanced_response: str = None) -> AgentResponse:
        customer_id = parameters.get("customer_id")
        
        if not customer_id:
            return AgentResponse(
                message="Missing customer_id in parameters",
                status="error",
                data={}
            )
        
        # Get feature service for recommendations
        try:
            service = self.feature_store.get_feature_service("recommendation_service")
        except ValueError as e:
            return AgentResponse(
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
        
        # Mock recommendation logic
        recommendations = []
        for i in range(3):  # Generate 3 recommendations
            product_id = f"PROD-{np.random.randint(1000, 9999)}"
            product_name = np.random.choice(["Smart Phone", "Laptop", "Headphones", "Tablet", "Smartwatch"])
            product_category = np.random.choice(["Electronics", "Computers", "Accessories"])
            product_price = round(np.random.uniform(100, 1000), 2)
            match_score = round(np.random.uniform(0.6, 0.95), 2)
            
            recommendations.append({
                "product_id": product_id,
                "product_name": product_name,
                "category": product_category,
                "price": product_price,
                "match_score": match_score
            })
        
        # Sort by match score
        recommendations = sorted(recommendations, key=lambda x: x["match_score"], reverse=True)
        
        return AgentResponse(
            message=f"Generated product recommendations for customer {customer_id}",
            status="success",
            data={
                "customer_id": customer_id,
                "customer_features": online_features["values"][0],
                "recommendations": recommendations
            }
        )
    
    def _handle_fraud_detection(self, parameters: Dict[str, Any], enhanced_response: str = None) -> AgentResponse:
        transaction_id = parameters.get("transaction_id")
        
        if not transaction_id:
            return AgentResponse(
                message="Missing transaction_id in parameters",
                status="error",
                data={}
            )
        
        # Get feature service for fraud detection
        try:
            service = self.feature_store.get_feature_service("fraud_detection_service")
        except ValueError as e:
            return AgentResponse(
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
        
        # Mock fraud detection logic
        is_fraudulent = np.random.random() < 0.3  # 30% chance of fraud
        fraud_score = round(np.random.uniform(0.1, 0.9), 2)
        
        risk_factors = []
        if fraud_score > 0.6:
            risk_factors.append("Unusual transaction amount")
        if fraud_score > 0.7:
            risk_factors.append("Suspicious location")
        if fraud_score > 0.8:
            risk_factors.append("Abnormal transaction pattern")
        
        return AgentResponse(
            message=f"Completed fraud analysis for transaction {transaction_id}",
            status="success",
            data={
                "transaction_id": transaction_id,
                "transaction_features": online_features["values"][0],
                "fraud_detected": is_fraudulent,
                "fraud_score": fraud_score,
                "risk_factors": risk_factors
            }
        )
    
    def _handle_customer_segmentation(self, parameters: Dict[str, Any], enhanced_response: str = None) -> AgentResponse:
        customer_id = parameters.get("customer_id")
        
        if not customer_id:
            return AgentResponse(
                message="Missing customer_id in parameters",
                status="error",
                data={}
            )
        
        # Get feature service for customer segmentation
        try:
            service = self.feature_store.get_feature_service("customer_segmentation_service")
        except ValueError as e:
            return AgentResponse(
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
        
        # Mock segmentation logic
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
            
        return AgentResponse(
            message=f"Completed customer segmentation for customer {customer_id}",
            status="success",
            data={
                "customer_id": customer_id,
                "customer_features": customer_features,
                "segment": segment,
                "score": score,
                "potential_value_increase": f"{potential_increase}%",
                "recommendations": recommendations
            }
        )

# Data model for mode toggle
class ModeToggle(BaseModel):
    use_agent: bool

# API Setup
app = FastAPI(title="Agentic AI with Feast Feature Store")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Feature Store and AI Agent
feature_store = FeatureStore(repo_path="./feature_repo")
ai_agent = AIAgent(feature_store, use_agent=True)  # Default to agent mode

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

@app.post("/agent/action")
async def agent_action(action: AgentAction):
    response = await ai_agent.process_action(action)
    return response

@app.get("/agent/history")
async def agent_history():
    return {"actions": ai_agent.action_history}

@app.get("/agent/mode")
async def get_agent_mode():
    return {"use_agent": ai_agent.use_agent}

@app.post("/agent/mode")
async def set_agent_mode(mode: ModeToggle):
    # Create a new agent with the requested mode
    global ai_agent
    ai_agent = AIAgent(feature_store, use_agent=mode.use_agent)
    
    # Add this mode change to the history
    mode_name = "Agent Mode" if mode.use_agent else "Traditional Mode"
    ai_agent.add_to_history(
        action_type="toggle_mode",
        description=f"Switched to {mode_name}",
        status="success"
    )
    
    return {"message": f"Switched to {mode_name}", "use_agent": mode.use_agent}

@app.post("/demo/recommendation")
async def demo_recommendation(customer_id: str = Body(..., embed=True)):
    action = AgentAction(
        action_type="make_recommendation",
        parameters={"customer_id": customer_id},
        description="Generate product recommendations for a customer"
    )
    return await ai_agent.process_action(action)

@app.post("/demo/fraud-detection")
async def demo_fraud_detection(transaction_id: str = Body(..., embed=True)):
    action = AgentAction(
        action_type="detect_fraud",
        parameters={"transaction_id": transaction_id},
        description="Detect fraud for a transaction"
    )
    # Process through normal action handling to update history
    return await ai_agent.process_action(action)

@app.post("/demo/customer-segmentation")
async def demo_customer_segmentation(customer_id: str = Body(..., embed=True)):
    action = AgentAction(
        action_type="segment_customer",
        parameters={"customer_id": customer_id},
        description="Segment a customer based on their features"
    )
    # Process through normal action handling to update history
    return await ai_agent.process_action(action)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)