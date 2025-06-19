import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import {
  PROFILE_OPTIONS,
  ROLE_DESTINATION,
  ROLE_TRANSPORTER,
  TYPE_AND_ROLE,
  ROLE_WORKER,
  BSDA,
  SSD,
  TEXS,
  SUB_PROFILES,
} from "../constants/constants.ts";

import { FilterValue } from "../types.ts";

export interface ProfileFilterState extends FilterValue {
  collectorTypes: string[];
  wasteProcessorTypes: string[];
  wasteVehiclesTypes: string[];
}

export interface SearchFilterState {
  selectedTab: number;
  filterMode: string;
  bsdTypeFilters: FilterValue; // which type of bsd ? Dasri, bsda etc…
  roleFilters: FilterValue; // which role on the bsd ? Emitter, Transporter…
  profileFilters: ProfileFilterState;
  operationCodeFilters: FilterValue;
  departmentFilters: FilterValue;
  wasteCodesFilter: FilterValue;
}

const initialFilters = {
  bsdTypeFilters: { root: [] },
  roleFilters: { root: [] },
  profileFilters: {
    root: [],
    collectorTypes: [],
    wasteProcessorTypes: [],
    wasteVehiclesTypes: [],
  },
  operationCodeFilters: { root: [] },
  departmentFilters: { root: [] },
  wasteCodesFilter: { root: [] },
};
const initialState: SearchFilterState = {
  selectedTab: 0,
  filterMode: TYPE_AND_ROLE,
  ...initialFilters,
};

interface AddRemoveFilterPayload {
  filterKey: keyof SearchFilterState;
  subFilterKey?: string;
  value: string;
}

interface ClearFilterPayload {
  filterKey: keyof SearchFilterState;
  subFilterKey?: string;
}

const getSubFilterKeyForProfileValue = (value: string): string | null => {
  const profileOption = PROFILE_OPTIONS.find(
    (option) => option.value === value,
  );

  if (profileOption && profileOption.subTypesName) {
    return profileOption.subTypesName;
  }

  return null;
};

export const searchFiltersSlice = createSlice({
  name: "searchFilters",
  initialState,
  reducers: {
    addFilter: (state, action: PayloadAction<AddRemoveFilterPayload>) => {
      const { filterKey, subFilterKey = "root", value } = action.payload;

      const filterState = state[filterKey] as Record<string, string[]>;

      const arr = filterState[subFilterKey];
      if (!arr.includes(value)) {
        arr.push(value);
      }
      // special handling for subprofiles
      if (filterKey === "profileFilters" && subFilterKey === "root") {
        const childFilterKey = getSubFilterKeyForProfileValue(value);
        if (childFilterKey) {
          const subProfiles = SUB_PROFILES[childFilterKey];
          filterState[childFilterKey] = subProfiles.map((p) => p.value);
        }
      }
    },
    setFilter: (state, action: PayloadAction<AddRemoveFilterPayload>) => {
      const { filterKey, subFilterKey = "root", value } = action.payload;

      const filterState = state[filterKey] as Record<string, string[]>;

      filterState[subFilterKey] = [value];
    },
    removeFilter: (state, action: PayloadAction<AddRemoveFilterPayload>) => {
      const { filterKey, subFilterKey = "root", value } = action.payload;

      const filterState = state[filterKey] as Record<string, string[]>;
      const arr = filterState[subFilterKey];

      const index = arr.findIndex((el: string) => el === value);

      if (index !== -1) arr.splice(index, 1);

      if (value === ROLE_DESTINATION) {
        // reset operation codes when destination role is removed
        state.operationCodeFilters = initialFilters.operationCodeFilters;
      }
    },
    clearFilter: (state, action: PayloadAction<ClearFilterPayload>) => {
      const { filterKey, subFilterKey = "root" } = action.payload;
      const filterState = state[filterKey] as Record<string, string[]>;
      filterState[subFilterKey] = [];
    },

    resetFilters: () => {
      return initialState;
    },

    setSelectedTab: (state, action) => {
      state.selectedTab = action.payload;
    },
    setFilterMode: (state, action) => {
      state.filterMode = action.payload;
      state.selectedTab = state.filterMode === TYPE_AND_ROLE ? 0 : 1;
      const departmentFilters = state.departmentFilters;
      Object.assign(state, initialFilters);
      // keep departments when changing mode
      state.departmentFilters = departmentFilters;
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(
      ({ type }) => type.startsWith("searchFilters"),
      (state) => {
        // Post-process the state
        // BSDA
        if (!state.bsdTypeFilters.root.includes(BSDA)) {
          const workerIndex = state.roleFilters.root.findIndex(
            (role) => role === ROLE_WORKER,
          );
          if (workerIndex !== -1) {
            state.roleFilters.root.splice(workerIndex, 1);
          }
        }
        // SSD
        if (
          state.bsdTypeFilters.root.includes(SSD) &&
          state.roleFilters.root.length
        ) {
          state.roleFilters.root = [];
        }
        // TEXS
        if (state.bsdTypeFilters.root.includes(TEXS)) {
          const transporterIndex = state.roleFilters.root.findIndex(
            (role) => role === ROLE_TRANSPORTER,
          );
          if (transporterIndex !== -1) {
            state.roleFilters.root.splice(transporterIndex, 1);
          }
        }
      },
    );
  },
});

export const {
  addFilter,
  setFilter,
  removeFilter,
  clearFilter,
  resetFilters,
  setSelectedTab,
  setFilterMode,
} = searchFiltersSlice.actions;

export default searchFiltersSlice.reducer;
