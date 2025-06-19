import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "./root";

interface UiState {
  expandedRegions: Record<string, boolean>;
}

const initialState: UiState = {
  expandedRegions: {},
};

export const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleRegion: (state, action: PayloadAction<string>) => {
      const regionCode = action.payload;
      state.expandedRegions[regionCode] = !state.expandedRegions[regionCode];
    },
  },
});

export const { toggleRegion } = uiSlice.actions;

export const selectExpandedRegions = (state: RootState) =>
  state.ui.expandedRegions;

export default uiSlice.reducer;
