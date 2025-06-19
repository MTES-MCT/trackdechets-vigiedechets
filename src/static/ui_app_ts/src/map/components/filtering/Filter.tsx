import { Modal } from "../Modal";
import ProcessingCodes from "./Operations";
import WasteTypesAndRoles from "./WasteTypesAndRoles.tsx";
import Profiles from "./Profiles";
import Departments from "./Departments";
import WasteCodes from "./WasteCodes";
import { useSelector } from "react-redux";
import { setSelectedTab, setFilterMode } from "../../store/searchFiltersSlice";
import { WASTE_CODE, TYPE_AND_ROLE } from "../../constants/constants.ts";
import classNames from "classnames";
import { RootState, useAppDispatch } from "../../store/root.ts";

export type FilterType = typeof TYPE_AND_ROLE | typeof WASTE_CODE;

export const Filters: React.FC = () => {
  const { filterMode } = useSelector((state: RootState) => state.searchFilters);

  const dispatch = useAppDispatch();
  return (
    <Modal>
      <h1 className="fr-modal__title">Paramétrer les filtres</h1>
      <p>Je recherche par</p>
      <p>
        <label>
          <input
            type="radio"
            name="filterMode"
            onChange={() => dispatch(setFilterMode(TYPE_AND_ROLE))}
            checked={filterMode === TYPE_AND_ROLE}
          />{" "}
          Types de déchets et rôles
        </label>
        <label className="fr-ml-2w">
          <input
            type="radio"
            name="filterMode"
            onChange={() => dispatch(setFilterMode(WASTE_CODE))}
            checked={filterMode === WASTE_CODE}
          />{" "}
          Code déchet
        </label>
      </p>
      <TabSet filterMode={filterMode as FilterType} />
    </Modal>
  );
};

interface TabSetProps {
  filterMode: FilterType;
}

const TabSet: React.FC<TabSetProps> = ({ filterMode }) => {
  const searchFilters = useSelector((state: RootState) => state.searchFilters);
  const { selectedTab } = searchFilters;

  const dispatch = useAppDispatch();

  return (
    <div className="fr-tabs">
      <ul className="fr-tabs__list" role="tablist" aria-label="Filtres">
        {filterMode === TYPE_AND_ROLE && (
          <li role="presentation">
            <button
              id="tabpanel-waste-type"
              className="fr-tabs__tab"
              tabIndex={0}
              role="tab"
              aria-selected={selectedTab === 0}
              aria-controls="tabpanel-waste-type-panel"
              onClick={() => dispatch(setSelectedTab(0))}
            >
              Types de déchets et rôles
            </button>
          </li>
        )}
        {filterMode === WASTE_CODE && (
          <li role="presentation">
            <button
              id="tabpanel-waste-code"
              className="fr-tabs__tab"
              tabIndex={0}
              role="tab"
              aria-selected={selectedTab === 1}
              aria-controls="tabpanel-waste-code-panel"
              onClick={() => dispatch(setSelectedTab(1))}
            >
              Code déchet
            </button>
          </li>
        )}
        <li role="presentation">
          <button
            id="tabpanel-operation"
            className="fr-tabs__tab"
            tabIndex={0}
            role="tab"
            aria-selected={selectedTab === 2}
            aria-controls="tabpanel-operation-panel"
            onClick={() => dispatch(setSelectedTab(2))}
          >
            Traitement réalisé
          </button>
        </li>

        {filterMode === TYPE_AND_ROLE && (
          <li role="presentation">
            <button
              id="tabpanel-profile"
              className="fr-tabs__tab"
              tabIndex={-1}
              role="tab"
              aria-selected={selectedTab === 3}
              aria-controls="tabpanel-profile-panel"
              onClick={() => dispatch(setSelectedTab(3))}
            >
              Profils
            </button>
          </li>
        )}
        <li role="presentation">
          <button
            id="tabpanel-department"
            className="fr-tabs__tab"
            tabIndex={-1}
            role="tab"
            aria-selected={selectedTab === 4}
            aria-controls="tabpanel-department-panel"
            onClick={() => dispatch(setSelectedTab(4))}
          >
            Départements
          </button>
        </li>
      </ul>
      {filterMode === TYPE_AND_ROLE && (
        <div
          id="tabpanel-waste-type-panel"
          className={classNames("fr-tabs__panel", {
            "fr-tabs__panel--selected": selectedTab === 0,
          })}
          role="tabpanel"
          aria-labelledby="tabpanel-waste-type"
          tabIndex={0}
        >
          <WasteTypesAndRoles />
        </div>
      )}
      {filterMode === WASTE_CODE && (
        <div
          id="tabpanel-waste-code-panel"
          className={classNames("fr-tabs__panel", {
            "fr-tabs__panel--selected": selectedTab === 1,
          })}
          role="tabpanel"
          aria-labelledby="tabpanel-waste-code"
          tabIndex={0}
        >
          <WasteCodes />
        </div>
      )}
      <div
        id="tabpanel-operation-panel"
        className={classNames("fr-tabs__panel", {
          "fr-tabs__panel--selected": selectedTab === 2,
        })}
        role="tabpanel"
        aria-labelledby="tabpanel-operation"
        tabIndex={0}
      >
        <div>
          <ProcessingCodes />
        </div>
      </div>
      {filterMode === TYPE_AND_ROLE && (
        <div
          id="tabpanel-profile-panel"
          className={classNames("fr-tabs__panel", {
            "fr-tabs__panel--selected": selectedTab === 3,
          })}
          role="tabpanel"
          aria-labelledby="tabpanel-profile"
          tabIndex={0}
        >
          <Profiles />
        </div>
      )}
      <div
        id="tabpanel-department-panel"
        className={classNames("fr-tabs__panel", {
          "fr-tabs__panel--selected": selectedTab === 4,
        })}
        role="tabpanel"
        aria-labelledby="tabpanel-department"
        tabIndex={0}
      >
        <Departments />
      </div>
    </div>
  );
};
