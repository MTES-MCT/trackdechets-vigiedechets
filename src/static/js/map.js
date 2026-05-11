// Rubriques annuelles et quotidiennes - alignées avec ANNUAL_ICPE_RUBRIQUES et DAILY_ICPE_RUBRIQUES du backend
var annualRubriques = ["2760-1", "2760-2"];
var dailyRubriques = ["2790", "2791","2770", "2771"];

// Fonction pour charger les données GeoJSON
async function loadGeoJSONData(url) {
  return fetch(url).then(function (response) {
    if (!response.ok) {
      throw new Error("Erreur réseau lors du chargement du GeoJSON");
    }
    return response.json();
  });
}

async function loadFeaturesStats(layer, year, rubrique) {
  if (
    featuresStats == {} ||
    featuresStats?.[`${layer}.${year}.${rubrique}`] == undefined
  ) {
    console.log("cache miss features stats");
    response = await fetch(`/map/api/icpe/${layer}/${year}/${rubrique}`);
    data = await response.json();
    featuresStats[`${layer}.${year}.${rubrique}`] = data["data"];
  }
}
async function loadFeaturesGraph(layer, year, rubrique, code) {
  if (featuresStats[`${layer}.${year}.${rubrique}`][code] == undefined) {
    return;
  }

  if (
    featuresStats[`${layer}.${year}.${rubrique}`][code]["graph"] == undefined
  ) {
    console.log("cache miss feature graph");
    response = await fetch(
      `/map/api/icpe/${layer}/${year}/${rubrique}/${code}`,
    );
    data = await response.json();
    featuresStats[`${layer}.${year}.${rubrique}`][code]["graph"] =
      data["graph"];
    featuresStats[`${layer}.${year}.${rubrique}`][code]["graph_cumul"] =
      data["graph_cumul"];
  }
}

async function loadFranceStats(year, rubrique) {
  if (
    featuresStats == {} ||
    featuresStats?.[`france.${year}.${rubrique}`] == undefined
  ) {
    console.log("cache miss features stats");
    response = await fetch(`/map/api/icpe/france/${year}/${rubrique}`);
    data = await response.json();
    featuresStats[`france.${year}.${rubrique}`] = data["data"];
  }
}

// Fonctions pour le zoom
function zoomToPolygon(e) {
  let bounds = e.target.getBounds();
  map.fitBounds(bounds, { paddingTopLeft: [700, 0] });
}

function zoomToPoint(e) {
  let latlng = structuredClone(e.target.getLatLng());
  latlng.lng = latlng.lng - 2;
  map.flyTo(latlng, 8);
}

// D3.js
// Configuration de D3 pour le formatage des nombres
var locale = d3.formatLocale({
  decimal: ".",
  thousands: " ",
  grouping: [3],
  currency: ["", "€"],
});
var formatInt = locale.format(",.2s");
var formatFloat = locale.format(",.2f");
var formatPercentage = locale.format(",.2%");
// Échelle de couleur D3 pour les styles des régions/départements
var colorScale = d3.scaleSequential(d3.interpolateOranges);

