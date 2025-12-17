import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

interface Node {
  id: string;
  label: string;
  size: number;
  type?: string[];
  metadata?: Record<string, unknown>;
}

interface Edge {
  source: string;
  target: string;
  weight: number;
  types: string[];
  roles: string[];
}

interface GalaxyState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  loading: boolean;
  error: string | null;
  filters: {
    siret: string;
    min_weight: number;
  };
}

const initialState: GalaxyState = {
  nodes: [],
  edges: [],
  selectedNode: null,
  loading: false,
  error: null,
  filters: {
    siret: "",
    min_weight: 1,
  },
};

export const fetchGraph = createAsyncThunk(
  "galaxy/fetchGraph",
  async (params: { siret?: string; bsd_types?: string[]; date_from?: string; date_to?: string; min_weight?: number }) => {
    const queryParams = new URLSearchParams();
    if (params.siret) {
      queryParams.append("siret", params.siret);
      console.log("Adding SIRET to query params:", params.siret);
    }
    if (params.bsd_types) params.bsd_types.forEach((t) => queryParams.append("bsd_types", t));
    if (params.date_from) queryParams.append("date_from", params.date_from);
    if (params.date_to) queryParams.append("date_to", params.date_to);
    if (params.min_weight) queryParams.append("min_weight", params.min_weight.toString());

    const url = `/galaxy/api/graph?${queryParams.toString()}`;
    console.log("Fetching graph from URL:", url);
    const response = await axios.get(url);
    console.log("Graph response:", { nodes: response.data.nodes?.length, edges: response.data.edges?.length });
    return response.data;
  }
);

const galaxySlice = createSlice({
  name: "galaxy",
  initialState,
  reducers: {
    selectNode: (state, action) => {
      state.selectedNode = action.payload;
    },
    resetView: (state) => {
      state.selectedNode = null;
    },
    setSiretFilter: (state, action: { payload: string }) => {
      state.filters.siret = action.payload;
    },
    setMinWeightFilter: (state, action: { payload: number }) => {
      state.filters.min_weight = action.payload;
    },
    clearFilters: (state) => {
      state.filters.siret = "";
      state.filters.min_weight = 1;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchGraph.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchGraph.fulfilled, (state, action) => {
        state.loading = false;
        state.nodes = action.payload.nodes || [];
        state.edges = action.payload.edges || [];
      })
      .addCase(fetchGraph.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "Erreur lors du chargement du graphe";
      });
  },
});

export const { selectNode, resetView, setSiretFilter, setMinWeightFilter, clearFilters } = galaxySlice.actions;
export default galaxySlice.reducer;
