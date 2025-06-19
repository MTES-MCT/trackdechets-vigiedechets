import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  popupTitle: "",
  popupText: "",
  popupRow1: [],
  popupRow2: [],
  popupRow3: [],
  popupLink: "",
  registeredOnTd: false,
};

export const mapPopupSlice = createSlice({
  name: "mapPopup",
  initialState,
  reducers: {
    setPopupData: (state, action) => {
      const {
        popupTitle,
        popupText,
        popupRow1,
        popupRow2,
        popupRow3,
        popupLink,
        registeredOnTd,
      } = action.payload;
      state.popupTitle = popupTitle || "";
      state.popupText = popupText || "";
      state.popupRow1 = popupRow1 || [];
      state.popupRow2 = popupRow2 || [];
      state.popupRow3 = popupRow3 || [];
      state.popupLink = popupLink || "";
      state.registeredOnTd = registeredOnTd;
    },
    closePopup: (state) => {
      state.popupTitle = "";
      state.popupText = "";
      state.popupRow1 = [];
      state.popupRow2 = [];
      state.popupRow3 = [];
      state.popupLink = "";
    },
  },
});

export const { setPopupData, closePopup } = mapPopupSlice.actions;

export default mapPopupSlice.reducer;