// Affiche les informations d'une région/département/installation dans une div
async function showRegionInfo(event, rubrique, featureType) {
  key =
    featureType === "installation"
      ? event.target.options.code
      : event.target.feature.properties.code;
  key = featureType === "region" ? parseInt(key) : key;

  layer = featureType === "installation" ? "installations" : selectedLayer;
  var stats =
    featuresStats[`${layer}.${selectedYear}.${selectedRubrique}`][key];

  var regionInfoDiv = document.getElementById("region-info");
  regionInfoDiv.replaceChildren();

  const regionTitleDiv = document.getElementById("region-title");
  regionTitleDiv.replaceChildren();


  //
  let dailyProcessedQuantityKey = "moyenne_quantite_journaliere_traitee";
  let dailyUnit = "t/j";
  let dailyProcessedQuantityPrefix = "Quantité journalière traitée en moyenne :";
  let annualProcessedQuantityKey = "cumul_quantite_traitee";
  let annualUnit = "t/an";
  let annualProcessedQuantityPrefix = "Quantité traitée en cumulé :";

  let dailyUsedQuantityPrefix = "Quantité journalière consommée en moyenne :";
  let annualUsedQuantityPrefix = "Quantité consommée sur l'année :";

  // Pour les rubriques quotidiennes on affiche le taux de consommation journalière
  let usedQuantityPrefix = dailyUsedQuantityPrefix;
  let authorizedQuantityUnit = dailyUnit;

  // Pour les rubriques annuelles on affiche le taux de consommation sur l'année
  if (annualRubriques.includes(rubrique)) {
      usedQuantityPrefix = annualUsedQuantityPrefix
      authorizedQuantityUnit = annualUnit
  }
  //

  if (featureType == "installation") {
    e = document.createElement("h5");
    e.textContent = stats.raison_sociale;
    regionInfoDiv.append(e);

    const adresseDiv = document.createElement("div");
    adresseDiv.classList.add("grouped-info");

    e = document.createElement("p");
    e.textContent = `${stats.adresse1 ?? ""}`;
    adresseDiv.append(e);
    e = document.createElement("p");
    e.textContent = `${stats.adresse2 ?? ""}`;
    adresseDiv.append(e);
    e = document.createElement("p");
    e.textContent = `${stats.code_postal ?? ""} ${stats.commune ?? ""}`;
    adresseDiv.append(e);

    regionInfoDiv.append(adresseDiv);

    const informationDiv = document.createElement("div");
    informationDiv.classList.add("grouped-info");

    e = document.createElement("p");
    e.textContent = `Code AIOT : ${stats.code_aiot}`;
    informationDiv.append(e);

    e = document.createElement("p");
    e.textContent = `SIRET : ${stats.siret ?? "N/A"}`;
    informationDiv.append(e);

    regionInfoDiv.append(informationDiv);

    const traitementDiv = document.createElement("div");
    traitementDiv.classList.add("grouped-info");

    e = document.createElement("p");
    const authorizedQuantity =
      stats.quantite_autorisee != null
        ? formatInt(stats.quantite_autorisee)
        : "N/A";
    e.textContent = `Quantité autorisée : `;
    const authorizedQuantitySpan = document.createElement("span");
    authorizedQuantitySpan.innerHTML = `${authorizedQuantity} ${authorizedQuantityUnit}`;
    e.appendChild(authorizedQuantitySpan);
    traitementDiv.append(e);

    // Daily
    if (dailyRubriques.includes(rubrique)) {
      e = document.createElement("p");
      const dailyProcessedQuantity = stats[dailyProcessedQuantityKey];
      e.textContent = `${dailyProcessedQuantityPrefix} `;
      const dailyProcessedQuantitySpan = document.createElement("span");
      dailyProcessedQuantitySpan.innerHTML = `${formatInt(dailyProcessedQuantity)} ${dailyUnit}`;
      e.appendChild(dailyProcessedQuantitySpan);
      traitementDiv.append(e);
    }


    // Annual
    e = document.createElement("p");
    const annualProcessedQuantity = stats[annualProcessedQuantityKey];
    e.textContent = `${annualProcessedQuantityPrefix} `;
    const annualProcessedQuantitySpan = document.createElement("span");
    annualProcessedQuantitySpan.innerHTML = `${formatInt(annualProcessedQuantity)} ${annualUnit}`;
    e.appendChild(annualProcessedQuantitySpan);
    traitementDiv.append(e);
  

    // Consumption rate
    e = document.createElement("p");
    const usedQuantity =
      stats.taux_consommation != null
        ? formatPercentage(stats.taux_consommation)
        : "N/A";
    e.textContent = `${usedQuantityPrefix} `;
    const usedQuantitySpan = document.createElement("span");
    usedQuantitySpan.innerHTML = `${usedQuantity}`;
    e.appendChild(usedQuantitySpan);
    traitementDiv.append(e);

    regionInfoDiv.append(traitementDiv);
  } else {
    e = document.createElement("h5");
    e.textContent = event.target.feature.properties.nom;
    regionInfoDiv.append(e);

    if (stats) {
      e = document.createElement("p");
      e.textContent = `Nombre d'installations : ${stats.nombre_installations}`;
      regionInfoDiv.append(e);

      const traitementDiv = document.createElement("div");
      traitementDiv.classList.add("grouped-info");

      e = document.createElement("p");
      const authorizedQuantity =
        stats.quantite_autorisee != null
          ? formatInt(stats.quantite_autorisee)
          : "N/A";
      e.textContent = `Quantité autorisée : `;
      const authorizedQuantitySpan = document.createElement("span");
      authorizedQuantitySpan.innerHTML = `${authorizedQuantity} ${authorizedQuantityUnit}`;
      e.appendChild(authorizedQuantitySpan);
      traitementDiv.append(e);


      // Daily
      if (dailyRubriques.includes(rubrique)) {
        e = document.createElement("p");
        const dailyProcessedQuantity = stats[dailyProcessedQuantityKey];
        e.textContent = `${dailyProcessedQuantityPrefix} `;
        const dailyProcessedQuantitySpan = document.createElement("span");
        dailyProcessedQuantitySpan.innerHTML = `${formatInt(dailyProcessedQuantity)} ${dailyUnit}`;
        e.appendChild(dailyProcessedQuantitySpan);
        traitementDiv.append(e);
      }


      // Annual
      e = document.createElement("p");
      const annualProcessedQuantity = stats[annualProcessedQuantityKey];
      e.textContent = `${annualProcessedQuantityPrefix} `;
      const annualProcessedQuantitySpan = document.createElement("span");
      annualProcessedQuantitySpan.innerHTML = `${formatInt(annualProcessedQuantity)} ${annualUnit}`;
      e.appendChild(annualProcessedQuantitySpan);
      traitementDiv.append(e);


      // Consumption rate
      e = document.createElement("p");
      const usedQuantity =
        stats.taux_consommation != null
          ? formatPercentage(stats.taux_consommation)
          : "N/A";
      e.textContent = `${usedQuantityPrefix} `;
      const usedQuantitySpan = document.createElement("span");
      usedQuantitySpan.innerHTML = `${usedQuantity}`;
      e.appendChild(usedQuantitySpan);
      traitementDiv.append(e);

      regionInfoDiv.append(traitementDiv);
    } else {
      e = document.createElement("p");
      e.textContent = "Nombre d'installations : N/A";
      regionInfoDiv.append(e);

      e = document.createElement("p");
      e.textContent = "Quantité autorisée : N/A";
      regionInfoDiv.append(e);
    }
  }

  idDivGraph = "region-graph";
  const idDivGraphCumul = "region-graph-cumul";
  Plotly.purge(idDivGraph);
  Plotly.purge(idDivGraphCumul);
  await loadFeaturesGraph(layer, selectedYear, selectedRubrique, key);
  if (stats && stats.graph) {
    e = document.createElement("div");
    e.classList.add("data-title", "fr-pt-2w");

    const dataTitleH6 = document.createElement("h6");
    dataTitleH6.classList.add("fr-m-0");
    dataTitleH6.textContent = "Données";
    e.append(dataTitleH6);

    const dataTitleButton = document.createElement("button");
    dataTitleButton.textContent = document
      .getElementById("stats-container")
      .classList.contains("stats-container--full")
      ? "Réduire"
      : "Afficher";
    dataTitleButton.classList.add(
      "fr-btn",
      "fr-btn--tertiary-no-outline",
      "fr-btn--icon-right",
      document
        .getElementById("stats-container")
        .classList.contains("stats-container--full")
        ? "fr-icon-close-line"
        : "fr-icon-fullscreen-line",
    );
    dataTitleButton.addEventListener("click", function (e) {
      document
        .getElementById("stats-container")
        .classList.toggle("stats-container--full");

      const button = e.target;
      button.classList.toggle("fr-icon-fullscreen-line");
      button.classList.toggle("fr-icon-close-line");

      button.textContent = button.classList.contains("fr-icon-fullscreen-line")
        ? "Afficher"
        : "Réduire";

      // wait for the end of the animation
      setTimeout(() => {
        Plotly.relayout(idDivGraph, { autosize: true });
        if (stats.graph_cumul) {
          Plotly.relayout(idDivGraphCumul, { autosize: true });
        }
      }, "250");
    });
    e.append(dataTitleButton);

    regionTitleDiv.append(e);

    const plotData = stats.graph;

    Plotly.newPlot(idDivGraph, plotData.data, plotData.layout, {
      responsive: true,
      autosize: true,
    });
    Plotly.relayout(idDivGraph, {
      autosize: true,
    });

    if (stats.graph_cumul) {
      const plotDataCumul = stats.graph_cumul;
      Plotly.newPlot(idDivGraphCumul, plotDataCumul.data, plotDataCumul.layout, {
        responsive: true,
        autosize: true,
      });
      Plotly.relayout(idDivGraphCumul, { autosize: true });
    }
  }

  document
    .getElementById("stats-container")
    .classList.remove("stats-container--closed");
}

