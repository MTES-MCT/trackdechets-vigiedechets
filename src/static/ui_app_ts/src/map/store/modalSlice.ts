import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  opened: false,
};

export const mapModalSlice = createSlice({
  name: "mapModal",
  initialState,
  reducers: {
    setModalState: (state, action) => {
      state.opened = action.payload;
    },
  },
});

const { actions, reducer } = mapModalSlice;

export const { setModalState } = actions;

export default reducer;
