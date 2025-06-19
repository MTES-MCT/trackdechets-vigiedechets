import {
  VERBOSE_ROLES,
  PROFILE_MAPPING,
  VERBOSE_BSD_TYPES,
} from "../constants/constants.ts";
import { FlyToProps, SidebarProps } from "../types";
import { setModalState } from "../store/modalSlice";
import { useAppDispatch, useAppSelector, RootState } from "../store/root";
import { ProfileFilterState, removeFilter } from "../store/searchFiltersSlice";
import { FRENCH_DEPARTMENTS } from "../constants/departments.ts";
import { useFileDownload } from "../hooks/downloadHook";

export function Sidebar({ mapRef }: SidebarProps) {
  const dispatch = useAppDispatch();
  const { downloadWithPost, isDownloading, downloadError } = useFileDownload();
  const { downloadUrl } = useAppSelector((state: RootState) => state.mapData);

  const handleExport = async () => {
    await downloadWithPost(downloadUrl);
  };

  return (
    <div className="map__sidebar">
      <div>
        <FlyTo
          mapRef={mapRef}
          lat={46.2321}
          long={2.209667}
          zoom={5}
          label="Métropole"
        />
        <FlyTo
          mapRef={mapRef}
          lat={14.63554}
          long={-61.02281}
          label="Martinique"
        />
        <FlyTo
          mapRef={mapRef}
          lat={16.1922}
          long={-61.272382}
          label="Guadeloupe"
        />
        <FlyTo mapRef={mapRef} lat={-21.114} long={55.532} label="La Réunion" />
        <FlyTo
          mapRef={mapRef}
          lat={3.9517949}
          long={-53.07822}
          label="Guyane"
          zoom={7}
        />
        <FlyTo
          mapRef={mapRef}
          lat={-12.82451}
          long={45.165455}
          label="Mayotte"
          zoom={7}
        />
      </div>
      <p className="fr-text--lg fr-text--bold">Je cherche des établissements</p>
      <button
        className="fr-btn fr-btn--secondary fr-icon-equalizer-line fr-btn--icon-right"
        onClick={() => dispatch(setModalState(true))}
      >
        Paramétrer les filtres
      </button>

      <FilterDigest />

      <button
        className="fr-btn fr-btn--primary fr-icon-download-fill fr-btn--icon-right fr-mt-1w"
        disabled={downloadUrl === ""}
        title={
          downloadUrl
            ? "Exporter"
            : "Le nombre d'établissements est trop important pour exporter"
        }
        onClick={() => handleExport()}
      >
        Exporter
      </button>

      {isDownloading && (
        <p className="fr-mt-1w">
          <span className="fr-icon-refresh-line spinning fr-mx-1w" />
          Préparation du fichier...
        </p>
      )}
      {downloadError && (
        <div className="fr-alert fr-alert--error fr-mt-1w">
          Erreur: {downloadError}
        </div>
      )}
    </div>
  );
}

