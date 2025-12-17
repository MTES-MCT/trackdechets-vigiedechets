import { useCallback, useEffect, useState } from "react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
} from "reactflow";
import "reactflow/dist/style.css";
import { useSelector } from "react-redux";
import CustomNode from "./CustomNode";

interface GalaxyState {
  nodes: Array<{ id: string; label: string }>;
  edges: Array<{ source: string; target: string; weight: number }>;
}

export default function Graph() {
  const { nodes: graphNodes, edges: graphEdges } = useSelector(
    (state: { galaxy: GalaxyState }) => state.galaxy
  );

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Définir les types de nœuds personnalisés
  const nodeTypes: NodeTypes = {
    custom: CustomNode,
  };

  // Mettre à jour les nœuds et edges quand les données changent
  useEffect(() => {
    setNodes((currentNodes) => {
      const nodeMap = new Map(currentNodes.map((n) => [n.id, n]));
      
      const newNodes: Node[] = graphNodes.map((node) => {
        // Préserver la position existante si le nœud existe déjà
        const existingNode = nodeMap.get(node.id);
        return {
          id: node.id,
          type: "custom",
          position: existingNode?.position || {
            x: Math.random() * 1000,
            y: Math.random() * 1000,
          },
          data: {
            label: node.label || node.id,
          },
        };
      });
      
      return newNodes;
    });

    const newEdges: Edge[] = graphEdges.map((edge, index) => ({
      id: `edge-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.weight.toString(),
      style: {
        strokeWidth: Math.min(edge.weight, 5),
      },
    }));

    setEdges(newEdges);
  }, [graphNodes, graphEdges, setNodes, setEdges]);

  // Si pas de données, afficher un message
  if (graphNodes.length === 0) {
    return (
      <div style={{ width: "100%", height: "80vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ padding: "2rem", textAlign: "center", color: "#666" }}>
          <p style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Aucune relation trouvée</p>
          <p style={{ fontSize: "0.9rem" }}>Essayez de modifier les filtres ou de réinitialiser la recherche.</p>
        </div>
      </div>
    );
  }

  const onNodeDoubleClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      // Vérifier si le double-clic est sur le bouton d'expansion
      const target = event.target as HTMLElement;
      if (target.closest('[data-expand-button]')) {
        // Le bouton gère son propre clic
        return;
      }
      // Sinon, permettre le comportement par défaut
    },
    []
  );

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      // Vérifier si le clic est sur le bouton d'expansion
      const target = event.target as HTMLElement;
      if (target.closest('[data-expand-button]')) {
        // Le bouton gère son propre clic, ne rien faire ici
        return;
      }
    },
    []
  );

  return (
    <div style={{ width: "100%", height: "80vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        nodesDraggable={true}
        nodesConnectable={false}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