// Mettre en surbrillance la région ou le département sélectionné
function styleSelected(e) {
  if (currentSelectedLayer) {
    currentSelectedLayer.setStyle({
      color: "#2f3640",
      weight: 1,
    });
  }

  currentSelectedLayer = e.target;

  e.target.setStyle({
    color: "#2c3e50",
    weight: 4,
    opacity: 1,
  });
}

// Gestionnaires d'événements pour interagir avec les polygones et les points
function clickOnPolygonHandler(e, rubrique, featureType) {
  zoomToPolygon(e);
  showRegionInfo(e, rubrique, featureType);
  styleSelected(e);
}

function onEachPolygonFeature(feature, layer, rubrique, featureType) {
  layer.on({
    click: (e) => {
      clickOnPolygonHandler(e, rubrique, featureType);
    },
  });
}

function clickOnPointHandler(e, rubrique) {
  zoomToPoint(e);
  showRegionInfo(e, rubrique, "installation");
}

function onEachPointFeature(feature, layer, rubrique) {
  layer.on({
    click: (e) => {
      clickOnPointHandler(e, rubrique);
    },
  });
}

// Ajoute ou enlève une couche
function setLayer(layerName) {
  if (currentLayer) {
    map.removeLayer(currentLayer);
  }

  if (layerName === "regions") {
    currentLayer = geojsonRegions;
  } else if (layerName === "departements") {
    currentLayer = geojsonDepartements;
  } else {
    currentLayer = null;
  }

  if (currentLayer) {
    map.addLayer(currentLayer);
  }
}

