import React, { ReactNode } from "react";

import { RootState, useAppDispatch, useAppSelector } from "../store/root";
import { setStatsOpened } from "../store/uiSlice";
import { formatInt, formatFloat, formatPercentage } from "./formatUtils.ts";

interface StatsContainerProps {
  children: ReactNode;
}

const Address =
  () =>
  ({ selectedCompany }) => {
    if (!selectedCompany) {
      return null;
    }
    return (
      <div className="grouped-info">
        <p> {selectedCompany?.adresse1}</p>
        <p> {selectedCompany?.adresse2}</p>
        <p>
          {selectedCompany?.code_postal} {selectedCompany?.commune}
        </p>
      </div>
    );
  };

const Info = ({ selectedDepartement, selectedRegion, selectedCompany }) => {
  let nombre_installations = null;
  let quantite_autorisee = null;
  let cumul_quantite_traitee = null;
  let taux_consommation = null;
  if (selectedDepartement) {
    nombre_installations = selectedDepartement?.nombre_installations;
    quantite_autorisee = selectedDepartement?.quantite_autorisee;
    cumul_quantite_traitee = selectedDepartement?.cumul_quantite_traitee;
    taux_consommation = selectedDepartement?.taux_consommation;
  }
  if (selectedRegion) {
    nombre_installations = selectedRegion?.nombre_installations;
    quantite_autorisee = selectedRegion?.quantite_autorisee;
    cumul_quantite_traitee = selectedRegion?.cumul_quantite_traitee;
    taux_consommation = selectedRegion?.taux_consommation;
  }
  if (selectedCompany) {
    quantite_autorisee = selectedCompany?.quantite_autorisee;
    cumul_quantite_traitee = selectedCompany?.cumul_quantite_traitee;
    taux_consommation = selectedCompany?.taux_consommation;
  }
  return (
    <>
      <Address selectedCompany={selectedCompany} />

      <div className="grouped-info">
        {nombre_installations && (
          <p>Nombre d'installations : {nombre_installations}</p>
        )}
      </div>

      <div className="grouped-info">
        <p>
          Quantité autorisée :{" "}
          <span>
            {quantite_autorisee ? formatInt(quantite_autorisee) : "N/A"} t/an
          </span>
        </p>
        <p>
          Quantité traitée en cumulé :{" "}
          <span>
            {cumul_quantite_traitee
              ? formatFloat(cumul_quantite_traitee)
              : "N/A"}{" "}
            t/an
          </span>
        </p>{" "}
        <p>
          Quantité consommée sur l'année :{" "}
          <span>
            {taux_consommation ? formatPercentage(taux_consommation) : " N/A"}
          </span>
        </p>
      </div>
    </>
  );
};

