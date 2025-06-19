import React from "react";
import { useSelector } from "react-redux";
import { RootState, useAppDispatch } from "../../store/root";
import { FRENCH_REGIONS_WITH_DEPARTMENTS } from "../../constants/departments.ts";
import { addFilter, removeFilter } from "../../store/searchFiltersSlice";
import { toggleRegion, selectExpandedRegions } from "../../store/uiFilterSlice";

const RegionDepartmentSelector: React.FC = () => {
  const dispatch = useAppDispatch();

  // Get department filters from Redux store
  const departmentFilters = useSelector(
    (state: RootState) => state.searchFilters.departmentFilters,
  );

  // Get expanded regions state from Redux store
  const expandedRegions = useSelector(selectExpandedRegions);

  // Toggle a region's expanded state using Redux
  const handleToggleRegion = (regionCode: string) => {
    dispatch(toggleRegion(regionCode));
  };

  // Check if all departments in a region are selected
  const isRegionSelected = (regionCode: string) => {
    const region = FRENCH_REGIONS_WITH_DEPARTMENTS.find(
      (r) => r.code === regionCode,
    );

    if (!region) return false;

    // If there are no departments in the region, return false
    if (region.departments.length === 0) return false;

    // Check if all departments in this region are in the departmentFilters
    return region.departments.every((dept) =>
      departmentFilters.root.includes(dept.code),
    );
  };

  // Handle region checkbox changes
  const handleRegionCheck = (regionCode: string, checked: boolean) => {
    const region = FRENCH_REGIONS_WITH_DEPARTMENTS.find(
      (r) => r.code === regionCode,
    );

    if (!region) return;

    // When a region is checked/unchecked, update all its departments
    region.departments.forEach((dept) => {
      if (checked) {
        // Add department if not already selected
        if (!departmentFilters.root.includes(dept.code)) {
          dispatch(
            addFilter({
              filterKey: "departmentFilters",
              value: dept.code,
            }),
          );
        }
      } else {
        // Remove department if selected
        if (departmentFilters.root.includes(dept.code)) {
          dispatch(
            removeFilter({
              filterKey: "departmentFilters",
              value: dept.code,
            }),
          );
        }
      }
    });
  };

  // Handle department checkbox changes
  const handleDepartmentCheck = (deptCode: string, checked: boolean) => {
    if (checked) {
      dispatch(
        addFilter({
          filterKey: "departmentFilters",
          value: deptCode,
        }),
      );
    } else {
      dispatch(
        removeFilter({
          filterKey: "departmentFilters",
          value: deptCode,
        }),
      );
    }
  };

  return (
    <div>
      {FRENCH_REGIONS_WITH_DEPARTMENTS.map((region) => (
        <div key={region.code}>
          <div className="flex align-items-center">
            <button
              className="fr-btn--tertiary-no-outline fr-btn--sm"
              onClick={() => handleToggleRegion(region.code)}
            >
              {expandedRegions[region.code] ? (
                <span
                  className="fr-icon-arrow-down-s-line"
                  aria-hidden="true"
                ></span>
              ) : (
                <span
                  className="fr-icon-arrow-right-s-line"
                  aria-hidden="true"
                ></span>
              )}
            </button>
            <div className="fr-checkbox-group fr-checkbox-group--sm">
              <input
                type="checkbox"
                id={`region-${region.code}`}
                checked={isRegionSelected(region.code)}
                onChange={(e) =>
                  handleRegionCheck(region.code, e.target.checked)
                }
              />
              <label htmlFor={`region-${region.code}`} className="pointable">
                {region.name}
              </label>
            </div>
          </div>

          {expandedRegions[region.code] && (
            <div className="fr-ml-8w">
              {region.departments.map((dept) => (
                <div key={dept.code} className="flex fr-mt-1w">
                  <div className="fr-checkbox-group fr-checkbox-group--sm">
                    <input
                      type="checkbox"
                      id={`dept-${dept.code}`}
                      checked={departmentFilters.root.includes(dept.code)}
                      onChange={(e) =>
                        handleDepartmentCheck(dept.code, e.target.checked)
                      }
                      className="mr-2"
                    />
                    <label htmlFor={`dept-${dept.code}`} className="pointable">
                      {dept.name}
                    </label>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default RegionDepartmentSelector;