// Ajoute ou enlève la couche contenant les installations
async function loadInstallations(year, rubrique) {
  await loadFeaturesStats("installations", year, rubrique);

  markers = [];
  for (const [key, value] of Object.entries(
    featuresStats[`installations.${selectedYear}.${selectedRubrique}`],
  )) {
    if (value.latitude == null || value.longitude == null) {
      continue;
    }

    marker_options = {
      title: value.raison_sociale,
      code: key,
    };

    // Determine marker color based on the value variable
    let markerColor;
    if (
      value["quantite_autorisee"] == 0 ||
      value["quantite_autorisee"] == null
    ) {
      markerColor = "red";
    } else if (
      (!annualRubriques.includes(selectedRubrique) &&
        (value["moyenne_quantite_journaliere_traitee"] == null ||
          value["moyenne_quantite_journaliere_traitee"] == 0)) ||
      (annualRubriques.includes(selectedRubrique) &&
        (value["cumul_quantite_traitee"] == null ||
          value["cumul_quantite_traitee"] == 0))
    ) {
      markerColor = "yellow";
    } else if (
      value["taux_consommation"] != null &&
      (value["taux_consommation"] <= 0.2 || value["taux_consommation"] >= 1)
    ) {
      markerColor = "dark";
    } else {
      markerColor = "blue";
    }

    marker_options = {
      ...marker_options,
      icon: L.icon({
        iconUrl: `/static/img/${markerColor}_icon.png`,
        iconSize: [30, 30],
        popupAnchor: [1, -34],
      }),
    };

    markers.push(
      L.marker([value.latitude, value.longitude], marker_options)
        .on("click", (e) => {
          clickOnPointHandler(e, selectedRubrique);
        })
        .bindTooltip(`${value.raison_sociale}`),
    );
  }

  installationsLayer = L.layerGroup(markers);
}

