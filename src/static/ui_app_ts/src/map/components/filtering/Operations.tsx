import { PROCESSING_CODES } from "../../constants/operations";

import { addFilter, removeFilter } from "../../store/searchFiltersSlice";
import { useSelector } from "react-redux";
import { RootState, useAppDispatch } from "../../store/root";
import { ROLE_DESTINATION, WASTE_CODE } from "../../constants/constants";

type ProcessingCodesProps = object;

const ProcessingCodes: React.FC<ProcessingCodesProps> = () => {
  const dispatch = useAppDispatch();

  const {
    roleFilters: selectRoleFilters,
    operationCodeFilters: selectOperationCodeFilters,
    filterMode,
  } = useSelector((state: RootState) => state.searchFilters);
  const wasteCodeMode = filterMode === WASTE_CODE;
  const roleDestinationSelected =
    selectRoleFilters.root.includes(ROLE_DESTINATION) || wasteCodeMode;

  const handleToggleCode = (code: string): void => {
    if (selectOperationCodeFilters.root.includes(code)) {
      dispatch(
        removeFilter({
          filterKey: "operationCodeFilters",
          value: code,
        }),
      );
    } else {
      dispatch(
        addFilter({
          filterKey: "operationCodeFilters",
          value: code,
        }),
      );
    }
  };

  const handleToggleDestinationRole = (): void => {
    if (roleDestinationSelected) {
      dispatch(
        removeFilter({
          filterKey: "roleFilters",
          value: ROLE_DESTINATION,
        }),
      );
    } else {
      dispatch(
        addFilter({
          filterKey: "roleFilters",
          value: ROLE_DESTINATION,
        }),
      );
    }
  };

  return (
    <div>
      <h2>Codes de traitement des déchets</h2>
      {!wasteCodeMode && (
        <div className="fr-toggle fr-mb-3w">
          <input
            type="checkbox"
            className="fr-toggle__input"
            aria-describedby="toggle-4633-messages"
            id="id_toggle_role_destination"
            checked={roleDestinationSelected}
            onChange={() => handleToggleDestinationRole()}
          />{" "}
          <label
            className="fr-toggle__label"
            htmlFor="id_toggle_role_destination"
          >
            Le rôle destinataire doit être activé pour choisir un ou des
            traitements réalisés
          </label>
        </div>
      )}
      <div>
        <div>
          {Object.entries(PROCESSING_CODES).map(([key, item]) => (
            <div key={key} className="fr-fieldset__element">
              <div className="fr-checkbox-group">
                <input
                  type="checkbox"
                  id={item.code}
                  disabled={!roleDestinationSelected}
                  checked={selectOperationCodeFilters.root.includes(item.code)}
                  onChange={() => handleToggleCode(item.code)}
                />
                <label htmlFor={item.code}>
                  {item.code} - {item.description}
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProcessingCodes;
