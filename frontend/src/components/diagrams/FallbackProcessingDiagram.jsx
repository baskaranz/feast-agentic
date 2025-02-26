import React from 'react';

/**
 * A simple fallback component that renders a basic processing flow
 * when the reactflow library is not available
 */
const FallbackProcessingDiagram = ({ isAgentMode, activeTab }) => {
  // Helper function to get result description based on active tab
  function getTabSpecificResult(activeTab) {
    switch (activeTab) {
      case 'recommendation':
        return 'Generate ranked product recommendations';
      case 'fraud':
        return 'Calculate fraud score and risk factors';
      case 'segmentation':
        return 'Determine customer segment and value';
      default:
        return 'Process results';
    }
  }

  return (
    <div className="fallback-processing-diagram p-4">
      <div className="text-sm mb-3 text-gray-700">
        Flow diagram visualization requires the reactflow package. Using simplified view instead.
      </div>
      
      <div className="border rounded p-4 bg-white">
        {isAgentMode ? (
          <div className="space-y-3">
            <h4 className="font-medium text-blue-600">AI Agent Mode Processing Flow</h4>
            <div className="flex flex-col space-y-2">
              {/* Agent mode flow steps */}
              <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                <div className="font-medium">Query Generation</div>
                <div className="text-xs text-gray-600">Convert request to natural language query</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-blue-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                <div className="font-medium">Feature Selection</div>
                <div className="text-xs text-gray-600">Identify required feature services</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-blue-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-green-50 border border-green-200 rounded">
                <div className="font-medium">Feature Retrieval</div>
                <div className="text-xs text-gray-600">Get features from feature store</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-blue-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                <div className="font-medium">AI Analysis</div>
                <div className="text-xs text-gray-600">Process features with LLM reasoning</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-blue-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                <div className="font-medium">Feature Importance</div>
                <div className="text-xs text-gray-600">Calculate importance of each feature</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-blue-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                <div className="font-medium">AI Insights</div>
                <div className="text-xs text-gray-600">Generate enhanced insights and confidence</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-blue-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-orange-50 border border-orange-200 rounded">
                <div className="font-medium">Final Results</div>
                <div className="text-xs text-gray-600">{getTabSpecificResult(activeTab)}</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-600">Traditional Mode Processing Flow</h4>
            <div className="flex flex-col space-y-2">
              {/* Traditional mode flow steps */}
              <div className="p-2 bg-gray-50 border border-gray-200 rounded">
                <div className="font-medium">Feature Service Selection</div>
                <div className="text-xs text-gray-600">Select appropriate feature service</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-gray-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-green-50 border border-green-200 rounded">
                <div className="font-medium">Feature Retrieval</div>
                <div className="text-xs text-gray-600">Get features from feature store</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-gray-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-gray-50 border border-gray-200 rounded">
                <div className="font-medium">Data Processing</div>
                <div className="text-xs text-gray-600">Apply business logic to features</div>
              </div>
              <div className="flex justify-center">
                <svg height="20" width="20" className="text-gray-300">
                  <line x1="10" y1="0" x2="10" y2="20" stroke="currentColor" strokeWidth="2" />
                  <polygon points="5,15 10,20 15,15" fill="currentColor" />
                </svg>
              </div>
              <div className="p-2 bg-orange-50 border border-orange-200 rounded">
                <div className="font-medium">Final Results</div>
                <div className="text-xs text-gray-600">{getTabSpecificResult(activeTab)}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FallbackProcessingDiagram;