// Chargement des géométries départementales et régionales
async function loadRegionalGeojsons() {
  if (!regionsGeojson) {
    await loadGeoJSONData(regionsGeoJSONUrl).then((data) => {
      regionsGeojson = data;
    });
  }

  if (!departementsGeojson) {
    await loadGeoJSONData(departementsGeoJSONUrl).then((data) => {
      departementsGeojson = data;
    });
  }
}

// Affichage des statistiques pour la france entière
async function showFranceStats(rubrique, year) {
  await loadFranceStats(year, rubrique);

  const stats = featuresStats[`france.${selectedYear}.${selectedRubrique}`];

  let dailyProcessedQuantityKey = "moyenne_quantite_journaliere_traitee";
  let dailyUnit = "t/j";
  let dailyProcessedQuantityPrefix = "Quantité journalière traitée en moyenne :";
  let annualProcessedQuantityKey = "cumul_quantite_traitee";
  let annualUnit = "t/an";
  let annualProcessedQuantityPrefix = "Quantité annuelle cumulée :";

  let dailyUsedQuantityPrefix = "Quantité journalière consommée en moyenne :";
  let annualUsedQuantityPrefix = "Quantité consommée sur l'année :";

  // Pour les rubriques quotidiennes on affiche le taux de consommation journalière
  let usedQuantityPrefix = dailyUsedQuantityPrefix;
  let authorizedQuantityUnit = dailyUnit;

  // Pour les rubriques annuelles on affiche le taux de consommation sur l'année
  if (annualRubriques.includes(rubrique)) {
      usedQuantityPrefix = annualUsedQuantityPrefix
      authorizedQuantityUnit = annualUnit
  }


  const franceInfoDiv = document.getElementById("region-info");
  franceInfoDiv.replaceChildren();

  const franceTitleDiv = document.getElementById("region-title");
  franceTitleDiv.replaceChildren();

  e = document.createElement("h5");
  e.textContent = "France";
  franceInfoDiv.append(e);

  e = document.createElement("p");
  e.textContent = `Nombre d'installations : ${stats.nombre_installations}`;
  franceInfoDiv.append(e);

  const traitementDiv = document.createElement("div");
  traitementDiv.classList.add("grouped-info");

  // Add authorized quantity (daily or annual)
  e = document.createElement("p");
  const authorizedQuantity =
    stats.quantite_autorisee != null
      ? formatInt(stats.quantite_autorisee)
      : "N/A";
  e.textContent = `Quantité autorisée : `;
  const authorizedQuantitySpan = document.createElement("span");
  authorizedQuantitySpan.innerHTML = `${authorizedQuantity} ${authorizedQuantityUnit}`;
  e.appendChild(authorizedQuantitySpan);
  traitementDiv.append(e);

  
  // For daily rubriques: add daily processed quantity
  if (dailyRubriques.includes(rubrique)) {
    e = document.createElement("p");
    const dailyProcessedQuantity = stats[dailyProcessedQuantityKey];
    e.textContent = `${dailyProcessedQuantityPrefix} `;
    const dailyProcessedQuantitySpan = document.createElement("span");
    dailyProcessedQuantitySpan.innerHTML = `${formatInt(dailyProcessedQuantity)} ${dailyUnit}`;
    e.appendChild(dailyProcessedQuantitySpan);
    traitementDiv.append(e);
  }

  // For all rubriques: add annual processed quantity
  e = document.createElement("p");
  const annualProcessedQuantity = stats[annualProcessedQuantityKey];
  e.textContent = `${annualProcessedQuantityPrefix} `;
  const annualProcessedQuantitySpan = document.createElement("span");
  annualProcessedQuantitySpan.innerHTML = `${formatInt(annualProcessedQuantity)} ${annualUnit}`;
  e.appendChild(annualProcessedQuantitySpan);
  traitementDiv.append(e);

  // Add consumption rate
  e = document.createElement("p");
  const usedQuantity =
    stats.taux_consommation != null
      ? formatPercentage(stats.taux_consommation)
      : "N/A";
  e.textContent = `${usedQuantityPrefix} `;
  const usedQuantitySpan = document.createElement("span");
  usedQuantitySpan.innerHTML = `${usedQuantity}`;
  e.appendChild(usedQuantitySpan);
  traitementDiv.append(e);

  franceInfoDiv.append(traitementDiv);

  idDivGraph = "region-graph";
  const idDivGraphCumulFrance = "region-graph-cumul";
  Plotly.purge(idDivGraph);
  Plotly.purge(idDivGraphCumulFrance);
  if (stats && stats.graph) {
    e = document.createElement("div");
    e.classList.add("data-title", "fr-pt-2w");

    const dataTitleH6 = document.createElement("h6");
    dataTitleH6.classList.add("fr-m-0");
    dataTitleH6.textContent = "Données";
    e.append(dataTitleH6);

    const dataTitleButton = document.createElement("button");
    dataTitleButton.textContent = document
      .getElementById("stats-container")
      .classList.contains("stats-container--full")
      ? "Réduire"
      : "Afficher";
    dataTitleButton.classList.add(
      "fr-btn",
      "fr-btn--tertiary-no-outline",
      "fr-btn--icon-right",
      document
        .getElementById("stats-container")
        .classList.contains("stats-container--full")
        ? "fr-icon-close-line"
        : "fr-icon-fullscreen-line",
    );
    dataTitleButton.addEventListener("click", function (e) {
      document
        .getElementById("stats-container")
        .classList.toggle("stats-container--full");

      const button = e.target;
      button.classList.toggle("fr-icon-fullscreen-line");
      button.classList.toggle("fr-icon-close-line");

      button.textContent = button.classList.contains("fr-icon-fullscreen-line")
        ? "Afficher"
        : "Réduire";

      // wait for the end of the animation
      setTimeout(() => {
        Plotly.relayout(idDivGraph, { autosize: true });
        if (stats.graph_cumul) {
          Plotly.relayout(idDivGraphCumulFrance, { autosize: true });
        }
      }, "250");
    });
    e.append(dataTitleButton);

    franceTitleDiv.append(e);

    const plotData = stats.graph;

    Plotly.newPlot(idDivGraph, plotData.data, plotData.layout, {
      responsive: true,
      autosize: true,
    });
    Plotly.relayout(idDivGraph, {
      autosize: true,
    });

    if (stats.graph_cumul) {
      const plotDataCumulFrance = stats.graph_cumul;
      Plotly.newPlot(idDivGraphCumulFrance, plotDataCumulFrance.data, plotDataCumulFrance.layout, {
        responsive: true,
        autosize: true,
      });
      Plotly.relayout(idDivGraphCumulFrance, { autosize: true });
    }
  }

  document
    .getElementById("stats-container")
    .classList.remove("stats-container--closed");
}

