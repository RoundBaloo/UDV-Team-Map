export const findNodeInSubtree = (node, targetId) => {
  const nodeId = node.org_unit_id || node.id;
  if (nodeId === targetId) return true;
  
  if (node.children) {
    for (let child of node.children) {
      if (findNodeInSubtree(child, targetId)) return true;
    }
  }
  
  return false;
};