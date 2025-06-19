import { createSlice } from "@reduxjs/toolkit";
import { RootState } from "./root";
import { MapUiState } from "../types";

const initialState: MapUiState = {
  zoom: 5,
  bounds: {
    _sw: { lng: 0, lat: 0 },
    _ne: { lng: 0, lat: 0 },
  },
};

export const mapUiSlice = createSlice({
  name: "mapUi",
  initialState,
  reducers: {
    setZoom: (state, action) => {
      state.zoom = action.payload;
    },
    setBounds: (state, action) => {
      state.bounds = action.payload;
    },
  },
});

export const { setZoom, setBounds } = mapUiSlice.actions;

// Selectors
export const selectZoom = (state: RootState) => state.mapUi.zoom;

export default mapUiSlice.reducer;
