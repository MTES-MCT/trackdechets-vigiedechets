import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../../map/store/root.ts";
import axios from "axios";

const buildUrl = (
  adminDivision: string,
  year: string,
  rubrique: string,
): string => {
  return `/map/api/icpe/${adminDivision}/${year}/${rubrique}`;
};

const buildInstallationsUrl = (year: string, rubrique: string): string => {
  return `/map/api/icpe/installations/${year}/${rubrique}`;
};

const buildGraphUrl = (state, layer: string): string => {
  const code =
    layer === "regions"
      ? state.selectedRegion.code_region_insee
      : layer === "departements"
        ? state.selectedDepartement.code_departement_insee
        : layer === "installations"
          ? state.selectedCompany.code_aiot
          : "";
  return `/map/api/icpe-graph/${layer}/${state.year}/${state.rubrique}/${code}`;
};

const buildInstallationDetailUrl = (
  year: string,
  rubrique: string,
  aiotCode: string,
): string => {
  return `/map/api/icpe-graph/installations/${year}/${rubrique}/${aiotCode}`;
};

type departementDataRow = {
  code_departement_insee: string;
  nom_departement: string;
  quantite_autorisee: number;
  taux_consommation: null;
  cumul_quantite_traitee: number;
  nombre_installations: number;
};

type regionDataRow = {
  code_region_insee: string;
  nom_region: string;
  quantite_autorisee: number;
  taux_consommation: null;
  cumul_quantite_traitee: number;
  nombre_installations: number;
};
type plotPopup = {
  latitude: number;
  longitude: number;
  text: string;
};

interface UiState {
  adminDivision: string;
  displayPlots: boolean;
  rubrique: string;
  year: string;
  regionData: regionDataRow[];
  departementsData: departementDataRow[];
  installationsData: any[];
  plotPopup: null | plotPopup;
  statsOpened: boolean;
  statsInfo: string;
  statsTitle: string;
  graphData: any;
  selectedRegion: any;
  selectedDepartement: any;
  selectedCompany: any;
  graphUrl: string;
}

export const fetchData = createAsyncThunk<
  any,
  void,
  {
    state: RootState;
  }
>(
  "mapData/fetchData",
  async (_, { getState }: { getState: () => RootState }) => {
    const state = getState();

    const { adminDivision, year, rubrique } = state.ui;

    const url = buildUrl(adminDivision, year, rubrique);

    const response = await axios.get(url);

    return { ...response.data };
  },
);

export const fetchInstallations = createAsyncThunk<
  any,
  void,
  {
    state: RootState;
  }
>(
  "mapData/fetchInstallations",
  async (_, { getState }: { getState: () => RootState }) => {
    const state = getState();

    const { year, rubrique } = state.ui;

    const url = buildInstallationsUrl(year, rubrique);

    const response = await axios.get(url);

    return { ...response.data };
  },
);
export const fetchGraph = createAsyncThunk<
  any,
  void,
  {
    state: RootState;
  }
>(
  "mapData/fetchGraph",
  async (_, { getState }: { getState: () => RootState }) => {
    const state = getState();

    const { year, rubrique, selectedCompany } = state.ui;

    const url = buildInstallationDetailUrl(
      year,
      rubrique,
      selectedCompany.aiotCode,
    );

    const response = await axios.get(url);

    return { html: response.data };
  },
);

const initialState: UiState = {
  adminDivision: "regions",
  displayPlots: false,
  rubrique: "2760-1",
  year: "2025",
  regionData: [],
  departementsData: [],
  installationsData: [],
  plotPopup: null,
  statsOpened: false,
  statsInfo: "",
  statsTitle: "",
  graphData: {},

  selectedCompany: {},
  selectedRegion: {},
  selectedDepartement: {},
  graphUrl: "",
};

export const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setAdminDivision: (state, action: PayloadAction<string>) => {
      state.adminDivision = action.payload;
    },
    toggleDisplayPlots: (state, action: PayloadAction<boolean>) => {
      state.displayPlots = action.payload;
    },

    setRubrique: (state, action) => {
      state.rubrique = action.payload;
    },

    setYear: (state, action) => {
      state.year = action.payload;
    },
    setPlotPopup: (state, action) => {
      state.plotPopup = action.payload;
    },

    setStatsOpened: (state, action) => {
      state.statsOpened = action.payload;
    },
    setSelectedCompany: (state, action) => {
      state.selectedCompany = action.payload;
      state.selectedRegion = null;
      state.selectedDepartement = null;
      state.graphUrl = buildGraphUrl(state, "installations");
    },
    setSelectedRegion: (state, action) => {
      if (action.payload.code in state.regionData) {
        state.selectedRegion =
          state.regionData[parseInt(action.payload.code, 10)];
        state.graphUrl = buildGraphUrl(state, "regions");
      } else {
        state.selectedRegion = {
          nom_region: action.payload.name,
          code_region_insee: action.payload.code,
        };
        state.graphUrl = "";
      }
      state.selectedCompany = null;
      state.selectedDepartement = null;
    },
    setSelectedDepartment: (state, action) => {
      if (action.payload.code in state.departementsData) {
        state.selectedDepartement =
          state.departementsData[parseInt(action.payload.code, 10)];
        state.graphUrl = buildGraphUrl(state, "departements");
      } else {
        state.selectedDepartement = {
          nom_departement: action.payload.name,
          code_department_insee: action.payload.code,
        };
        state.graphUrl = "";
      }

      state.selectedRegion = null;
      state.selectedCompany = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchData.pending, (state) => {
        // state.status = "loading";
      })
      .addCase(fetchData.fulfilled, (state, action) => {
        // state.status = "loading";
        if (state.adminDivision === "regions") {
          state.regionData = action.payload.data;
        }
        if (state.adminDivision === "departements") {
          state.departementsData = action.payload.data;
        }
      })
      .addCase(fetchInstallations.fulfilled, (state, action) => {
        // state.status = "loading";

        state.installationsData = action.payload;
      })
      .addCase(fetchGraph.fulfilled, (state, action) => {
        // state.status = "loading";

        state.graphData = action.payload;
      });
  },
});

export const {
  setAdminDivision,
  toggleDisplayPlots,
  setYear,
  setRubrique,
  setPlotPopup,
  setStatsOpened,
  setSelectedCompany,
  setSelectedRegion,
  setSelectedDepartment,
} = uiSlice.actions;

export default uiSlice.reducer;