// Crée et configure les couches GeoJSON en fonction des données sélectionnées
async function prepareMap(layerName, rubrique, year) {
  // Si les couches existent déjà sur la carte, il faut les retirer
  if (regionsLayer) map.removeLayer(regionsLayer);
  if (departementsLayer) map.removeLayer(departementsLayer);
  if (installationsLayer) map.removeLayer(installationsLayer);

  await loadRegionalGeojsons();

  await loadFeaturesStats(layerName, year, rubrique);
  if (layerName == "regions") {
    regionsLayer = L.geoJSON(regionsGeojson, {
      style: stylePolygon,
      onEachFeature: (feature, layer) => {
        onEachPolygonFeature(feature, layer, rubrique, "regions");
        layer.bindTooltip(`${feature.properties.nom}`);
      },
    });
    map.addLayer(regionsLayer);
  }

  if (layerName == "departements") {
    departementsLayer = L.geoJSON(departementsGeojson, {
      style: stylePolygon,
      onEachFeature: (feature, layer) => {
        onEachPolygonFeature(feature, layer, rubrique, "departements");
        layer.bindTooltip(`${feature.properties.nom}`);
      },
    });
    map.addLayer(departementsLayer);
  }

  await loadInstallations(year, rubrique);

  if (installationsToggled) {
    map.addLayer(installationsLayer);
  }
}

