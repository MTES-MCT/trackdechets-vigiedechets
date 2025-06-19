import searchFiltersReducer from "./searchFiltersSlice";
import uiReducer from "./uiFilterSlice";

import mapDataReducer from "./mapDataSlice.ts";
import mapUiReducer from "./mapUiSlice";
import mapPopupReducer from "./mapPopupSlice.ts";

import modalReducer from "./modalSlice";
import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, TypedUseSelectorHook, useSelector } from "react-redux";

export const store = configureStore({
  reducer: {
    searchFilters: searchFiltersReducer,
    ui: uiReducer,
    mapData: mapDataReducer,
    mapUi: mapUiReducer,
    mapPopup: mapPopupReducer,
    modal: modalReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // To allow non-serializable data like bounds objects
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = useDispatch.withTypes<AppDispatch>(); // Export a hook that can be reused to resolve types
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
