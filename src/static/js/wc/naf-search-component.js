let globalSheets = null;

// access global css
export function getGlobalStyleSheets() {
  if (globalSheets === null) {
    globalSheets = Array.from(document.styleSheets).map((x) => {
      const sheet = new CSSStyleSheet();
      const css = Array.from(x.cssRules)
        .map((rule) => rule.cssText)
        .join(" ");
      sheet.replaceSync(css);
      return sheet;
    });
  }

  return globalSheets;
}

export function addGlobalStylesToShadowRoot(shadowRoot) {
  shadowRoot.adoptedStyleSheets.push(...getGlobalStyleSheets());
}

class NAFSearchComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });

    addGlobalStylesToShadowRoot(this.shadowRoot);

    this.selectedCode = null;
    this.searchTimeout = null;

    this.apiBaseUrl = this.getAttribute("api-base-url");
    this.placeholder = this.getAttribute("placeholder") || "Rechercher...";
    this.label = this.getAttribute("label");

    this.render();
    this.bindEvents();
  }

  render() {
    this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: block;
                            font-family: inherit;
                        }
                        
                        .input-wrapper {
                            position: relative;
                            display: flex;
                            align-items: center;
                        }
                        
                        .clear-button {
                            position: absolute;
                            right: 12px;
                            top: 50%;
                            transform: translateY(-50%);
                            background: none;
                            border: none;
                            font-size: 18px;
                            color: #666;
                            cursor: pointer;
                            padding: 4px;
                            border-radius: 50%;
                            display: none;
                            line-height: 1;
                            width: 24px;
                            height: 24px;
                            align-items: center;
                            justify-content: center;
                        }
                        
                        .clear-button:hover {
                            background: #f0f0f0;
                            color: #333;
                        }
                        
                        .clear-button.visible {
                            display: flex;
                        }
                        
                        .search-results {
                            margin-top: 16px;
                        }
                        
                        .naf-item {
                            padding: 12px 16px;
                            margin-bottom: 8px;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            transition: all 0.2s;
                            background: white;
                        }
                        
                        .naf-item.selectable {
                            cursor: pointer;
                        }
                        
                        .naf-item.selectable:hover {
                            background: #f6f6f6;
                            border-color: #000091;
                        }
                        
                        .naf-item.non-selectable {
                            cursor: default;
                            opacity: 0.7;
                            background: #f8f8f8;
                        }
                        
                        .naf-item.selected {
                            background: #e3e3fd;
                            border-color: #000091;
                            color: #000091;
                        }
                        
                        .naf-item.child {
                            margin-left: 32px;
                            border-left: 3px solid #e5e5e5;
                        }
                        
                        .naf-code {
                            font-weight: 600;
                            margin-right: 8px;
                        }
                        
                        .naf-label {
                            color: #333;
                        }
                        
                        .naf-item.selected .naf-label {
                            color: #000091;
                        }
                        
                        .naf-item.non-selectable .naf-label {
                            color: #666;
                        }
                        
                        .loading-spinner {
                            display: inline-block;
                            width: 20px;
                            height: 20px;
                            border: 3px solid #f3f3f3;
                            border-top: 3px solid #000091;
                            border-radius: 50%;
                            animation: spin 1s linear infinite;
                            margin-right: 8px;
                        }
                        
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                        
                        .no-results {
                            color: #666;
                            font-style: italic;
                            padding: 20px;
                            text-align: center;
                        }
                        
                        .error-message {
                            color: #e1000f;
                            background: #ffe8e8;
                            padding: 12px;
                            border-radius: 4px;
                            border-left: 4px solid #e1000f;
                        }
                        
                        .loading-message {
                            padding: 20px;
                            text-align: center;
                            color: #666;
                        }
                    </style>
                    
                    <div  >
                        <div class="fr-input-group">
                            <label class="fr-label" for="naf-search">
                                <span class="label-content">${this.label} :</span>
                            </label>
                            <div class="input-wrapper">
                                <input 
                                    type="text" 
                                    id="naf-search"
                                    class="fr-input"
                                    placeholder="${this.placeholder}"
                                    maxlength="100">
                                <button class="clear-button" id="clear-button" type="button">×</button>
                            </div>
                        </div>
                        
                        <div class="search-results" id="search-results"></div>
                    </div>
                `;
  }

  bindEvents() {
    const nafSearch = this.shadowRoot.getElementById("naf-search");
    const searchResults = this.shadowRoot.getElementById("search-results");
    const clearButton = this.shadowRoot.getElementById("clear-button");

    // Auto-search on input with debouncing
    nafSearch.addEventListener("input", () => {
      this.updateClearButtonVisibility();
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.performSearch();
      }, 500);
    });

    // Search on Enter key
    nafSearch.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.performSearch();
      }
    });

    // Clear button click
    clearButton.addEventListener("click", () => {
      this.clearSelection();
    });

    // Event delegation for item clicks
    searchResults.addEventListener("click", (e) => {
      const nafItem = e.target.closest(".naf-item");
      if (nafItem && nafItem.classList.contains("selectable")) {
        this.handleItemSelection(nafItem);
      }
    });

    // Initial search  e
    if (nafSearch.value.trim()) {
      this.performSearch();
    }

    this.updateClearButtonVisibility();
  }

  updateClearButtonVisibility() {
    const nafSearch = this.shadowRoot.getElementById("naf-search");
    const clearButton = this.shadowRoot.getElementById("clear-button");

    if (nafSearch.value.trim() || this.selectedCode) {
      clearButton.classList.add("visible");
    } else {
      clearButton.classList.remove("visible");
    }
  }

  async performSearch() {
    const nafTerm = this.shadowRoot.getElementById("naf-search").value.trim();
    const searchResults = this.shadowRoot.getElementById("search-results");

    if (!nafTerm) {
      searchResults.innerHTML =
        '<div class="no-results">Saisissez un terme de recherche pour voir les codes NAF disponibles</div>';
      return;
    }

    this.setLoading(true);

    try {
      // api call
      const params = new URLSearchParams();
      params.append("naf", nafTerm);

      const apiUrl = `${this.apiBaseUrl}?${params.toString()}`;

      const response = await this.callAPI(apiUrl);
      this.renderResults(response.data || response);
    } catch (error) {
      searchResults.innerHTML = `
                        <div class="error-message">
                            Erreur lors de la recherche: ${error.message}
                        </div>
                    `;
    } finally {
      this.setLoading(false);
    }
  }

  async callAPI(url) {
    return fetch(url).then((response) => {
      if (!response.ok) throw new Error(`API Error: ${response.status}`);
      return response.json();
    });
  }

  renderResults(results) {
    const searchResults = this.shadowRoot.getElementById("search-results");

    if (!results || results.length === 0) {
      searchResults.innerHTML =
        '<div class="no-results">Aucun résultat trouvé</div>';
      return;
    }

    searchResults.innerHTML = results
      .map((item) => this.renderNAFItem(item, 0))
      .join("");

    this.restoreSelection();
  }

  renderNAFItem(item, level) {
    const isChild = level > 0;
    const childClass = isChild ? "child" : "";
    const isLeaf = !item.children || item.children.length === 0;
    const selectableClass = isLeaf ? "selectable" : "non-selectable";
    const itemId = `naf_${item.code.replace(/\./g, "_")}`;

    let html = `
                    <div class="naf-item ${childClass} ${selectableClass}" 
                         data-code="${item.code}" 
                         data-label="${item.content}" 
                         data-is-leaf="${isLeaf}"
                         id="${itemId}">
                        <span class="naf-code">${item.code}</span>
                        <span class="naf-label">${item.content}</span>
                    </div>
                `;

    if (item.children && item.children.length > 0) {
      const childrenHtml = item.children
        .map((child) => this.renderNAFItem(child, level + 1))
        .join("");
      html += childrenHtml;
    }

    return html;
  }

  restoreSelection() {
    if (this.selectedCode) {
      const selectedItem = this.shadowRoot.querySelector(
        `[data-code="${this.selectedCode.code}"]`,
      );
      if (selectedItem) {
        selectedItem.classList.add("selected");
      }
    }
  }

  handleItemSelection(nafItem) {
    const code = nafItem.dataset.code;
    const label = nafItem.dataset.label;
    const isLeaf = nafItem.dataset.isLeaf === "true";

    // Only allow selection of leaf nodes
    if (!isLeaf) {
      return;
    }

    this.shadowRoot.querySelectorAll(".naf-item.selected").forEach((item) => {
      item.classList.remove("selected");
    });

    nafItem.classList.add("selected");
    this.selectedCode = { code, label };

    const nafSearch = this.shadowRoot.getElementById("naf-search");
    nafSearch.value = `${code} - ${label}`;

    this.updateClearButtonVisibility();

    this.hideDropdown();

    // Dispatch custom evt
    this.dispatchEvent(
      new CustomEvent("selection-changed", {
        bubbles: true,
        cancelable: false,
        composed: true,
        detail: {
          code: code,
        },
      }),
    );
  }

  setLoading(loading) {
    const searchResults = this.shadowRoot.getElementById("search-results");

    if (loading) {
      searchResults.innerHTML =
        '<div class="loading-message"><span class="loading-spinner"></span>Recherche en cours...</div>';
    }
  }

  // showDropdown() {
  //   const searchResults = this.shadowRoot.getElementById("search-results");
  //   searchResults.classList.remove("hidden");
  // }

  hideDropdown() {
    const searchResults = this.shadowRoot.getElementById("search-results");
    searchResults.innerHTML = "";
  }

  // Public API methods
  getSelectedCode() {
    return this.selectedCode ? this.selectedCode.code : null;
  }

  getSelectedCodeWithLabel() {
    return this.selectedCode ? { ...this.selectedCode } : null;
  }

  clearSelection() {
    // Clear visual selection
    this.shadowRoot.querySelectorAll(".naf-item.selected").forEach((item) => {
      item.classList.remove("selected");
    });

    this.selectedCode = null;

    const nafSearch = this.shadowRoot.getElementById("naf-search");
    nafSearch.value = "";

    this.updateClearButtonVisibility();

    this.hideDropdown();

    this.dispatchEvent(
      new CustomEvent("selection-changed", {
        bubbles: true,
        cancelable: false,
        composed: true,
        detail: {
          code: "",
        },
      }),
    );
  }
}

// Register the custom element
customElements.define("naf-search-component", NAFSearchComponent);
