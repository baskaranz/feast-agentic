import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;

const FeatureStoreDashboard = () => {
  const [activeTab, setActiveTab] = useState('recommendation');
  const [customerId, setCustomerId] = useState('CUST-1234');
  const [transactionId, setTransactionId] = useState('TRANS-5678');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [actionHistory, setActionHistory] = useState([]);
  const [featureViews, setFeatureViews] = useState([]);
  const [featureServices, setFeatureServices] = useState([]);
  const [error, setError] = useState(null);
  const [apiConnected, setApiConnected] = useState(true);
  const [useAgentMode, setUseAgentMode] = useState(true);

  useEffect(() => {
    // Fetch feature views and services when component mounts
    fetchInitialData();
  }, []);

  useEffect(() => {
    // Reset result when switching tabs
    setResult(null);
  }, [activeTab]);

  const fetchInitialData = async () => {
    try {
      // Use Docker service name instead of localhost
      // This should be used in docker-compose environments
      const API_URL_DOCKER = "http://backend:8000";
      
      // Try first with docker service name
      try {
        const healthCheck = await axios.get(`${API_URL_DOCKER}/`, { timeout: 3000 });
        if (healthCheck.status === 200) {
          // If successful, update the API_URL and continue
          console.log("Connected to backend via docker service name");
          
          const [viewsResponse, servicesResponse] = await Promise.all([
            axios.get(`${API_URL_DOCKER}/feature-views`),
            axios.get(`${API_URL_DOCKER}/feature-services`)
          ]);
          
          setFeatureViews(viewsResponse.data.feature_views);
          setFeatureServices(servicesResponse.data.feature_services);
          setApiConnected(true);
          return;
        }
      } catch (e) {
        console.log("Could not connect via docker service name, trying localhost...");
      }
      
      // Fall back to localhost if docker service name doesn't work
      const healthCheck = await axios.get(`${API_URL}/`, { timeout: 3000 });
      setApiConnected(healthCheck.status === 200);
  
      const [viewsResponse, servicesResponse] = await Promise.all([
        axios.get(`${API_URL}/feature-views`),
        axios.get(`${API_URL}/feature-services`)
      ]);
      
      setFeatureViews(viewsResponse.data.feature_views);
      setFeatureServices(servicesResponse.data.feature_services);
      
      // Fetch agent mode and history
      try {
        const [historyResponse, modeResponse] = await Promise.all([
          axios.get(`${API_URL}/features/history`),
          axios.get(`${API_URL}/agent/mode`)
        ]);
        
        setActionHistory(historyResponse.data.actions || []);
        
        // Set the agent mode if available
        if (modeResponse.data && 'use_agent' in modeResponse.data) {
          setUseAgentMode(modeResponse.data.use_agent);
        }
      } catch (err) {
        console.warn("Could not fetch feature history or agent mode, but other API calls succeeded:", err);
      }
    } catch (err) {
      console.error('Error fetching initial data:', err);
      setApiConnected(false);
      setError('Failed to connect to the backend service. Make sure the API is running.');
      
      // Set mock data for demo purposes when API is not available
      setFeatureViews(['customer_features', 'product_features', 'transaction_features']);
      setFeatureServices(['recommendation_service', 'fraud_detection_service', 'customer_segmentation_service']);
      setActionHistory([
        { 
          timestamp: '2025-02-25T10:23:45', 
          action: 'get_recommendation_features', 
          description: 'Retrieved features for customer CUST-1234 (Agent Mode)',
          status: 'success'
        },
        { 
          timestamp: '2025-02-25T10:24:12', 
          action: 'get_fraud_detection_features', 
          description: 'Fetched features for transaction TRANS-5678 (Agent Mode)',
          status: 'success'
        },
        { 
          timestamp: '2025-02-25T10:25:33', 
          action: 'get_segmentation_features', 
          description: 'Retrieved features for customer CUST-1234 (Agent Mode)',
          status: 'success'
        }
      ]);
    }
  };

  // Add toggle function for agent/traditional mode
  const toggleAgentMode = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (apiConnected) {
        const response = await axios.post(`${API_URL}/agent/mode`, {
          use_agent: !useAgentMode
        });
        
        if (response.data && 'use_agent' in response.data) {
          setUseAgentMode(response.data.use_agent);
          
          // Refresh history to show the mode change
          try {
            const historyResponse = await axios.get(`${API_URL}/features/history`);
            if (historyResponse.data && historyResponse.data.actions) {
              setActionHistory(historyResponse.data.actions);
            }
          } catch (err) {
            console.warn("Could not refresh history after mode change");
          }
        }
      } else {
        // Mock mode toggle in demo mode
        setUseAgentMode(!useAgentMode);
        
        // Add mock history entry
        const newAction = {
          timestamp: new Date().toISOString(),
          action: "toggle_mode",
          description: `Switched to ${!useAgentMode ? "AI Agent" : "Traditional"} Mode`,
          status: "success"
        };
        setActionHistory([newAction, ...actionHistory]);
      }
    } catch (err) {
      console.error('Error toggling agent mode:', err);
      setError('Failed to toggle agent mode');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let endpoint;
      let body;

      if (activeTab === 'recommendation') {
        endpoint = `${API_URL}/demo/recommendation`;
        body = { customer_id: customerId };
      } else if (activeTab === 'fraud') {
        endpoint = `${API_URL}/demo/fraud-detection`;
        body = { transaction_id: transactionId };
      } else if (activeTab === 'segmentation') {
        endpoint = `${API_URL}/demo/customer-segmentation`;
        body = { customer_id: customerId };
      }

      if (apiConnected) {
        try {
          const response = await axios.post(endpoint, body);
          setResult(response.data);
          
          // Try to refresh feature history
          try {
            const historyResponse = await axios.get(`${API_URL}/features/history`);
            if (historyResponse.data.actions) {
              setActionHistory(historyResponse.data.actions);
            }
          } catch (historyErr) {
            console.warn('Could not fetch updated history:', historyErr);
          }
        } catch (apiErr) {
          console.error('API request failed:', apiErr);
          setError(apiErr.response?.data?.message || 'Failed to process request. Please try again.');
          
          // Add failed action to history
          const errorAction = {
            timestamp: new Date().toISOString(),
            action: activeTab === 'recommendation' ? 'get_recommendation_features' :
                   activeTab === 'fraud' ? 'get_fraud_detection_features' :
                   'get_segmentation_features',
            description: `Failed to retrieve features - ${apiErr.message}`,
            status: 'error'
          };
          setActionHistory(prev => [errorAction, ...prev]);
        }
      } else {
        // Mock API response with proper timestamp handling
        mockApiResponse(activeTab);
      }
    } catch (err) {
      console.error('Error in request setup:', err);
      setError('Failed to setup request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const mockApiResponse = (activeTab) => {
    setTimeout(() => {
      const isAgentMode = useAgentMode;
      
      if (activeTab === 'recommendation') {
        const recommendations = [];
        const numRecs = isAgentMode ? 5 : 3;
        
        for (let i = 0; i < numRecs; i++) {
          recommendations.push({
            product_id: `PROD-${1000 + Math.floor(Math.random() * 9000)}`,
            product_name: ["Smart Phone", "Laptop", "Headphones", "Tablet", "Smartwatch"][Math.floor(Math.random() * 5)],
            category: ["Electronics", "Computers", "Accessories"][Math.floor(Math.random() * 3)],
            price: Math.floor(100 + Math.random() * 900),
            relevance_score: 0.6 + Math.random() * 0.35
          });
          
          // Add reasoning if in agent mode
          if (isAgentMode) {
            recommendations[i].reasoning = "Based on the customer's age and income, this product matches their interests";
          }
        }
        
        // Sort by relevance
        recommendations.sort((a, b) => b.relevance_score - a.relevance_score);
        
        const responseData = {
          status: 'success',
          message: `Retrieved features and generated product recommendations for customer ${customerId} using ${isAgentMode ? 'agent' : 'traditional'} mode`,
          data: {
            customer_id: customerId,
            customer_features: {
              'customer_features:age': 34,
              'customer_features:income': 85000,
              'customer_features:purchase_history': 28
            },
            recommendations: recommendations
          }
        };
        
        // Add AI insights if in agent mode
        if (isAgentMode) {
          responseData.data.ai_insights = {
            analysis: "The customer profile indicates preferences for technology products with specific price sensitivity.",
            confidence: 0.85 + Math.random() * 0.14,
            feature_importance: {
              age: 0.1 + Math.random() * 0.2,
              income: 0.3 + Math.random() * 0.2,
              purchase_history: 0.4 + Math.random() * 0.3
            }
          };
        }
        
        setResult(responseData);
      } else if (activeTab === 'fraud') {
        const fraudScore = Math.random() * 0.9;
        const riskFactors = [];
        
        if (fraudScore > 0.6) riskFactors.push("Unusual transaction amount");
        if (fraudScore > 0.7) riskFactors.push("Suspicious location");
        if (fraudScore > 0.8) riskFactors.push("Abnormal transaction pattern");
        
        const responseData = {
          status: 'success',
          message: `Retrieved features and analyzed transaction ${transactionId} using ${isAgentMode ? 'agent' : 'traditional'} mode`,
          data: {
            transaction_id: transactionId,
            transaction_features: {
              'customer_features:credit_score': 720,
              'transaction_features:amount': 423.95,
              'transaction_features:timestamp': '2025-02-25T10:15:00',
              'transaction_features:location': 'Austin'
            },
            fraud_detected: fraudScore > 0.7,
            fraud_score: fraudScore,
            risk_factors: riskFactors
          }
        };
        
        // Add AI insights if in agent mode
        if (isAgentMode) {
          responseData.data.ai_insights = {
            analysis: "The transaction exhibits several patterns that require further investigation.",
            confidence: 0.7 + Math.random() * 0.25,
            anomaly_detection: {
              amount: Math.random(),
              location: Math.random(),
              timing: Math.random()
            },
            recommendations: fraudScore > 0.7 ? [
              "Request additional verification from the customer",
              "Flag account for monitoring of future transactions"
            ] : []
          };
        }
        
        setResult(responseData);
      } else if (activeTab === 'segmentation') {
        const segments = ["Low Value", "Medium Value", "High Value", "VIP"];
        const segment = segments[Math.floor(Math.random() * segments.length)];
        const score = segment === "VIP" ? 7 + Math.floor(Math.random() * 3) :
                    segment === "High Value" ? 5 + Math.floor(Math.random() * 2) :
                    segment === "Medium Value" ? 3 + Math.floor(Math.random() * 2) : Math.floor(Math.random() * 3);
        
        let recommendations;
        if (segment === "Low Value") {
          recommendations = [
            "Offer promotional discounts to increase purchase frequency",
            "Suggest loyalty program enrollment",
            "Target with entry-level product recommendations"
          ];
        } else if (segment === "Medium Value") {
          recommendations = [
            "Send personalized product recommendations",
            "Offer mid-tier loyalty program benefits",
            "Target with cross-sell opportunities"
          ];
        } else if (segment === "High Value") {
          recommendations = [
            "Provide premium customer service",
            "Offer exclusive early access to new products",
            "Target with premium product upsells"
          ];
        } else {
          recommendations = [
            "Assign dedicated account manager",
            "Provide complimentary premium services",
            "Invite to exclusive VIP events and offerings"
          ];
        }
        
        const responseData = {
          status: 'success',
          message: `Retrieved features and segmented customer ${customerId} using ${isAgentMode ? 'agent' : 'traditional'} mode`,
          data: {
            customer_id: customerId,
            customer_features: {
              'customer_features:age': 34,
              'customer_features:income': 85000,
              'customer_features:credit_score': 720,
              'customer_features:purchase_history': 28
            },
            segment: segment,
            score: score,
            potential_value_increase: `${5 + Math.floor(Math.random() * 25)}%`,
            recommendations: recommendations
          }
        };
        
        // Add AI insights if in agent mode
        if (isAgentMode) {
          responseData.data.ai_insights = {
            analysis: `The customer falls into the ${segment} segment with potential for growth.`,
            confidence: 0.8 + Math.random() * 0.18,
            engagement_strategy: segment === "VIP" || segment === "High Value" ? 
              "High-touch personalized outreach and premium offering focus" : 
              "Automated engagement with value-based offerings",
            customer_journey: {
              current_stage: ["Acquisition", "Growth", "Maturity", "At-risk"][Math.floor(Math.random() * 4)],
              next_best_action: [
                "Personalized email campaign", 
                "Product recommendation bundle", 
                "Loyalty tier upgrade offer",
                "Retention discount"
              ][Math.floor(Math.random() * 4)]
            }
          };
        }
        
        setResult(responseData);
      }
      
      // Update feature history with mock entry
      const modeText = useAgentMode ? "Agent Mode" : "Traditional Mode";
      const newAction = {
        timestamp: new Date().toISOString(),
        action: activeTab === 'recommendation' 
          ? 'get_recommendation_features' 
          : activeTab === 'fraud' 
            ? 'get_fraud_detection_features' 
            : 'get_segmentation_features',
        description: `Retrieved features ${activeTab === 'recommendation' ? ' for customer ' + customerId : 
                     activeTab === 'fraud' ? ' for transaction ' + transactionId : 
                     ' for customer ' + customerId} (${modeText})`,
        status: 'success'
      };
      
      setActionHistory([newAction, ...actionHistory]);
      setLoading(false);
    }, 1500);
  };

  const renderResultContent = () => {
    if (!result || !result.data) return null;

    const isAgentMode = result.data.ai_insights !== undefined;

    switch (activeTab) {
      case 'recommendation':
        const recommendations = result.data.recommendations || [];
        const aiInsights = result.data.ai_insights;
        
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Customer Information</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Age</div>
                <div className="text-xl font-bold">{result.data.customer_features?.['customer_features:age'] || 'N/A'}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Income</div>
                <div className="text-xl font-bold">${(result.data.customer_features?.['customer_features:income'] || 0).toLocaleString()}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Purchase History</div>
                <div className="text-xl font-bold">{result.data.customer_features?.['customer_features:purchase_history'] || 0} items</div>
              </div>
            </div>

            {aiInsights && (
              <div className="mt-4 p-4 border rounded-lg bg-blue-50">
                <h3 className="text-md font-medium mb-2">AI Feature Analysis</h3>
                <div className="mb-3">
                  <div className="text-sm text-gray-600">Analysis</div>
                  <div className="text-base">{aiInsights.analysis}</div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <div className="text-sm text-gray-600">Confidence</div>
                    <div className="text-lg font-semibold">{(aiInsights.confidence * 100).toFixed(0)}%</div>
                  </div>
                </div>
                
                {aiInsights.feature_importance && (
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Feature Importance</div>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.entries(aiInsights.feature_importance).map(([feature, value]) => (
                        <div key={feature} className="bg-white p-2 rounded">
                          <div className="text-xs text-gray-500">{feature}</div>
                          <div className="font-medium">{(value * 100).toFixed(0)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <h3 className="text-lg font-medium mt-6">Recommendations</h3>
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <div className="font-bold">{rec?.product_name || 'Unknown Product'}</div>
                      <div className="text-sm text-gray-500">
                        {rec?.category || 'Uncategorized'} | ${(rec?.price || 0).toFixed(2)}
                      </div>
                    </div>
                    <div className="flex items-center">
                      <div className="text-sm mr-2">Relevance:</div>
                      <div className="text-lg font-bold text-green-600">
                        {((rec?.relevance_score || 0) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  
                  {rec.reasoning && (
                    <div className="mt-2 text-sm italic text-gray-600 border-t pt-2">
                      "{rec.reasoning}"
                    </div>
                  )}
                </div>
              ))}
              {recommendations.length === 0 && (
                <div className="text-gray-500 text-center py-4">
                  No recommendations available
                </div>
              )}
            </div>
            
            {recommendations.length > 0 && (
              <div className="mt-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={recommendations.map(rec => ({
                      product_name: rec.product_name,
                      relevance_score: rec.relevance_score
                    }))}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="product_name" />
                    <YAxis label={{ value: 'Relevance Score (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip 
                      formatter={(value) => [`${((value || 0) * 100).toFixed(0)}%`, 'Relevance Score']}
                      labelFormatter={(label) => `Product: ${label || 'Unknown'}`}
                    />
                    <Bar dataKey="relevance_score" fill="#8884d8" name="Relevance Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        );
      
      case 'fraud':
        const transactionFeatures = result.data.transaction_features || {};
        const fraudScore = result.data.fraud_score || 0;
        const fraudDetected = result.data.fraud_detected || false;
        const riskFactors = result.data.risk_factors || [];
        const fraudAiInsights = result.data.ai_insights;
        
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Transaction Information</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Amount</div>
                <div className="text-xl font-bold">${(transactionFeatures['transaction_features:amount'] || 0).toFixed(2)}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Location</div>
                <div className="text-xl font-bold">{transactionFeatures['transaction_features:location'] || 'Unknown'}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Credit Score</div>
                <div className="text-xl font-bold">{transactionFeatures['customer_features:credit_score'] || 'N/A'}</div>
              </div>
            </div>

            {fraudAiInsights && (
              <div className="mt-4 p-4 border rounded-lg bg-blue-50">
                <h3 className="text-md font-medium mb-2">AI Transaction Analysis</h3>
                <div className="mb-3">
                  <div className="text-sm text-gray-600">Analysis</div>
                  <div className="text-base">{fraudAiInsights.analysis}</div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <div className="text-sm text-gray-600">Confidence</div>
                    <div className="text-lg font-semibold">{(fraudAiInsights.confidence * 100).toFixed(0)}%</div>
                  </div>
                </div>
                
                {fraudAiInsights.anomaly_detection && (
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Anomaly Detection</div>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.entries(fraudAiInsights.anomaly_detection).map(([factor, value]) => (
                        <div key={factor} className="bg-white p-2 rounded">
                          <div className="text-xs text-gray-500">{factor}</div>
                          <div className="font-medium">{(value * 100).toFixed(0)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {fraudAiInsights.recommendations && fraudAiInsights.recommendations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm text-gray-600 mb-1">AI Recommendations</div>
                    <ul className="list-disc ml-5">
                      {fraudAiInsights.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm">{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <h3 className="text-lg font-medium mt-6">Fraud Analysis</h3>
            <div className="p-6 border rounded-lg bg-gray-50">
              <div className="flex justify-between items-center mb-4">
                <div className="text-lg">Fraud Score:</div>
                <div className={`text-3xl font-bold ${fraudScore > 0.6 ? 'text-red-600' : 'text-green-600'}`}>
                  {(fraudScore * 100).toFixed(0)}%
                </div>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-6">
                <div 
                  className={`h-2.5 rounded-full ${fraudScore > 0.6 ? 'bg-red-600' : 'bg-green-600'}`} 
                  style={{ width: `${fraudScore * 100}%` }}
                ></div>
              </div>
              
              <div className="text-center text-lg font-bold mb-4">
                {fraudDetected ? 
                  <span className="text-red-600">FRAUD DETECTED</span> : 
                  <span className="text-green-600">NO FRAUD DETECTED</span>
                }
              </div>
              
              {riskFactors.length > 0 && (
                <div className="mt-4">
                  <div className="font-medium">Risk Factors:</div>
                  <ul className="list-disc pl-5 mt-2">
                    {riskFactors.map((factor, index) => (
                      <li key={index} className="text-red-600">{factor}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        );
      
      case 'segmentation':
        const customerFeatures = result.data.customer_features || {};
        const segment = result.data.segment || 'Unknown';
        const score = result.data.score || 0;
        const potentialValueIncrease = result.data.potential_value_increase || '0%';
        const segmentRecommendations = result.data.recommendations || [];
        const segmentAiInsights = result.data.ai_insights;
        
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Customer Information</h3>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Age</div>
                <div className="text-xl font-bold">{customerFeatures['customer_features:age'] || 'N/A'}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Income</div>
                <div className="text-xl font-bold">${(customerFeatures['customer_features:income'] || 0).toLocaleString()}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Credit Score</div>
                <div className="text-xl font-bold">{customerFeatures['customer_features:credit_score'] || 'N/A'}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Purchase History</div>
                <div className="text-xl font-bold">{customerFeatures['customer_features:purchase_history'] || 0} items</div>
              </div>
            </div>

            {segmentAiInsights && (
              <div className="mt-4 p-4 border rounded-lg bg-blue-50">
                <h3 className="text-md font-medium mb-2">AI Segmentation Analysis</h3>
                <div className="mb-3">
                  <div className="text-sm text-gray-600">Analysis</div>
                  <div className="text-base">{segmentAiInsights.analysis}</div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <div className="text-sm text-gray-600">Confidence</div>
                    <div className="text-lg font-semibold">{(segmentAiInsights.confidence * 100).toFixed(0)}%</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Strategy</div>
                    <div className="text-sm">{segmentAiInsights.engagement_strategy}</div>
                  </div>
                </div>
                
                {segmentAiInsights.customer_journey && (
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Customer Journey</div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-white p-2 rounded">
                        <div className="text-xs text-gray-500">Current Stage</div>
                        <div className="font-medium">{segmentAiInsights.customer_journey.current_stage}</div>
                      </div>
                      <div className="bg-white p-2 rounded">
                        <div className="text-xs text-gray-500">Next Best Action</div>
                        <div className="font-medium">{segmentAiInsights.customer_journey.next_best_action}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border rounded-lg p-6 bg-gray-50">
                <h3 className="text-lg font-medium mb-4">Customer Segment</h3>
                <div className="text-center py-4">
                  <div className="text-xl text-gray-600">Current Segment</div>
                  <div className={`text-4xl font-bold mt-2 ${
                    segment === 'VIP' ? 'text-purple-600' :
                    segment === 'High Value' ? 'text-green-600' :
                    segment === 'Medium Value' ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {segment}
                  </div>
                  <div className="text-sm text-gray-500 mt-2">Customer Score: {score}/9</div>
                  <div className="text-sm text-green-600 mt-1">Potential Value Increase: {potentialValueIncrease}</div>
                </div>
              </div>
              
              <div className="border rounded-lg p-6">
                <h3 className="text-lg font-medium mb-4">Recommendations</h3>
                <ul className="space-y-2">
                  {segmentRecommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <div className="text-green-500 mr-2">•</div>
                      <div>{rec}</div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    try {
      // Ensure we have a valid string
      if (typeof timestamp !== 'string' || !timestamp) {
        console.warn('Invalid timestamp format:', timestamp);
        return 'N/A';
      }

      // Parse the ISO string
      const date = new Date(timestamp);
      
      // Check if the date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid date:', timestamp);
        return 'N/A';
      }

      // Format the date using local timezone
      return new Intl.DateTimeFormat('default', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      }).format(date);
    } catch (err) {
      console.error('Error formatting timestamp:', err);
      return 'N/A';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6">
      <header className="mb-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Agentic Feature Store</h1>
            <p className="text-gray-600 mt-1">
              AI-powered feature retrieval and processing for ML applications
            </p>
            {!apiConnected && (
              <div className="mt-2 text-sm text-amber-600 bg-amber-50 p-2 rounded-md">
                ⚠️ Backend API not detected. Running in demo mode with mock data.
              </div>
            )}
          </div>
          
          <div className="mt-4 md:mt-0 bg-white px-4 py-2 rounded-lg shadow border flex items-center">
            <div className="mr-3">
              <span className="font-semibold">Processing Mode:</span>
            </div>
            <div 
              className="relative inline-block w-12 h-6 transition duration-200 ease-in-out rounded-full cursor-pointer"
              onClick={toggleAgentMode}
            >
              <label
                className={`absolute left-0 w-12 h-6 transition duration-200 ease-in-out rounded-full ${
                  useAgentMode ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`absolute left-1 top-1 w-4 h-4 transition duration-200 ease-in-out rounded-full bg-white transform ${
                    useAgentMode ? 'translate-x-6' : 'translate-x-0'
                  }`}
                />
              </label>
            </div>
            <div className="ml-3">
              <span className={`text-sm font-medium ${useAgentMode ? 'text-blue-600' : 'text-gray-600'}`}>
                {useAgentMode ? 'AI Agent' : 'Traditional'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md border p-4 md:p-6">
            <div className="flex border-b pb-4 mb-4 overflow-x-auto">
              <button
                className={`px-4 py-2 rounded-md mr-2 ${activeTab === 'recommendation' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
                onClick={() => setActiveTab('recommendation')}
              >
                Recommendation
              </button>
              <button
                className={`px-4 py-2 rounded-md mr-2 ${activeTab === 'fraud' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
                onClick={() => setActiveTab('fraud')}
              >
                Fraud Detection
              </button>
              <button
                className={`px-4 py-2 rounded-md ${activeTab === 'segmentation' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
                onClick={() => setActiveTab('segmentation')}
              >
                Segmentation
              </button>
            </div>

            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-4">
                {activeTab === 'recommendation' ? 'Product Recommendations' : 
                 activeTab === 'fraud' ? 'Fraud Detection' : 
                 'Customer Segmentation'}
              </h2>

              <div className="mb-4">
                {activeTab === 'recommendation' || activeTab === 'segmentation' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Customer ID
                    </label>
                    <input
                      type="text"
                      className="border rounded-md px-3 py-2 w-full"
                      value={customerId}
                      onChange={(e) => setCustomerId(e.target.value)}
                    />
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Transaction ID
                    </label>
                    <input
                      type="text"
                      className="border rounded-md px-3 py-2 w-full"
                      value={transactionId}
                      onChange={(e) => setTransactionId(e.target.value)}
                    />
                  </div>
                )}
              </div>

              <button
                className="bg-blue-600 text-white px-4 py-2 rounded-md flex items-center"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </>
                ) : (
                  'Get Features'
                )}
              </button>
            </div>

            {error && (
              <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
                {error}
              </div>
            )}

            {result && (
              <div className="mt-4 border-t pt-4">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center">
                    <h3 className="text-lg font-medium">Results</h3>
                    <div className={`ml-3 px-3 py-1 text-xs font-medium rounded-full ${
                      result.data.ai_insights ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {result.data.ai_insights ? 'AI Agent Mode' : 'Traditional Mode'}
                    </div>
                  </div>
                  
                  {/* Processing details toggle */}
                  <div className="flex items-center text-sm text-blue-600 cursor-pointer group" 
                       onClick={() => document.getElementById('processing-details').classList.toggle('hidden')}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="group-hover:underline">Processing Details</span>
                  </div>
                </div>
                
                {/* Processing details panel */}
                <div id="processing-details" className="mb-4 p-4 bg-gray-50 rounded-lg border hidden">
                  <h4 className="font-medium mb-2">
                    {result.data.ai_insights ? 'AI Agent Processing Steps' : 'Traditional Processing Steps'}
                  </h4>
                  
                  {result.data.ai_insights ? (
                    <div className="text-sm">
                      <ol className="list-decimal pl-5 space-y-2">
                        <li className="text-blue-800">
                          <span className="font-medium">Natural Language Query Generation</span>
                          <p className="text-gray-700 pl-2">Created a query to retrieve and analyze features for {activeTab} task</p>
                        </li>
                        <li className="text-blue-800">
                          <span className="font-medium">Feature Service Selection</span>
                          <p className="text-gray-700 pl-2">Identified appropriate feature service for {activeTab} task</p>
                        </li>
                        <li className="text-blue-800">
                          <span className="font-medium">Feature Retrieval</span>
                          <p className="text-gray-700 pl-2">Retrieved relevant features from feature store using entity ID</p>
                        </li>
                        <li className="text-blue-800">
                          <span className="font-medium">AI Feature Analysis</span>
                          <p className="text-gray-700 pl-2">Analyzed feature relationships and patterns using LLM reasoning</p>
                        </li>
                        <li className="text-blue-800">
                          <span className="font-medium">Feature Importance Calculation</span>
                          <p className="text-gray-700 pl-2">Determined importance of each feature in the analysis</p>
                        </li>
                        <li className="text-blue-800">
                          <span className="font-medium">Enhanced Insight Generation</span>
                          <p className="text-gray-700 pl-2">Generated detailed insights and confidence metrics</p>
                        </li>
                        <li className="text-blue-800">
                          <span className="font-medium">Response Organization</span>
                          <p className="text-gray-700 pl-2">Structured results with AI reasoning and explanations</p>
                        </li>
                      </ol>
                    </div>
                  ) : (
                    <div className="text-sm">
                      <ol className="list-decimal pl-5 space-y-2">
                        <li className="text-gray-800">
                          <span className="font-medium">Feature Service Selection</span>
                          <p className="text-gray-700 pl-2">Identified appropriate feature service for {activeTab} task</p>
                        </li>
                        <li className="text-gray-800">
                          <span className="font-medium">Feature Retrieval</span>
                          <p className="text-gray-700 pl-2">Retrieved features directly from feature store using entity ID</p>
                        </li>
                        <li className="text-gray-800">
                          <span className="font-medium">Data Processing</span>
                          <p className="text-gray-700 pl-2">Applied predefined business logic to process features</p>
                        </li>
                        <li className="text-gray-800">
                          <span className="font-medium">Result Generation</span>
                          <p className="text-gray-700 pl-2">Generated standardized results based on feature values</p>
                        </li>
                      </ol>
                    </div>
                  )}
                </div>
                
                {renderResultContent()}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md border p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Feature Store Activity</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {actionHistory.map((action, index) => {
                // Check if the action is related to the current result
                const isCurrentAction = result && 
                  ((activeTab === 'recommendation' && action.action.includes('recommendation')) ||
                   (activeTab === 'fraud' && action.action.includes('fraud')) ||
                   (activeTab === 'segmentation' && action.action.includes('segmentation')));
                
                // Determine if it's an agent or traditional mode action
                const isAgentMode = action.description && action.description.includes('Agent Mode');
                const isTraditionalMode = action.description && action.description.includes('Traditional Mode');
                
                return (
                  <div 
                    key={index} 
                    className={`border-b pb-2 last:border-b-0 ${isCurrentAction ? 'bg-blue-50' : ''}`}
                  >
                    <div className="text-xs text-gray-500 flex justify-between">
                      <span>{formatTimestamp(action.timestamp)}</span>
                      {(isAgentMode || isTraditionalMode) && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          isAgentMode ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {isAgentMode ? 'AI Agent' : 'Traditional'}
                        </span>
                      )}
                    </div>
                    <div className="font-medium flex items-center">
                      {action.action}
                      <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                        action.status === 'success' ? 'bg-green-100 text-green-800' :
                        action.status === 'error' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {action.status}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">{action.description}</div>
                    
                    {/* Show activity steps for current action */}
                    {isCurrentAction && isAgentMode && (
                      <div className="mt-2 text-xs text-gray-600 border-t border-blue-100 pt-2">
                        <div className="font-medium text-blue-700 mb-1">Steps:</div>
                        <ol className="list-decimal pl-5 space-y-1">
                          <li>Natural language query created to analyze features</li>
                          <li>Feature service identified and features retrieved from feature store</li>
                          <li>LLM analysis performed on retrieved features</li>
                          <li>Feature importance calculated through AI reasoning</li>
                          <li>Insights generated based on feature relationships</li>
                          <li>Results processed with confidence metrics</li>
                        </ol>
                      </div>
                    )}
                    {isCurrentAction && isTraditionalMode && (
                      <div className="mt-2 text-xs text-gray-600 border-t border-gray-100 pt-2">
                        <div className="font-medium text-gray-700 mb-1">Steps:</div>
                        <ol className="list-decimal pl-5 space-y-1">
                          <li>Feature service identified for requested task</li>
                          <li>Features retrieved directly from feature store</li>
                          <li>Predefined business logic applied to features</li>
                          <li>Results calculated using standard algorithms</li>
                        </ol>
                      </div>
                    )}
                  </div>
                );
              })}
              {actionHistory.length === 0 && (
                <div className="text-gray-500 text-center py-4">No feature store activity yet</div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md border p-4 md:p-6">
            <h2 className="text-lg font-semibold mb-4">Feature Store Information</h2>
            
            <div className="mb-4">
              <h3 className="font-medium mb-2">Feature Views</h3>
              <ul className="text-sm text-gray-600">
                {featureViews.length > 0 ? (
                  featureViews.map((view, index) => (
                    <li key={index} className="py-1">{view}</li>
                  ))
                ) : (
                  <li className="text-gray-500">No feature views available</li>
                )}
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Feature Services</h3>
              <ul className="text-sm text-gray-600">
                {featureServices.length > 0 ? (
                  featureServices.map((service, index) => (
                    <li key={index} className="py-1">{service}</li>
                  ))
                ) : (
                  <li className="text-gray-500">No feature services available</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeatureStoreDashboard;