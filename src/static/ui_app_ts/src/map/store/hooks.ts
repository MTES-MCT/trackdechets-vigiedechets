import { useEffect } from "react";
import { fetchPlots } from "./mapDataSlice";
import { closePopup } from "./mapPopupSlice";
import { useAppDispatch, useAppSelector } from "./root";

// Custom hook to fetch plots whenever filters or bounds change
export const useFetchPlots = () => {
  const dispatch = useAppDispatch();

  const {
    departmentFilters,
    profileFilters,
    operationCodeFilters,
    bsdTypeFilters,
    wasteCodesFilter,
    roleFilters,
  } = useAppSelector((state) => state.searchFilters);
  const { opened: modalOpened } = useAppSelector((state) => state.modal);
  const bounds = useAppSelector((state) => state.mapUi.bounds);

  useEffect(() => {
    // trigger only if modal not opened
    if (!modalOpened) {
      dispatch(closePopup());
      dispatch(fetchPlots());
    }
  }, [
    dispatch,
    bsdTypeFilters,
    profileFilters,
    roleFilters,
    operationCodeFilters,
    departmentFilters,
    wasteCodesFilter,
    modalOpened,
    bounds,
  ]);
};
