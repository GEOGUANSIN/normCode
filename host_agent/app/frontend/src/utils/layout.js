export const calculateHierarchicalLayout = (nodes, edges) => {
  // Create adjacency list
  const adjacencyList = {};
  const inDegree = {};
  
  // Initialize adjacency list and in-degree count
  nodes.forEach(node => {
    adjacencyList[node.id] = [];
    inDegree[node.id] = 0;
  });
  
  // Build adjacency list and count in-degrees
  edges.forEach(edge => {
    adjacencyList[edge.source].push(edge.target);
    inDegree[edge.target]++;
  });
  
  // Find leaf nodes (nodes with no outgoing edges)
  const leafNodes = nodes.filter(node => adjacencyList[node.id].length === 0);
  
  // Calculate levels using BFS starting from leaf nodes
  const levels = [];
  const visited = new Set();
  
  const bfs = (startNode) => {
    const queue = [{ node: startNode, level: 0 }];
    visited.add(startNode.id);
    
    while (queue.length > 0) {
      const { node, level } = queue.shift();
      
      // Ensure level array exists
      if (!levels[level]) {
        levels[level] = [];
      }
      levels[level].push(node);
      
      // Process parents (nodes that have this node as a child)
      const parents = nodes.filter(n => adjacencyList[n.id].includes(node.id));
      parents.forEach(parent => {
        if (!visited.has(parent.id)) {
          visited.add(parent.id);
          queue.push({ node: parent, level: level + 1 });
        }
      });
    }
  };
  
  // Start BFS from each leaf node
  leafNodes.forEach(leaf => {
    if (!visited.has(leaf.id)) {
      bfs(leaf);
    }
  });
  
  // Calculate positions
  const VERTICAL_SPACING = 150;
  const MIN_NODE_SPACING = 100; // Minimum space between nodes
  
  // Reverse the levels array to start from bottom
  levels.reverse();
  
  levels.forEach((levelNodes, levelIndex) => {
    // Calculate node widths based on their content
    const nodeWidths = levelNodes.map(node => {
      const labelLength = node.data?.label?.length || 0;
      // Base width + additional width based on label length
      return Math.max(150, 150 + (labelLength * 8));
    });
    
    // Calculate total width needed for this level
    const totalWidth = nodeWidths.reduce((sum, width) => sum + width + MIN_NODE_SPACING, 0);
    let currentX = -totalWidth / 2;
    
    // Position nodes with calculated spacing
    levelNodes.forEach((node, index) => {
      // Add half of this node's width to center it
      currentX += nodeWidths[index] / 2;
      
      node.position = {
        x: currentX,
        y: levelIndex * VERTICAL_SPACING
      };
      
      // Move to next position, adding the other half of this node's width plus minimum spacing
      currentX += nodeWidths[index] / 2 + MIN_NODE_SPACING;
    });
  });
  
  return nodes;
}; 