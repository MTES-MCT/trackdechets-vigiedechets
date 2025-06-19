import React from "react";
import { PROFILE_OPTIONS } from "../../constants/constants.ts";
import {
  addFilter,
  removeFilter,
  SearchFilterState,
  ProfileFilterState,
} from "../../store/searchFiltersSlice";
import { useSelector } from "react-redux";
import { RootState, useAppDispatch } from "../../store/root.ts";
import { Profile, SubProfile } from "../../types.ts";

type ProfileSubFilterKey = keyof ProfileFilterState;

interface ProfilesProps {
  options?: Profile[];
  filterKey?: keyof SearchFilterState;
  subFilterKey?: ProfileSubFilterKey;
  nestLevel?: number;
  parentChecked?: boolean;
}

const Profiles: React.FC<ProfilesProps> = ({
  options = PROFILE_OPTIONS,
  filterKey = "profileFilters",
  subFilterKey = "root",
  parentChecked = true,
  nestLevel = 0,
}) => {
  const dispatch = useAppDispatch();

  const selectProfileFilters = useSelector(
    (state: RootState) => state.searchFilters.profileFilters,
  );
  const handleToggleCode = (option: Profile | SubProfile): void => {
    const code = option.value;

    if (selectProfileFilters[subFilterKey].includes(code)) {
      dispatch(
        removeFilter({
          filterKey,
          subFilterKey: subFilterKey as string,
          value: code,
        }),
      );
    } else {
      dispatch(
        addFilter({
          filterKey,
          subFilterKey: subFilterKey as string,
          value: code,
        }),
      );
    }
  };

  return options.map((option: Profile) => {
    const isChecked = selectProfileFilters[subFilterKey].includes(option.value);

    return (
      <div key={option.value}>
        <div className={`fr-mb-2v fr-checkbox-group fr-ml-${nestLevel * 4}v`}>
          <input
            id={`id_checkbox—${option.value}`}
            type="checkbox"
            className={`optionCheckbox`}
            name={option.value}
            checked={isChecked}
            onChange={() => handleToggleCode(option)}
          />
          <label htmlFor={`id_checkbox—${option.value}`}>{option.label}</label>
        </div>
        {option.options && (
          <div>
            <Profiles
              options={option.options}
              subFilterKey={option.subTypesName as ProfileSubFilterKey}
              nestLevel={nestLevel + 1}
              parentChecked={parentChecked && isChecked} // Only enable if both parent and current are checked
            />
          </div>
        )}
      </div>
    );
  });
};

export default Profiles;
