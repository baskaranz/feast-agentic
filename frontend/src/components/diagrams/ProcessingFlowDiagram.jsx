import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom node styles
const nodeStyles = {
  agentNode: {
    backgroundColor: '#d4e8ff',
    borderColor: '#2684ff',
    borderRadius: '8px',
    borderWidth: '2px',
    padding: '10px',
    width: 180,
  },
  traditionalNode: {
    backgroundColor: '#f0f0f0',
    borderColor: '#666',
    borderRadius: '8px',
    borderWidth: '2px',
    padding: '10px',
    width: 180,
  },
  featureStoreNode: {
    backgroundColor: '#e6f4ea',
    borderColor: '#34a853',
    borderRadius: '8px',
    borderWidth: '2px',
    padding: '10px',
    width: 180,
  },
  resultNode: {
    backgroundColor: '#fef0e5',
    borderColor: '#f5ad78',
    borderRadius: '8px',
    borderWidth: '2px',
    padding: '10px',
    width: 180,
  }
};

// Define custom node component for better styling
const CustomNode = ({ data, type }) => {
  const style = nodeStyles[data.nodeType] || {};
  
  return (
    <div className="custom-node shadow-md" style={style}>
      <div className="font-medium mb-1">{data.label}</div>
      <div className="text-xs text-gray-700">{data.description}</div>
    </div>
  );
};

// Node types mapping
const nodeTypes = {
  customNode: CustomNode,
};

const ProcessingFlowDiagram = ({ isAgentMode, activeTab }) => {
  // Initialize nodes and edges with empty arrays
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Generate the nodes and edges based on the processing mode and task
  useEffect(() => {
    let flowNodes = [];
    let flowEdges = [];
    
    // Different flows for agent mode vs traditional mode
    if (isAgentMode) {
      // Agent mode flow
      flowNodes = [
        {
          id: '1',
          type: 'customNode',
          position: { x: 250, y: 50 },
          data: { 
            label: 'Query Generation', 
            description: 'Convert request to natural language query',
            nodeType: 'agentNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '2',
          type: 'customNode',
          position: { x: 250, y: 150 },
          data: { 
            label: 'Feature Selection', 
            description: 'Identify required feature services',
            nodeType: 'agentNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '3',
          type: 'customNode',
          position: { x: 250, y: 250 },
          data: { 
            label: 'Feature Retrieval', 
            description: 'Get features from feature store',
            nodeType: 'featureStoreNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '4',
          type: 'customNode',
          position: { x: 250, y: 350 },
          data: { 
            label: 'AI Analysis', 
            description: 'Process features with LLM reasoning',
            nodeType: 'agentNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '5',
          type: 'customNode',
          position: { x: 250, y: 450 },
          data: { 
            label: 'Feature Importance', 
            description: 'Calculate importance of each feature',
            nodeType: 'agentNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '6',
          type: 'customNode',
          position: { x: 250, y: 550 },
          data: { 
            label: 'AI Insights', 
            description: 'Generate enhanced insights and confidence',
            nodeType: 'agentNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '7',
          type: 'customNode',
          position: { x: 250, y: 650 },
          data: { 
            label: 'Final Results', 
            description: getTabSpecificResult(activeTab),
            nodeType: 'resultNode' 
          },
          targetPosition: Position.Top,
        },
      ];
      
      // Connect the nodes with edges
      flowEdges = [
        { id: 'e1-2', source: '1', target: '2', animated: true },
        { id: 'e2-3', source: '2', target: '3', animated: true },
        { id: 'e3-4', source: '3', target: '4', animated: true },
        { id: 'e4-5', source: '4', target: '5', animated: true },
        { id: 'e5-6', source: '5', target: '6', animated: true },
        { id: 'e6-7', source: '6', target: '7', animated: true },
      ];
    } else {
      // Traditional mode flow (simpler)
      flowNodes = [
        {
          id: '1',
          type: 'customNode',
          position: { x: 250, y: 100 },
          data: { 
            label: 'Feature Service Selection', 
            description: 'Select appropriate feature service',
            nodeType: 'traditionalNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '2',
          type: 'customNode',
          position: { x: 250, y: 225 },
          data: { 
            label: 'Feature Retrieval', 
            description: 'Get features from feature store',
            nodeType: 'featureStoreNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '3',
          type: 'customNode',
          position: { x: 250, y: 350 },
          data: { 
            label: 'Data Processing', 
            description: 'Apply business logic to features',
            nodeType: 'traditionalNode' 
          },
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        },
        {
          id: '4',
          type: 'customNode',
          position: { x: 250, y: 475 },
          data: { 
            label: 'Final Results', 
            description: getTabSpecificResult(activeTab),
            nodeType: 'resultNode' 
          },
          targetPosition: Position.Top,
        },
      ];
      
      // Connect the nodes with edges
      flowEdges = [
        { id: 'e1-2', source: '1', target: '2', animated: true },
        { id: 'e2-3', source: '2', target: '3', animated: true },
        { id: 'e3-4', source: '3', target: '4', animated: true },
      ];
    }
    
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [isAgentMode, activeTab, setNodes, setEdges]);

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

  // Event handlers
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="processing-flow-diagram" style={{ height: 700, width: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
};

export default ProcessingFlowDiagram;