export const StatsContainer: React.FC<StatsContainerProps> = () => {
  const {
    statsOpened,

    selectedCompany,
    selectedRegion,
    selectedDepartement,
    graphUrl,
  } = useAppSelector((state: RootState) => state.ui);
  const dispatch = useAppDispatch();

  if (!statsOpened) {
    return null;
  }

  return (
    <div className="icpe-stats-container">
      <div className="icpe-stats-container-header">
        <button
          className="fr-btn fr-btn--tertiary-no-outline fr-btn--icon-right fr-icon-close-line"
          title="Fermer"
          id="close-stats"
          onClick={() => dispatch(setStatsOpened(false))}
        >
          Fermer
        </button>
      </div>
      <div id="region-stats-container">
        <div id="region-title">
          <h5>
            {selectedCompany?.raison_sociale}
            {selectedRegion?.nom_region}
            {selectedDepartement?.nom_departement}
          </h5>
        </div>

        <Info
          selectedDepartement={selectedDepartement}
          selectedRegion={selectedRegion}
          selectedCompany={selectedCompany}
        />
        {/*<div id="region-info">*/}
        {/*  {selectedDepartement && (*/}
        {/*    <>*/}
        {/*      <div className="grouped-info">*/}
        {/*        <p>*/}
        {/*          Nombre d'installations :{" "}*/}
        {/*          {selectedDepartement?.nombre_installations}*/}
        {/*        </p>*/}
        {/*      </div>*/}

        {/*      <div className="grouped-info">*/}
        {/*        <p>*/}
        {/*          Quantité autorisée :{" "}*/}
        {/*          <span>*/}
        {/*            {formatInt(selectedDepartement?.quantite_autorisee)} t/an*/}
        {/*          </span>*/}
        {/*        </p>*/}
        {/*        <p>*/}
        {/*          Quantité traitée en cumulé :{" "}*/}
        {/*          <span>*/}
        {/*            {formatFloat(selectedDepartement?.cumul_quantite_traitee)}{" "}*/}
        {/*            t/an*/}
        {/*          </span>*/}
        {/*        </p>{" "}*/}
        {/*        <p>*/}
        {/*          Quantité consommée sur l'année :{" "}*/}
        {/*          <span>*/}
        {/*            {formatPercentage(selectedDepartement?.taux_consommation)}*/}
        {/*          </span>*/}
        {/*        </p>*/}
        {/*      </div>*/}
        {/*    </>*/}
        {/*  )}*/}
        {/*  {selectedRegion && (*/}
        {/*    <>*/}
        {/*      <div className="grouped-info">*/}
        {/*        <p>*/}
        {/*          Nombre d'installations :{" "}*/}
        {/*          {selectedRegion?.nombre_installations}*/}
        {/*        </p>*/}
        {/*      </div>*/}

        {/*      <div className="grouped-info">*/}
        {/*        <p>Quantité autorisée : {selectedRegion?.quantite_autorisee}</p>*/}
        {/*        <p>*/}
        {/*          Quantité traitée en cumulé :{" "}*/}
        {/*          {selectedRegion?.cumul_quantite_traitee}*/}
        {/*        </p>{" "}*/}
        {/*        <p>*/}
        {/*          Quantité consommée sur l'année :{" "}*/}
        {/*          {selectedRegion?.taux_consommation}*/}
        {/*        </p>*/}
        {/*      </div>*/}
        {/*    </>*/}
        {/*  )}*/}
        {/*  {selectedCompany && (*/}
        {/*    <>*/}
        {/*      <div className="grouped-info">*/}
        {/*        <p> {selectedCompany?.adresse1}</p>*/}
        {/*        <p> {selectedCompany?.adresse2}</p>*/}
        {/*        <p>*/}
        {/*          {selectedCompany?.code_postal} {selectedCompany?.commune}*/}
        {/*        </p>*/}
        {/*      </div>*/}

        {/*      <div className="grouped-info">*/}
        {/*        <p>Code AIOT: {selectedCompany?.code_aiot}</p>*/}
        {/*        <p>SIRET: {selectedCompany?.siret}</p>*/}
        {/*      </div>*/}

        {/*      <div className="grouped-info">*/}
        {/*        <p>*/}
        {/*          Quantité autorisée :{" "}*/}
        {/*          <span>*/}
        {/*            {selectedCompany?.quantite_autorisee &&*/}
        {/*              formatInt(selectedCompany?.quantite_autorisee)}{" "}*/}
        {/*            {selectedCompany?.unite}*/}
        {/*          </span>*/}
        {/*        </p>*/}
        {/*        <p>*/}
        {/*          Quantité traitée en cumulé :{" "}*/}
        {/*          <span>*/}
        {/*            {selectedCompany?.cumul_quantite_traitee &&*/}
        {/*              formatFloat(selectedCompany?.cumul_quantite_traitee)}{" "}*/}
        {/*            {selectedCompany?.unite}*/}
        {/*          </span>*/}
        {/*        </p>*/}
        {/*        <p>*/}
        {/*          Quantité consommée sur l'année :{" "}*/}
        {/*          <span>*/}
        {/*            {selectedCompany?.taux_consommation &&*/}
        {/*              formatPercentage(selectedCompany?.taux_consommation)}*/}
        {/*          </span>*/}
        {/*        </p>*/}
        {/*      </div>*/}
        {/*    </>*/}
        {/*  )}*/}
        {/*</div>*/}

        {graphUrl && (
          <div className="icpe-graph">
            <iframe
              src={graphUrl}
              style={{ height: "500px", width: "700px" }}
              frameborder="0"
            ></iframe>
          </div>
        )}
      </div>
    </div>
  );
};
