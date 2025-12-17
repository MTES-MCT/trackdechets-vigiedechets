import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setSiretFilter, setMinWeightFilter, fetchGraph, clearFilters } from "../../store/galaxySlice";

export default function Filters() {
  const dispatch = useDispatch();
  const { filters, loading } = useSelector(
    (state: {
      galaxy: {
        filters: { siret: string; min_weight: number };
        loading: boolean;
      };
    }) => state.galaxy
  );

  const [localSiret, setLocalSiret] = useState(filters.siret);
  const [localMinWeight, setLocalMinWeight] = useState(filters.min_weight.toString());

  const handleApplyFilters = () => {
    const trimmedSiret = localSiret.trim();
    const minWeight = parseInt(localMinWeight) || 1;
    
    console.log("Applying filters:", { siret: trimmedSiret, min_weight: minWeight });
    
    dispatch(setSiretFilter(trimmedSiret));
    dispatch(setMinWeightFilter(minWeight));
    
    // Ne pas envoyer siret si vide
    const params: { siret?: string; min_weight: number } = {
      min_weight: minWeight,
    };
    if (trimmedSiret) {
      // Valider que le SIRET est bien 14 chiffres
      if (trimmedSiret.length === 14 && /^\d+$/.test(trimmedSiret)) {
        params.siret = trimmedSiret;
      } else {
        alert(`SIRET invalide. Le SIRET doit contenir exactement 14 chiffres. Vous avez saisi: "${trimmedSiret}" (${trimmedSiret.length} caractères)`);
        return;
      }
    }
    
    console.log("Dispatching fetchGraph with params:", params);
    dispatch(fetchGraph(params));
  };

  const handleClearFilters = () => {
    setLocalSiret("");
    setLocalMinWeight("1");
    dispatch(clearFilters());
    dispatch(fetchGraph({ min_weight: 1 }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleApplyFilters();
    }
  };

  return (
    <div
      style={{
        padding: "1rem",
        backgroundColor: "#f5f5f5",
        borderBottom: "1px solid #ddd",
        display: "flex",
        gap: "1rem",
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        <label htmlFor="siret-filter" style={{ fontSize: "0.875rem", fontWeight: "bold" }}>
          Filtrer par SIRET :
        </label>
        <input
          id="siret-filter"
          type="text"
          value={localSiret}
          onChange={(e) => setLocalSiret(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="12345678901234"
          maxLength={14}
          style={{
            padding: "0.5rem",
            border: "1px solid #ccc",
            borderRadius: "4px",
            width: "200px",
          }}
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        <label htmlFor="min-weight-filter" style={{ fontSize: "0.875rem", fontWeight: "bold" }}>
          Nombre minimum de BSD :
        </label>
        <input
          id="min-weight-filter"
          type="number"
          value={localMinWeight}
          onChange={(e) => setLocalMinWeight(e.target.value)}
          onKeyPress={handleKeyPress}
          min="1"
          style={{
            padding: "0.5rem",
            border: "1px solid #ccc",
            borderRadius: "4px",
            width: "120px",
          }}
        />
      </div>

      <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end" }}>
        <button
          onClick={handleApplyFilters}
          disabled={loading}
          style={{
            padding: "0.5rem 1rem",
            backgroundColor: "#0066cc",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Chargement..." : "Appliquer"}
        </button>
        <button
          onClick={handleClearFilters}
          disabled={loading}
          style={{
            padding: "0.5rem 1rem",
            backgroundColor: "#666",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          Réinitialiser
        </button>
      </div>
    </div>
  );
}
