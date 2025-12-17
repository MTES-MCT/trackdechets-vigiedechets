import { useState, useRef, useEffect } from "react";
import { Handle, Position, NodeProps } from "reactflow";

interface CustomNodeData {
  label: string;
}

const MAX_LENGTH = 25; // Nombre maximum de caractères avant troncature

export default function CustomNode({ data }: NodeProps<CustomNodeData>) {
  const label = data.label || "";
  // Gérer l'état d'expansion localement dans le composant
  const [isExpanded, setIsExpanded] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Déterminer si le nom doit être tronqué
  const shouldTruncate = label.length > MAX_LENGTH;
  const displayLabel = isExpanded || !shouldTruncate ? label : `${label.substring(0, MAX_LENGTH)}...`;

  // Gérer le clic sur le bouton avec un event listener direct en phase de capture (backup)
  useEffect(() => {
    const button = buttonRef.current;
    if (!button || !shouldTruncate) return;

    const handleClick = (e: MouseEvent) => {
      e.stopPropagation();
      e.stopImmediatePropagation();
      e.preventDefault();
      console.log("Button clicked via event listener (backup), toggling expansion");
      setIsExpanded((prev) => {
        const newValue = !prev;
        console.log("Expansion state changed to:", newValue);
        return newValue;
      });
    };

    const handleMouseDown = (e: MouseEvent) => {
      e.stopPropagation();
      e.stopImmediatePropagation();
      e.preventDefault();
    };

    // Utiliser la phase de capture pour intercepter avant React Flow
    const options = { capture: true };
    button.addEventListener("click", handleClick, options);
    button.addEventListener("mousedown", handleMouseDown, options);

    return () => {
      button.removeEventListener("click", handleClick, options);
      button.removeEventListener("mousedown", handleMouseDown, options);
    };
  }, [shouldTruncate]);

  return (
    <div
      style={{
        padding: "8px 12px",
        backgroundColor: "white",
        border: "2px solid #1a192b",
        borderRadius: "4px",
        minWidth: "120px",
        maxWidth: isExpanded ? "300px" : "200px",
        fontSize: "11px",
        textAlign: "center",
        wordWrap: "break-word",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        transition: "max-width 0.2s ease",
        position: "relative",
      }}
      title={label}
    >
      <Handle type="target" position={Position.Top} style={{ background: "#555", width: "8px", height: "8px" }} />
      <div
        style={{
          fontWeight: "500",
          lineHeight: "1.3",
          color: "#1a192b",
          userSelect: "none",
        }}
      >
        {displayLabel}
      </div>
      {shouldTruncate && (
        <button
          ref={buttonRef}
          type="button"
          data-expand-button="true"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log("Button onClick handler called");
            setIsExpanded((prev) => !prev);
          }}
          onMouseDown={(e) => {
            e.stopPropagation();
            e.preventDefault();
          }}
          style={{
            fontSize: "10px",
            color: "#0066cc",
            marginTop: "6px",
            fontWeight: "500",
            background: "#f0f0f0",
            border: "1px solid #0066cc",
            borderRadius: "3px",
            cursor: "pointer",
            padding: "4px 8px",
            width: "100%",
            transition: "background-color 0.2s",
            userSelect: "none",
            touchAction: "none",
            pointerEvents: "auto",
            zIndex: 1000,
            position: "relative",
            fontFamily: "inherit",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#e0e0e0";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "#f0f0f0";
          }}
        >
          {isExpanded ? "▼ Réduire" : "▶ Voir plus"}
        </button>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: "#555", width: "8px", height: "8px" }} />
    </div>
  );
}
