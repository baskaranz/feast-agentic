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

load_dotenv()

# Feature Store Implementation
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
        # Implementation to return historical features
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
        # Implementation to return online features
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

# Data Models
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

class ProcessingModeToggle(BaseModel):
    advanced_processing: bool

# Feature Processing Service
class FeatureProcessor:
    def __init__(self, feature_store: FeatureStore, advanced_processing: bool = False):
        self.feature_store = feature_store
        self.action_history: List[ActionHistory] = []
        self.advanced_processing = advanced_processing
    
    def add_to_history(self, action_type: str, description: str, status: str = "success") -> None:
        history_action = ActionHistory(
            timestamp=datetime.utcnow().isoformat(),
            action=action_type,
            description=description,
            status=status
        )
        self.action_history.insert(0, history_action)

    def process_feature_request(self, request: FeatureRequest) -> FeatureResponse:
        try:
            processing_mode = "advanced" if self.advanced_processing else "basic"
            
            if request.action_type == "recommendation":
                result = self._process_recommendation(request.entity_id)
                self.add_to_history(
                    action_type="get_recommendation_features", 
                    description=f"Retrieved features for customer {request.entity_id} ({processing_mode} processing)"
                )
                return result
            elif request.action_type == "fraud_detection":
                result = self._process_fraud_detection(request.entity_id)
                self.add_to_history(
                    action_type="get_fraud_detection_features", 
                    description=f"Retrieved features for transaction {request.entity_id} ({processing_mode} processing)"
                )
                return result
            elif request.action_type == "segmentation":
                result = self._process_customer_segmentation(request.entity_id)
                self.add_to_history(
                    action_type="get_segmentation_features", 
                    description=f"Retrieved features for customer {request.entity_id} ({processing_mode} processing)"
                )
                return result
            else:
                raise ValueError(f"Unsupported action type: {request.action_type}")
                
        except Exception as e:
            # Add failed action to history
            self.add_to_history(
                action_type=f"get_{request.action_type}_features",
                description=f"Error: {str(e)}",
                status="error"
            )
            raise HTTPException(status_code=400, detail=str(e))
    
    def _process_recommendation(self, customer_id: str) -> FeatureResponse:
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
        
        # Number of recommendations varies based on processing mode
        num_recommendations = 5 if self.advanced_processing else 3
        
        for i in range(num_recommendations):
            product_id = f"PROD-{np.random.randint(1000, 9999)}"
            
            # Advanced processing uses a wider variety of products
            if self.advanced_processing:
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
            
            # Advanced processing has more precise relevance scores
            if self.advanced_processing:
                # Simulate more personalized scoring with higher average scores
                relevance_score = round(np.random.uniform(0.75, 0.98), 3)
            else:
                relevance_score = round(np.random.uniform(0.6, 0.95), 2)
            
            recommendations.append({
                "product_id": product_id,
                "product_name": product_name,
                "category": product_category,
                "price": product_price,
                "relevance_score": relevance_score
            })
        
        # Sort by relevance score
        recommendations = sorted(recommendations, key=lambda x: x["relevance_score"], reverse=True)
        
        # Advanced processing includes confidence metrics
        response_data = {
            "customer_id": customer_id,
            "customer_features": online_features["values"][0],
            "recommendations": recommendations
        }
        
        if self.advanced_processing:
            response_data["processing_info"] = {
                "mode": "advanced",
                "confidence": round(np.random.uniform(0.85, 0.99), 2),
                "recommendation_count": len(recommendations),
                "feature_importance": {
                    "age": round(np.random.uniform(0.1, 0.3), 2),
                    "income": round(np.random.uniform(0.3, 0.5), 2),
                    "purchase_history": round(np.random.uniform(0.4, 0.7), 2)
                }
            }
        
        mode_text = "advanced" if self.advanced_processing else "basic"
        return FeatureResponse(
            message=f"Retrieved features and generated product recommendations for customer {customer_id} using {mode_text} processing",
            status="success",
            data=response_data
        )
    
    def _process_fraud_detection(self, transaction_id: str) -> FeatureResponse:
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
        
        return FeatureResponse(
            message=f"Retrieved features and analyzed transaction {transaction_id}",
            status="success",
            data={
                "transaction_id": transaction_id,
                "transaction_features": online_features["values"][0],
                "fraud_detected": is_fraudulent,
                "fraud_score": fraud_score,
                "risk_factors": risk_factors
            }
        )
    
    def _process_customer_segmentation(self, customer_id: str) -> FeatureResponse:
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
            
        return FeatureResponse(
            message=f"Retrieved features and segmented customer {customer_id}",
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

# API Setup
app = FastAPI(title="Feast Feature Store")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Feature Store and Feature Processor
feature_store = FeatureStore(repo_path="./feature_repo")
feature_processor = FeatureProcessor(feature_store, advanced_processing=False)

@app.get("/")
async def root():
    return {"message": "Feast Feature Store API"}

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
    response = feature_processor.process_feature_request(request)
    return response

@app.get("/features/history")
async def feature_history():
    return {"actions": feature_processor.action_history}

@app.get("/processing/mode")
async def get_processing_mode():
    return {"advanced_processing": feature_processor.advanced_processing}

@app.post("/processing/mode")
async def set_processing_mode(mode: ProcessingModeToggle):
    # Update the processing mode
    global feature_processor
    feature_processor.advanced_processing = mode.advanced_processing
    
    # Add this mode change to the history
    mode_name = "Advanced Processing" if mode.advanced_processing else "Basic Processing"
    feature_processor.add_to_history(
        action_type="toggle_mode",
        description=f"Switched to {mode_name}",
        status="success"
    )
    
    return {"message": f"Switched to {mode_name}", "advanced_processing": mode.advanced_processing}

@app.post("/demo/recommendation")
async def demo_recommendation(customer_id: str = Body(..., embed=True)):
    request = FeatureRequest(
        entity_id=customer_id,
        action_type="recommendation"
    )
    return feature_processor.process_feature_request(request)

@app.post("/demo/fraud-detection")
async def demo_fraud_detection(transaction_id: str = Body(..., embed=True)):
    request = FeatureRequest(
        entity_id=transaction_id,
        action_type="fraud_detection"
    )
    return feature_processor.process_feature_request(request)

@app.post("/demo/customer-segmentation")
async def demo_customer_segmentation(customer_id: str = Body(..., embed=True)):
    request = FeatureRequest(
        entity_id=customer_id,
        action_type="segmentation"
    )
    return feature_processor.process_feature_request(request)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)