// Gestion du toggle du side panel
document.getElementById("toggle-side").addEventListener("click", function (e) {
  e.target.classList.toggle("fr-icon-arrow-left-s-line-double");
  e.target.classList.toggle("fr-icon-arrow-right-s-line-double");

  document
    .getElementById("side-container")
    .classList.toggle("side-container--closed");
  setTimeout(function () {
    map.invalidateSize();
  }, 400);
});

// Gestion du toggle du panneau de stats
document.getElementById("close-stats").addEventListener("click", function (e) {
  document
    .getElementById("stats-container")
    .classList.add("stats-container--closed");
});

// Gestionnaire d'événements pour le sélecteur de couche
document
  .getElementById("layer-select")
  .addEventListener("change", function (e) {
    selectedLayer = e.target.value;
    prepareMap(selectedLayer, selectedRubrique, selectedYear);
  });

// Gestionnaire d'événements pour le sélecteur d'année'e
document.getElementById("year-select").addEventListener("change", function (e) {
  selectedYear = e.target.value;
  prepareMap(selectedLayer, selectedRubrique, selectedYear);
  showFranceStats(selectedRubrique, selectedYear);
});

// Gestionnaire d'événements pour le sélecteur de rubrique
document
  .getElementById("rubrique-select")
  .addEventListener("change", function (e) {
    selectedRubrique = e.target.value;

    if (!annualRubriques.includes(selectedRubrique)) {
      var legend_div = document.getElementById("icon-legend");
      legend_div.display = "block";
    }
    prepareMap(selectedLayer, selectedRubrique, selectedYear);
    showFranceStats(selectedRubrique, selectedYear);
  });

// Gestionnaire d'événements pour le sélecteur de zoom
document.getElementById("zoom-select").addEventListener("change", function (e) {
  const selectedZoom = e.target.value;
  switch (selectedZoom) {
    case "metropole":
      map.flyTo([46.2276, 2.2137], 5);
      break;
    case "mgg":
      map.flyTo([12, -56], 5.5);
      break;
    case "mr":
      map.flyTo([-17, 50], 6);
      break;
  }
});

// Gestionnaire d'événements pour le bouton toggle des installations
document
  .getElementById("toggle-installations")
  .addEventListener("change", function (e) {
    installationsToggled = e.target.checked;

    if (installationsToggled) {
      map.addLayer(installationsLayer);
    } else {
      map.removeLayer(installationsLayer);
    }
  });

// Gestionnaires d'événements pour revenir aux stats France
document
  .getElementById("back-to-france")
  .addEventListener("click", function (e) {
    if (currentSelectedLayer) {
      currentSelectedLayer.setStyle({
        color: "#2f3640",
        weight: 1,
      });
    }
    showFranceStats(selectedRubrique, selectedYear);
  });

// Styles pour les régions/départements
function stylePolygon(feature) {
  // Extract the relevant properties
  featureId = feature.properties.code;
  featureStats =
    featuresStats[`${selectedLayer}.${selectedYear}.${selectedRubrique}`][
      featureId
    ];

  var processedQuantityKey = "moyenne_quantite_journaliere_traitee";
  if (annualRubriques.includes(selectedRubrique)) {
    processedQuantityKey = "cumul_quantite_traitee";
  }
  var processedQuantity = featureStats
    ? featureStats[processedQuantityKey]
    : null;

  var ratio = featureStats ? featureStats.taux_consommation : null;

  var fillColor;
  var fillOpacity;

  if (ratio == null && processedQuantity == null) {
    // Case when there is no data
    fillColor = "#2f3640";
    fillOpacity = 0.6;
  } else if ((ratio == null && processedQuantity > 0) || ratio > 1) {
    // Case when quantity processed is above authorization (also handles null authorization)
    fillColor = "url(#stripes)";
    fillOpacity = 1;
  } else {
    // Nominal case
    fillColor = colorScale(ratio);
    fillOpacity = 0.6;
  }

  return {
    fillColor: fillColor,
    weight: 1,
    opacity: 0.6,
    color: "#2f3640",
    fillOpacity: 0.6,
  };
}
