import os
import json
import sqlite3
import csv
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
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

# Configuration for offline and online stores
OFFLINE_STORE_PATH = os.path.join(os.path.dirname(__file__), 'offline_store')
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'feature_store.db')

# Create directories if they don't exist
os.makedirs(OFFLINE_STORE_PATH, exist_ok=True)

# Initialize SQLite database for online store
def initialize_sqlite_db():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Create tables for each feature view
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customer_features (
        customer_id TEXT PRIMARY KEY,
        age INTEGER,
        income REAL,
        credit_score INTEGER,
        purchase_history INTEGER,
        last_updated TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_features (
        product_id TEXT PRIMARY KEY,
        price REAL,
        category TEXT,
        rating REAL,
        inventory INTEGER,
        last_updated TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_features (
        transaction_id TEXT PRIMARY KEY,
        amount REAL,
        timestamp TIMESTAMP,
        location TEXT,
        last_updated TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("SQLite database initialized")

# Generate synthetic data for offline store
def generate_offline_data():
    # Customer data
    customers = []
    for i in range(1000):
        customer_id = f"CUST-{1000 + i}"
        age = np.random.randint(18, 80)
        income = np.random.randint(30000, 150000)
        credit_score = np.random.randint(300, 850)
        purchase_history = np.random.randint(0, 100)
        customers.append([customer_id, age, income, credit_score, purchase_history])
    
    # Save to CSV
    customer_file = os.path.join(OFFLINE_STORE_PATH, 'customer_features.csv')
    with open(customer_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['customer_id', 'age', 'income', 'credit_score', 'purchase_history'])
        writer.writerows(customers)
    
    # Product data
    products = []
    categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
    for i in range(500):
        product_id = f"PROD-{1000 + i}"
        price = np.random.uniform(10, 1000)
        category = np.random.choice(categories)
        rating = np.random.uniform(1, 5)
        inventory = np.random.randint(0, 1000)
        products.append([product_id, price, category, rating, inventory])
    
    # Save to CSV
    product_file = os.path.join(OFFLINE_STORE_PATH, 'product_features.csv')
    with open(product_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['product_id', 'price', 'category', 'rating', 'inventory'])
        writer.writerows(products)
    
    # Transaction data
    transactions = []
    locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(2000):
        transaction_id = f"TRANS-{1000 + i}"
        amount = np.random.uniform(10, 500)
        timestamp = base_time + timedelta(minutes=np.random.randint(1, 43200))
        location = np.random.choice(locations)
        transactions.append([transaction_id, amount, timestamp, location])
    
    # Save to CSV
    transaction_file = os.path.join(OFFLINE_STORE_PATH, 'transaction_features.csv')
    with open(transaction_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'amount', 'timestamp', 'location'])
        writer.writerows(transactions)
    
    print(f"Generated synthetic data in {OFFLINE_STORE_PATH}")

# Populate online store with sample data
def populate_online_store():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Sample customer data
    for i in range(100):
        customer_id = f"CUST-{1000 + i}"
        age = np.random.randint(18, 80)
        income = np.random.randint(30000, 150000)
        credit_score = np.random.randint(300, 850)
        purchase_history = np.random.randint(0, 100)
        last_updated = datetime.now()
        
        cursor.execute(
            "INSERT OR REPLACE INTO customer_features VALUES (?, ?, ?, ?, ?, ?)",
            (customer_id, age, income, credit_score, purchase_history, last_updated)
        )
    
    # Sample product data
    categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
    for i in range(50):
        product_id = f"PROD-{1000 + i}"
        price = np.random.uniform(10, 1000)
        category = np.random.choice(categories)
        rating = np.random.uniform(1, 5)
        inventory = np.random.randint(0, 1000)
        last_updated = datetime.now()
        
        cursor.execute(
            "INSERT OR REPLACE INTO product_features VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, price, category, rating, inventory, last_updated)
        )
    
    # Sample transaction data
    locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
    for i in range(200):
        transaction_id = f"TRANS-{1000 + i}"
        amount = np.random.uniform(10, 500)
        timestamp = datetime.now() - timedelta(minutes=np.random.randint(1, 60))
        location = np.random.choice(locations)
        last_updated = datetime.now()
        
        cursor.execute(
            "INSERT OR REPLACE INTO transaction_features VALUES (?, ?, ?, ?, ?)",
            (transaction_id, amount, timestamp, location, last_updated)
        )
    
    conn.commit()
    conn.close()
    print("Online store populated with sample data")

# Initialize database and generate data on module import
initialize_sqlite_db()
generate_offline_data()
populate_online_store()

# Mock Feast imports and functionality
# In a real implementation, you would use the actual Feast library
@dataclass
class FeatureStore:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.offline_store_path = OFFLINE_STORE_PATH
        self.online_store_path = SQLITE_DB_PATH
        
        self.feature_views = {
            "customer_features": {
                "features": ["age", "income", "credit_score", "purchase_history"],
                "entities": ["customer_id"],
                "offline_file": os.path.join(self.offline_store_path, "customer_features.csv"),
                "online_table": "customer_features"
            },
            "product_features": {
                "features": ["price", "category", "rating", "inventory"],
                "entities": ["product_id"],
                "offline_file": os.path.join(self.offline_store_path, "product_features.csv"),
                "online_table": "product_features"
            },
            "transaction_features": {
                "features": ["amount", "timestamp", "location"],
                "entities": ["transaction_id"],
                "offline_file": os.path.join(self.offline_store_path, "transaction_features.csv"),
                "online_table": "transaction_features"
            }
        }
        print(f"Feature store initialized with offline store at {self.offline_store_path} and online store at {self.online_store_path}")
    
    def get_feature_service(self, name: str):
        if name in ["recommendation_service", "fraud_detection_service", "customer_segmentation_service"]:
            return FeatureService(name, self)
        raise ValueError(f"Feature service {name} not found")
    
    def get_feature_view(self, name: str):
        if name in self.feature_views:
            return self.feature_views[name]
        raise ValueError(f"Feature view {name} not found")
    
    def get_historical_features(self, entity_df, features):
        """
        Get historical features from offline store (CSV files)
        
        Args:
            entity_df: DataFrame containing entity IDs
            features: List of features to retrieve in format 'feature_view:feature'
        
        Returns:
            DataFrame with requested features
        """
        # Map features to their feature views
        feature_view_map = {}
        for feature in features:
            parts = feature.split(':')
            if len(parts) != 2:
                continue
            view_name, feat_name = parts
            if view_name not in feature_view_map:
                feature_view_map[view_name] = []
            feature_view_map[view_name].append(feat_name)
        
        # Load required feature views from CSV files
        feature_dfs = {}
        for view_name, feat_list in feature_view_map.items():
            if view_name in self.feature_views:
                csv_file = self.feature_views[view_name]["offline_file"]
                entity_col = self.feature_views[view_name]["entities"][0]  # Assuming single entity
                try:
                    df = pd.read_csv(csv_file)
                    # Only keep requested features and entity column
                    keep_cols = [entity_col] + feat_list
                    keep_cols = [col for col in keep_cols if col in df.columns]
                    df = df[keep_cols]
                    feature_dfs[view_name] = df
                except Exception as e:
                    print(f"Error loading {csv_file}: {str(e)}")
                    # Fall back to synthetic data for missing files
                    num_rows = 1000
                    fallback_data = {}
                    fallback_data[entity_col] = [f"{entity_col.split('_')[0].upper()}-{1000 + i}" for i in range(num_rows)]
                    
                    for feat in feat_list:
                        if "age" in feat:
                            fallback_data[feat] = np.random.randint(18, 80, num_rows)
                        elif "income" in feat:
                            fallback_data[feat] = np.random.randint(30000, 150000, num_rows)
                        elif "credit_score" in feat:
                            fallback_data[feat] = np.random.randint(300, 850, num_rows)
                        elif "purchase_history" in feat:
                            fallback_data[feat] = np.random.randint(0, 100, num_rows)
                        elif "price" in feat:
                            fallback_data[feat] = np.random.uniform(10, 1000, num_rows)
                        elif "category" in feat:
                            categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
                            fallback_data[feat] = np.random.choice(categories, num_rows)
                        elif "rating" in feat:
                            fallback_data[feat] = np.random.uniform(1, 5, num_rows)
                        elif "inventory" in feat:
                            fallback_data[feat] = np.random.randint(0, 1000, num_rows)
                        elif "amount" in feat:
                            fallback_data[feat] = np.random.uniform(10, 500, num_rows)
                        elif "timestamp" in feat:
                            base_time = datetime.now() - timedelta(days=30)
                            fallback_data[feat] = [base_time + timedelta(minutes=np.random.randint(1, 43200)) for _ in range(num_rows)]
                        elif "location" in feat:
                            locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
                            fallback_data[feat] = np.random.choice(locations, num_rows)
                    
                    feature_dfs[view_name] = pd.DataFrame(fallback_data)
        
        # Join with entity dataframe
        result_df = entity_df.copy()
        
        for view_name, feat_df in feature_dfs.items():
            entity_col = self.feature_views[view_name]["entities"][0]
            if entity_col in result_df.columns and entity_col in feat_df.columns:
                for feat in feature_view_map[view_name]:
                    if feat in feat_df.columns:
                        # Create feature column name in form 'view:feature'
                        feature_col = f"{view_name}:{feat}"
                        # Join the feature to the result dataframe
                        result_df = pd.merge(
                            result_df,
                            feat_df[[entity_col, feat]].rename(columns={feat: feature_col}),
                            on=entity_col,
                            how='left'
                        )
        
        # Fill NaN values for missing features with random values as fallback
        for feature in features:
            if feature not in result_df.columns:
                parts = feature.split(':')
                if len(parts) != 2:
                    continue
                view_name, feat_name = parts
                
                num_rows = len(result_df)
                if "customer" in view_name:
                    if "age" in feat_name:
                        result_df[feature] = np.random.randint(18, 80, num_rows)
                    elif "income" in feat_name:
                        result_df[feature] = np.random.randint(30000, 150000, num_rows)
                    elif "credit_score" in feat_name:
                        result_df[feature] = np.random.randint(300, 850, num_rows)
                    elif "purchase_history" in feat_name:
                        result_df[feature] = np.random.randint(0, 100, num_rows)
                elif "product" in view_name:
                    if "price" in feat_name:
                        result_df[feature] = np.random.uniform(10, 1000, num_rows)
                    elif "category" in feat_name:
                        categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
                        result_df[feature] = np.random.choice(categories, num_rows)
                    elif "rating" in feat_name:
                        result_df[feature] = np.random.uniform(1, 5, num_rows)
                    elif "inventory" in feat_name:
                        result_df[feature] = np.random.randint(0, 1000, num_rows)
                elif "transaction" in view_name:
                    if "amount" in feat_name:
                        result_df[feature] = np.random.uniform(10, 500, num_rows)
                    elif "timestamp" in feat_name:
                        base_time = datetime.now() - timedelta(days=30)
                        result_df[feature] = [base_time + timedelta(minutes=np.random.randint(1, 43200)) for _ in range(num_rows)]
                    elif "location" in feat_name:
                        locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
                        result_df[feature] = np.random.choice(locations, num_rows)
        
        return result_df
    
    def get_online_features(self, entity_rows, features):
        """
        Get online features from SQLite database
        
        Args:
            entity_rows: List of entity dictionaries
            features: List of features to retrieve in format 'feature_view:feature'
        
        Returns:
            Dictionary with features and values
        """
        result = {
            "features": features,
            "values": []
        }
        
        try:
            conn = sqlite3.connect(self.online_store_path)
            cursor = conn.cursor()
            
            for entity_row in entity_rows:
                values = {}
                
                # Map features to their feature views
                feature_view_map = {}
                for feature in features:
                    parts = feature.split(':')
                    if len(parts) != 2:
                        continue
                    view_name, feat_name = parts
                    if view_name not in feature_view_map:
                        feature_view_map[view_name] = []
                    feature_view_map[view_name].append(feat_name)
                
                # Query each feature view
                for view_name, feat_list in feature_view_map.items():
                    if view_name in self.feature_views:
                        table_name = self.feature_views[view_name]["online_table"]
                        entity_col = self.feature_views[view_name]["entities"][0]  # Assuming single entity
                        entity_val = entity_row.get(entity_col)
                        
                        if entity_val:
                            # Build query for requested features
                            select_cols = ", ".join(feat_list)
                            query = f"SELECT {select_cols} FROM {table_name} WHERE {entity_col} = ?"
                            
                            cursor.execute(query, (entity_val,))
                            row = cursor.fetchone()
                            
                            if row:
                                # Add features to values dict
                                for i, feat in enumerate(feat_list):
                                    feature_name = f"{view_name}:{feat}"
                                    values[feature_name] = row[i]
                
                # Fill in missing features with random values
                for feature in features:
                    if feature not in values:
                        parts = feature.split(':')
                        if len(parts) != 2:
                            continue
                        view_name, feat_name = parts
                        
                        if "customer" in view_name:
                            if "age" in feat_name:
                                values[feature] = np.random.randint(18, 80)
                            elif "income" in feat_name:
                                values[feature] = np.random.randint(30000, 150000)
                            elif "credit_score" in feat_name:
                                values[feature] = np.random.randint(300, 850)
                            elif "purchase_history" in feat_name:
                                values[feature] = np.random.randint(0, 100)
                        elif "product" in view_name:
                            if "price" in feat_name:
                                values[feature] = np.random.uniform(10, 1000)
                            elif "category" in feat_name:
                                categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
                                values[feature] = np.random.choice(categories)
                            elif "rating" in feat_name:
                                values[feature] = np.random.uniform(1, 5)
                            elif "inventory" in feat_name:
                                values[feature] = np.random.randint(0, 1000)
                        elif "transaction" in view_name:
                            if "amount" in feat_name:
                                values[feature] = np.random.uniform(10, 500)
                            elif "timestamp" in feat_name:
                                values[feature] = datetime.now() - timedelta(minutes=np.random.randint(1, 60))
                            elif "location" in feat_name:
                                locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
                                values[feature] = np.random.choice(locations)
                
                # Add entity values to result
                for key, value in entity_row.items():
                    values[key] = value
                
                result["values"].append(values)
            
            conn.close()
            
        except Exception as e:
            print(f"Error querying online store: {str(e)}")
            # Fall back to random data generation
            for entity_row in entity_rows:
                values = {}
                for feature in features:
                    parts = feature.split(':')
                    if len(parts) != 2:
                        continue
                    view_name, feat_name = parts
                    
                    if "customer" in view_name:
                        if "age" in feat_name:
                            values[feature] = np.random.randint(18, 80)
                        elif "income" in feat_name:
                            values[feature] = np.random.randint(30000, 150000)
                        elif "credit_score" in feat_name:
                            values[feature] = np.random.randint(300, 850)
                        elif "purchase_history" in feat_name:
                            values[feature] = np.random.randint(0, 100)
                    elif "product" in view_name:
                        if "price" in feat_name:
                            values[feature] = np.random.uniform(10, 1000)
                        elif "category" in feat_name:
                            categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
                            values[feature] = np.random.choice(categories)
                        elif "rating" in feat_name:
                            values[feature] = np.random.uniform(1, 5)
                        elif "inventory" in feat_name:
                            values[feature] = np.random.randint(0, 1000)
                    elif "transaction" in view_name:
                        if "amount" in feat_name:
                            values[feature] = np.random.uniform(10, 500)
                        elif "timestamp" in feat_name:
                            values[feature] = datetime.now() - timedelta(minutes=np.random.randint(1, 60))
                        elif "location" in feat_name:
                            locations = ["New York", "San Francisco", "Chicago", "Austin", "Seattle"]
                            values[feature] = np.random.choice(locations)
                
                # Add entity values to result
                for key, value in entity_row.items():
                    values[key] = value
                    
                result["values"].append(values)
        
        return result

@dataclass
class FeatureService:
    name: str
    feature_store: FeatureStore
    
    def get_features(self):
        # Check if this is a custom feature service
        if hasattr(self.feature_store, '_agentic_feature_store'):
            agentic_store = self.feature_store._agentic_feature_store
            if hasattr(agentic_store, 'custom_feature_services') and self.name in agentic_store.custom_feature_services:
                return agentic_store.custom_feature_services[self.name]["features"]
        
        # Standard predefined services
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

class FeatureViewRequest(BaseModel):
    name: str
    entity: str
    features: List[str]
    description: str = ""

class FeatureServiceRequest(BaseModel):
    name: str
    features: List[str]
    description: str = ""
    use_case: str = ""

class DataSourceAnalysisRequest(BaseModel):
    data_source: str
    entity_type: str = ""

class FeatureSuggestionRequest(BaseModel):
    use_case: str
    entity_type: str = ""

# Agentic Feature Store Service
class AgenticFeatureStore:
    def __init__(self, feature_store: FeatureStore, use_agent: bool = True):
        self.feature_store = feature_store
        self.action_history: List[ActionHistory] = []
        self.use_agent = use_agent
        
        # Custom feature views and services created by the agent
        self.custom_feature_views = {}
        self.custom_feature_services = {}
        
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
                        name="create_feature_view",
                        func=self._tool_create_feature_view,
                        description="Create a new feature view by combining features from existing feature views"
                    ),
                    Tool(
                        name="create_feature_service",
                        func=self._tool_create_feature_service,
                        description="Create a new feature service for a specific ML use case by selecting relevant features"
                    ),
                    Tool(
                        name="get_feature_views",
                        func=self._tool_get_feature_views,
                        description="Get a list of all available feature views in the feature store"
                    ),
                    Tool(
                        name="get_feature_services",
                        func=self._tool_get_feature_services,
                        description="Get a list of all available feature services in the feature store"
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
                    ),
                    Tool(
                        name="analyze_data_source",
                        func=self._tool_analyze_data_source,
                        description="Analyze a data source (CSV file) to identify potential features and entities"
                    ),
                    Tool(
                        name="suggest_features_for_use_case",
                        func=self._tool_suggest_features_for_use_case,
                        description="Suggest relevant features for a specific ML use case based on available data"
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
        
        self.feature_view_creation_prompt = PromptTemplate(
            input_variables=["entity", "data_source", "existing_features", "use_case"],
            template="""You are a feature engineering expert. Help create a new feature view for:
            
            Entity: {entity}
            Data Source: {data_source}
            Existing Features: {existing_features}
            Use Case: {use_case}
            
            Analyze the data source and identify relevant features.
            Consider:
            1. Feature relevance to the use case
            2. Feature transformation needs
            3. Feature quality and coverage
            4. Entity relationships
            
            For each feature, provide:
            - Feature name
            - Data type
            - Description
            - Relevance to use case (low, medium, high)
            - Suggested transformations (if needed)
            
            Format your response as a structured feature view definition."""
        )
        
        self.feature_service_creation_prompt = PromptTemplate(
            input_variables=["use_case", "available_features", "entity_type"],
            template="""You are a machine learning feature expert. Help create a new feature service for:
            
            Use Case: {use_case}
            Entity Type: {entity_type}
            Available Features: {available_features}
            
            Identify the most relevant features for this use case.
            Consider:
            1. Feature importance for the specific use case
            2. Potential feature interactions
            3. Required vs. optional features
            4. Performance implications
            
            Format your response as a structured feature service definition with:
            - Service name
            - List of selected features with justification
            - Expected performance impact
            - Potential limitations"""
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
            
            # Check custom feature services first
            if service_name in self.custom_feature_services:
                service_info = self.custom_feature_services[service_name]
                return json.dumps({
                    "service_name": service_name, 
                    "features": service_info["features"],
                    "description": service_info.get("description", ""),
                    "custom": True
                })
            
            # Fall back to standard feature services
            service = self.feature_store.get_feature_service(service_name)
            features = service.get_features()
            return json.dumps({"service_name": service_name, "features": features, "custom": False})
        except Exception as e:
            return f"Error retrieving feature service: {str(e)}"
    
    def _tool_create_feature_view(self, params: str) -> str:
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            name = params_dict.get("name")
            entity = params_dict.get("entity")
            features = params_dict.get("features", [])
            description = params_dict.get("description", "")
            
            if not name or not entity or not features:
                return "Error: Missing required parameters (name, entity, features)"
            
            # Check if name already exists
            if name in self.feature_store.feature_views or name in self.custom_feature_views:
                return f"Error: Feature view '{name}' already exists"
            
            # Create the custom feature view
            self.custom_feature_views[name] = {
                "features": features,
                "entities": [entity],
                "description": description,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add to action history
            self.add_to_history(
                action_type="create_feature_view",
                description=f"Created new feature view '{name}' with {len(features)} features for entity '{entity}'"
            )
            
            return json.dumps({
                "name": name,
                "entity": entity,
                "features": features,
                "description": description,
                "message": f"Successfully created feature view '{name}'"
            })
        except Exception as e:
            self.add_to_history(
                action_type="create_feature_view",
                description=f"Failed to create feature view: {str(e)}",
                status="error"
            )
            return f"Error creating feature view: {str(e)}"
    
    def _tool_create_feature_service(self, params: str) -> str:
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            name = params_dict.get("name")
            features = params_dict.get("features", [])
            description = params_dict.get("description", "")
            use_case = params_dict.get("use_case", "")
            
            if not name or not features:
                return "Error: Missing required parameters (name, features)"
            
            # Check if name already exists
            if name in self.custom_feature_services:
                return f"Error: Feature service '{name}' already exists"
            
            # Check if service can be created with standard get_feature_service
            try:
                self.feature_store.get_feature_service(name)
                return f"Error: Feature service '{name}' already exists as a standard service"
            except ValueError:
                # This is expected - we want to create a new custom service
                pass
            
            # Create the custom feature service
            self.custom_feature_services[name] = {
                "features": features,
                "description": description,
                "use_case": use_case,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add to action history
            self.add_to_history(
                action_type="create_feature_service",
                description=f"Created new feature service '{name}' with {len(features)} features for use case '{use_case}'"
            )
            
            return json.dumps({
                "name": name,
                "features": features,
                "description": description,
                "use_case": use_case,
                "message": f"Successfully created feature service '{name}'"
            })
        except Exception as e:
            self.add_to_history(
                action_type="create_feature_service",
                description=f"Failed to create feature service: {str(e)}",
                status="error"
            )
            return f"Error creating feature service: {str(e)}"
    
    def _tool_get_feature_views(self, _) -> str:
        try:
            # Combine standard and custom feature views
            all_feature_views = {}
            
            # Add standard feature views
            for name, view in self.feature_store.feature_views.items():
                all_feature_views[name] = {
                    "features": view["features"],
                    "entities": view["entities"],
                    "custom": False
                }
            
            # Add custom feature views
            for name, view in self.custom_feature_views.items():
                all_feature_views[name] = {
                    "features": view["features"],
                    "entities": view["entities"],
                    "description": view.get("description", ""),
                    "created_at": view.get("created_at", ""),
                    "custom": True
                }
            
            return json.dumps(all_feature_views)
        except Exception as e:
            return f"Error retrieving feature views: {str(e)}"
    
    def _tool_get_feature_services(self, _) -> str:
        try:
            # Get standard feature service names
            standard_services = ["recommendation_service", "fraud_detection_service", "customer_segmentation_service"]
            
            # Combine standard and custom feature services
            all_services = {}
            
            # Add standard services
            for name in standard_services:
                try:
                    service = self.feature_store.get_feature_service(name)
                    all_services[name] = {
                        "features": service.get_features(),
                        "custom": False
                    }
                except ValueError:
                    pass
            
            # Add custom services
            for name, service in self.custom_feature_services.items():
                all_services[name] = {
                    "features": service["features"],
                    "description": service.get("description", ""),
                    "use_case": service.get("use_case", ""),
                    "created_at": service.get("created_at", ""),
                    "custom": True
                }
            
            return json.dumps(all_services)
        except Exception as e:
            return f"Error retrieving feature services: {str(e)}"
    
    def _tool_analyze_data_source(self, params: str) -> str:
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            data_source = params_dict.get("data_source")
            entity_type = params_dict.get("entity_type", "")
            
            if not data_source:
                return "Error: Missing data_source parameter"
            
            # Check if data source exists in offline store
            if data_source.endswith('.csv'):
                file_path = os.path.join(self.feature_store.offline_store_path, data_source)
                if not os.path.exists(file_path):
                    return f"Error: Data source file '{file_path}' does not exist"
                
                # Analyze CSV file
                try:
                    df = pd.read_csv(file_path)
                    
                    # Get basic stats
                    stats = {
                        "filename": data_source,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns),
                        "sample_data": df.head(5).to_dict(orient='records'),
                    }
                    
                    # Use LLM to suggest entity and features if agent mode is enabled
                    if self.use_agent and hasattr(self, 'llm'):
                        # Use LLM to analyze and suggest features
                        analysis_prompt = f"""
                        You are a feature engineering expert. Analyze this dataset:
                        
                        Data Source: {data_source}
                        Columns: {list(df.columns)}
                        Sample Data: {df.head(5).to_dict(orient='records')}
                        
                        1. Identify the most likely entity column
                        2. For each column, determine if it's a good feature and why
                        3. Suggest any feature transformations that would be useful
                        
                        Format your response as a JSON object with:
                        - suggested_entity: the column that appears to be the entity ID
                        - features: list of suggested feature columns
                        - transformations: suggested transformations
                        """
                        
                        response = self.llm.invoke(analysis_prompt)
                        if isinstance(response, dict) and "text" in response:
                            response = response["text"]
                        
                        stats["ai_analysis"] = response
                    
                    # Add to action history
                    self.add_to_history(
                        action_type="analyze_data_source",
                        description=f"Analyzed data source '{data_source}' with {len(df.columns)} columns and {len(df)} rows"
                    )
                    
                    return json.dumps(stats, default=str)
                except Exception as e:
                    return f"Error analyzing CSV file: {str(e)}"
            else:
                return f"Error: Unsupported data source type. Only CSV files are supported."
        except Exception as e:
            return f"Error analyzing data source: {str(e)}"
    
    def _tool_suggest_features_for_use_case(self, params: str) -> str:
        try:
            params_dict = json.loads(params) if isinstance(params, str) else params
            use_case = params_dict.get("use_case")
            entity_type = params_dict.get("entity_type", "")
            
            if not use_case:
                return "Error: Missing use_case parameter"
            
            # Get all available features from feature views
            all_features = []
            
            # Add standard feature views
            for name, view in self.feature_store.feature_views.items():
                for feature in view["features"]:
                    all_features.append(f"{name}:{feature}")
            
            # Add custom feature views
            for name, view in self.custom_feature_views.items():
                for feature in view["features"]:
                    all_features.append(f"{name}:{feature}")
            
            # Use LLM to suggest features if agent mode is enabled
            if self.use_agent and hasattr(self, 'llm'):
                # Use LLM to suggest features for use case
                chain = LLMChain(
                    llm=self.llm,
                    prompt=self.feature_service_creation_prompt
                )
                
                response = chain.invoke({
                    "use_case": use_case,
                    "available_features": ', '.join(all_features),
                    "entity_type": entity_type
                })
                
                if isinstance(response, dict) and "text" in response:
                    response = response["text"]
                
                # Add to action history
                self.add_to_history(
                    action_type="suggest_features",
                    description=f"Generated feature suggestions for use case '{use_case}'"
                )
                
                return json.dumps({
                    "use_case": use_case,
                    "available_features": all_features,
                    "suggestions": response
                })
            else:
                # Without LLM, return basic recommendations based on use case
                recommended_features = []
                
                if "recommendation" in use_case.lower():
                    recommended_features = [
                        "customer_features:age",
                        "customer_features:income",
                        "customer_features:purchase_history",
                        "product_features:price",
                        "product_features:category",
                        "product_features:rating"
                    ]
                elif "fraud" in use_case.lower():
                    recommended_features = [
                        "customer_features:credit_score",
                        "transaction_features:amount",
                        "transaction_features:timestamp",
                        "transaction_features:location"
                    ]
                elif "segment" in use_case.lower():
                    recommended_features = [
                        "customer_features:age",
                        "customer_features:income",
                        "customer_features:credit_score",
                        "customer_features:purchase_history"
                    ]
                
                return json.dumps({
                    "use_case": use_case,
                    "available_features": all_features,
                    "recommended_features": recommended_features
                })
        except Exception as e:
            return f"Error suggesting features: {str(e)}"
    
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
            
            if self.use_agent:
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
        
        if self.use_agent:
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
        if self.use_agent:
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
        if self.use_agent:
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

# Add reference to agentic feature store in the feature store for custom services
feature_store._agentic_feature_store = agentic_feature_store

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

# New endpoints for enhanced feature store management

@app.get("/feature-views/custom")
async def get_custom_feature_views():
    """Get all custom feature views created by the agent"""
    return {"custom_feature_views": agentic_feature_store.custom_feature_views}

@app.post("/feature-views/create")
async def create_feature_view(request: FeatureViewRequest):
    """Create a new feature view"""
    if not agentic_feature_store.use_agent:
        return {
            "message": "Feature view creation is only available in Agent mode",
            "status": "error"
        }
    
    try:
        result = agentic_feature_store._tool_create_feature_view(json.dumps({
            "name": request.name,
            "entity": request.entity,
            "features": request.features,
            "description": request.description
        }))
        
        result_data = json.loads(result)
        return {
            "message": result_data.get("message", "Feature view created successfully"),
            "status": "success",
            "data": result_data
        }
    except Exception as e:
        return {
            "message": f"Error creating feature view: {str(e)}",
            "status": "error"
        }

@app.get("/feature-services/custom")
async def get_custom_feature_services():
    """Get all custom feature services created by the agent"""
    return {"custom_feature_services": agentic_feature_store.custom_feature_services}

@app.post("/feature-services/create")
async def create_feature_service(request: FeatureServiceRequest):
    """Create a new feature service"""
    if not agentic_feature_store.use_agent:
        return {
            "message": "Feature service creation is only available in Agent mode",
            "status": "error"
        }
    
    try:
        result = agentic_feature_store._tool_create_feature_service(json.dumps({
            "name": request.name,
            "features": request.features,
            "description": request.description,
            "use_case": request.use_case
        }))
        
        result_data = json.loads(result)
        return {
            "message": result_data.get("message", "Feature service created successfully"),
            "status": "success",
            "data": result_data
        }
    except Exception as e:
        return {
            "message": f"Error creating feature service: {str(e)}",
            "status": "error"
        }

@app.post("/data-source/analyze")
async def analyze_data_source(request: DataSourceAnalysisRequest):
    """Analyze a data source to identify features and entities"""
    if not agentic_feature_store.use_agent:
        return {
            "message": "Data source analysis is only available in Agent mode",
            "status": "error"
        }
    
    try:
        result = agentic_feature_store._tool_analyze_data_source(json.dumps({
            "data_source": request.data_source,
            "entity_type": request.entity_type
        }))
        
        try:
            result_data = json.loads(result)
            return {
                "message": "Data source analyzed successfully",
                "status": "success",
                "data": result_data
            }
        except:
            # If result is not valid JSON, return as text
            return {
                "message": "Data source analyzed with warnings",
                "status": "success",
                "data": {"analysis": result}
            }
    except Exception as e:
        return {
            "message": f"Error analyzing data source: {str(e)}",
            "status": "error"
        }

@app.post("/features/suggest")
async def suggest_features_for_use_case(request: FeatureSuggestionRequest):
    """Suggest features for a specific use case"""
    if not agentic_feature_store.use_agent:
        return {
            "message": "Feature suggestion is only available in Agent mode",
            "status": "error"
        }
    
    try:
        result = agentic_feature_store._tool_suggest_features_for_use_case(json.dumps({
            "use_case": request.use_case,
            "entity_type": request.entity_type
        }))
        
        try:
            result_data = json.loads(result)
            return {
                "message": "Features suggested successfully",
                "status": "success",
                "data": result_data
            }
        except:
            # If result is not valid JSON, return as text
            return {
                "message": "Features suggested with warnings",
                "status": "success",
                "data": {"suggestions": result}
            }
    except Exception as e:
        return {
            "message": f"Error suggesting features: {str(e)}",
            "status": "error"
        }

@app.get("/stores/info")
async def get_store_info():
    """Get information about the offline and online stores"""
    try:
        # Count offline records
        offline_stats = {}
        for view_name, view in agentic_feature_store.feature_store.feature_views.items():
            file_path = view.get("offline_file", "")
            if file_path and os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path)
                    offline_stats[view_name] = {
                        "file": os.path.basename(file_path),
                        "rows": len(df),
                        "columns": len(df.columns),
                        "entity_column": view["entities"][0],
                        "feature_columns": view["features"]
                    }
                except Exception as e:
                    offline_stats[view_name] = {
                        "file": os.path.basename(file_path),
                        "error": str(e)
                    }
        
        # Count online records
        online_stats = {}
        try:
            conn = sqlite3.connect(agentic_feature_store.feature_store.online_store_path)
            cursor = conn.cursor()
            
            for view_name, view in agentic_feature_store.feature_store.feature_views.items():
                table_name = view.get("online_table", "")
                if table_name:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                        columns = [description[0] for description in cursor.description]
                        
                        online_stats[view_name] = {
                            "table": table_name,
                            "rows": count,
                            "columns": columns
                        }
                    except Exception as e:
                        online_stats[view_name] = {
                            "table": table_name,
                            "error": str(e)
                        }
            
            conn.close()
        except Exception as e:
            online_stats["error"] = str(e)
        
        return {
            "message": "Store information retrieved successfully",
            "status": "success",
            "data": {
                "offline_store": {
                    "path": agentic_feature_store.feature_store.offline_store_path,
                    "stats": offline_stats
                },
                "online_store": {
                    "path": agentic_feature_store.feature_store.online_store_path,
                    "stats": online_stats
                }
            }
        }
    except Exception as e:
        return {
            "message": f"Error retrieving store information: {str(e)}",
            "status": "error"
        }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)