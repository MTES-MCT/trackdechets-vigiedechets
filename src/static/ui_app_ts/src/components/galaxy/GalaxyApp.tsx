import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchGraph } from "../../store/galaxySlice";
import Graph from "./Graph";
import Filters from "./Filters";

export default function GalaxyApp() {
  const dispatch = useDispatch();
  const { loading, error } = useSelector((state: { galaxy: { loading: boolean; error: string | null } }) => state.galaxy);

  useEffect(() => {
    dispatch(fetchGraph({ min_weight: 1 }));
  }, [dispatch]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Filters />
      {loading && (
        <div style={{ padding: "1rem", textAlign: "center" }}>Chargement du graphe...</div>
      )}
      {error && (
        <div style={{ padding: "1rem", textAlign: "center", color: "red" }}>Erreur: {error}</div>
      )}
      {!loading && !error && <Graph />}
    </div>
  );
}