const FlyTo = ({ mapRef, lat, long, label, zoom = 9 }: FlyToProps) => {
  return (
    <button
      className="fr-btn fr-btn--sm fr-btn--secondary fr-ml-1v fr-mb-1v"
      onClick={() => mapRef.current.flyTo({ center: [long, lat], zoom })}
    >
      {label}
    </button>
  );
};
const profileFilterToTag = (profileFilters: ProfileFilterState) => {
  const result: { value: string; key: string }[] = [];

  Object.keys(profileFilters).forEach((key) => {
    profileFilters[key].forEach((value) => {
      result.push({ value, key });
    });
  });
  return result;
};
const FilterDigest = () => {
  const dispatch = useAppDispatch();

  const {
    bsdTypeFilters,
    roleFilters,
    profileFilters,
    operationCodeFilters,
    departmentFilters,
    wasteCodesFilter,
  } = useAppSelector((state: RootState) => state.searchFilters);

  const { totalCount } = useAppSelector((state: RootState) => state.mapData);

  const bsdTypeFilter = bsdTypeFilters.root.length
    ? bsdTypeFilters.root[0]
    : "Tous";

  const profiles = profileFilterToTag(profileFilters);

  return (
    <div>
      {(!!roleFilters.root.length ||
        (!!bsdTypeFilter && bsdTypeFilter !== "Tous")) && (
        <>
          <div className="fr-mb-0 fr-mt-2w">
            Mentionné par déchets et rôles&nbsp;:
          </div>

          {roleFilters.root.length ? (
            roleFilters.root.map((role: string) => (
              <button
                className="fr-tag fr-tag--sm fr-tag--dismiss fr-mr-1v"
                key={`${bsdTypeFilter}-${role}`}
                onClick={() =>
                  dispatch(
                    removeFilter({
                      filterKey: "roleFilters",
                      value: role,
                    }),
                  )
                }
              >
                {
                  VERBOSE_BSD_TYPES[
                    bsdTypeFilter as keyof typeof VERBOSE_BSD_TYPES
                  ]
                }
                / {VERBOSE_ROLES[role as keyof typeof VERBOSE_ROLES]}
              </button>
            ))
          ) : (
            <button
              className="fr-tag fr-tag--sm fr-tag--dismiss fr-mr-1v"
              onClick={() =>
                dispatch(
                  removeFilter({
                    filterKey: "bsdTypeFilters",
                    value: bsdTypeFilter,
                  }),
                )
              }
            >
              {
                VERBOSE_BSD_TYPES[
                  bsdTypeFilter as keyof typeof VERBOSE_BSD_TYPES
                ]
              }
            </button>
          )}
        </>
      )}
      {!!operationCodeFilters.root.length && (
        <>
          <p className="fr-mb-0 fr-mt-2w">
            ET les traitements réalisés en tant que destinataire&nbsp;:
          </p>

          {operationCodeFilters.root.map((code) => (
            <button
              className="fr-tag fr-tag--sm fr-tag--dismiss fr-mr-1v"
              key={code}
              onClick={() =>
                dispatch(
                  removeFilter({
                    filterKey: "operationCodeFilters",
                    value: code,
                  }),
                )
              }
            >
              {code}
            </button>
          ))}
        </>
      )}

      {!!profiles.length && (
        <>
          <p className="fr-mb-0 fr-mt-2w">
            ET les profils déclarés sont&nbsp;:
          </p>
          {profiles.map((profile: Record<string, string>) => (
            <button
              className="fr-tag fr-tag--sm fr-tag--dismiss fr-mr-1v"
              key={`${profile.value}-${profile.key}`}
              onClick={() =>
                dispatch(
                  removeFilter({
                    filterKey: "profileFilters",
                    subFilterKey: profile.key,
                    value: profile.value,
                  }),
                )
              }
            >
              {PROFILE_MAPPING[profile.value]}
            </button>
          ))}
        </>
      )}
      {!!wasteCodesFilter.root.length && (
        <>
          <p className="fr-mb-0 fr-mt-2w">Codes déchet&nbsp;:</p>
          {wasteCodesFilter.root.map((wc) => (
            <button
              className="fr-tag fr-tag--sm fr-tag--dismiss "
              key={wc}
              onClick={() =>
                dispatch(
                  removeFilter({
                    filterKey: "wasteCodesFilter",
                    value: wc,
                  }),
                )
              }
            >
              {wc}
            </button>
          ))}
        </>
      )}

      {!!departmentFilters.root.length && (
        <>
          <p className="fr-mb-0 fr-mt-2w">ET dans les départements&nbsp;:</p>
          {departmentFilters.root.map((dept) => (
            <button
              className="fr-tag fr-tag--sm fr-tag--dismiss fr-mr-1v"
              key={dept}
              onClick={() =>
                dispatch(
                  removeFilter({
                    filterKey: "departmentFilters",
                    value: dept,
                  }),
                )
              }
            >
              {FRENCH_DEPARTMENTS[dept]}
            </button>
          ))}
        </>
      )}

      {!!totalCount && (
        <p className="fr-text--bold fr-text--lg fr-mt-1w">
          {new Intl.NumberFormat().format(totalCount)} établissements
          correspondent à vos filtres
        </p>
      )}
    </div>
  );
};
