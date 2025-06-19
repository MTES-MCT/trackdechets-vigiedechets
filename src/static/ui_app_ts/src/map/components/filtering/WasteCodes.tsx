import React, { useState, useEffect, ReactNode, ChangeEvent } from "react";
import { useSelector } from "react-redux";
import { addFilter, removeFilter } from "../../store/searchFiltersSlice";

import { WASTES_TREE } from "../../constants/wasteCodes";
import { RootState, useAppDispatch } from "../../store/root";

interface WasteItem {
  code: string;
  description: string;
  children: readonly WasteItem[];
}

interface WasteTreeProps {
  wasteCodes: readonly WasteItem[];
}

interface WasteNodeProps {
  item: WasteItem;
  level: number;
  selectedItems: string[];
  searchTerm: string;
  matchesSearch: boolean;
}

/**
 * Normalize code by removing spaces for comparison

 */
const normalizeCode = (code: string): string => code.replace(/\s+/g, "");

/**
 * Check if an item or any of its descendants match the search term

 */
const hasMatchingDescendant = (item: WasteItem, term: string): boolean => {
  if (!term) return true;

  // Check for normal text matches
  const descriptionMatch: boolean = item.description
    .toLowerCase()
    .includes(term);

  // Check for code matches, both with spaces and without
  const normalizedItemCode: string = normalizeCode(item.code.toLowerCase());
  const normalizedSearchTerm: string = normalizeCode(term.toLowerCase());
  const codeMatch: boolean =
    item.code.toLowerCase().includes(term) ||
    normalizedItemCode.includes(normalizedSearchTerm);

  const directMatch: boolean = descriptionMatch || codeMatch;

  if (directMatch) return true;

  if (!item.children || item.children.length === 0) return false;

  return item.children.some((child: WasteItem) =>
    hasMatchingDescendant(child, term),
  );
};

const WasteNode: React.FC<WasteNodeProps> = ({
  item,
  level,
  selectedItems,
  searchTerm,
}): React.ReactElement | null => {
  const hasChildren: boolean = item.children && item.children.length > 0;
  const isLeaf: boolean = !hasChildren;

  const lowerSearchTerm: string = searchTerm.toLowerCase();

  // Check if this item matches the search
  const itemMatchesSearch: boolean = searchTerm // Check for normal text matches
    ? item.description.toLowerCase().includes(lowerSearchTerm) || // Check for code matches, both with spaces and without
      item.code.toLowerCase().includes(lowerSearchTerm) ||
      normalizeCode(item.code.toLowerCase()).includes(
        normalizeCode(lowerSearchTerm),
      )
    : false;

  // Additional check for leaf nodes during search
  const shouldDisplayInSearch: boolean =
    !searchTerm ||
    itemMatchesSearch ||
    hasMatchingDescendant(item, lowerSearchTerm);

  const dispatch = useAppDispatch();
  const expanded: boolean = true;

  const selectWasteCodesFilters = useSelector(
    (state: RootState) => state.searchFilters.wasteCodesFilter,
  );

  const selected: boolean = selectWasteCodesFilters.root.includes(item.code);

  const handleSelect = (code: string): void => {
    if (selected) {
      dispatch(
        removeFilter({
          filterKey: "wasteCodesFilter",
          value: code,
        }),
      );
    } else {
      dispatch(
        addFilter({
          filterKey: "wasteCodesFilter",
          value: code,
        }),
      );
    }
  };

  if (searchTerm && !shouldDisplayInSearch) {
    return null;
  }

  const highlightMatch = (text: string): ReactNode => {
    if (!searchTerm) return text;

    // For codes, we need special handling to match normalized versions too
    if (text === item.code) {
      // If this is a direct match with the original search term
      if (text.toLowerCase().includes(searchTerm.toLowerCase())) {
        const parts: string[] = text.split(new RegExp(`(${searchTerm})`, "gi"));
        return parts.map((part: string, i: number) =>
          part.toLowerCase() === searchTerm.toLowerCase() ? (
            <span key={i} className="search-highlight">
              {part}
            </span>
          ) : (
            part
          ),
        );
      } else if (
        normalizeCode(text.toLowerCase()).includes(
          normalizeCode(searchTerm.toLowerCase()),
        )
      ) {
        return <span className="search-highlight">{text}</span>;
      }
      return text;
    }

    const parts: string[] = text.split(new RegExp(`(${searchTerm})`, "gi"));
    return parts.map((part: string, i: number) =>
      part.toLowerCase() === searchTerm.toLowerCase() ? (
        <span key={i} className="search-highlight">
          {part}
        </span>
      ) : (
        part
      ),
    );
  };

  const idCode: string = `id_code_${item.code.replace(/\s+/g, "_")}`;

  return (
    <div
      className={`${isLeaf ? "flex" : ""} ${level > 0 ? "fr-ml-2w" : ""} ${itemMatchesSearch ? "fr-highlight-bg" : ""}`}
      style={{ marginLeft: `${level * 16}px` }}
    >
      {isLeaf && (
        <input
          type="checkbox"
          checked={selected}
          id={idCode}
          onChange={() => handleSelect(item.code)}
          className="fr-mr-2w"
        />
      )}

      <div className={`${!isLeaf ? "fr-mt-1w" : ""}`}>
        <label htmlFor={idCode}>
          <span className={`fr-mr-1w ${hasChildren ? "fr-text--bold" : ""}`}>
            {searchTerm ? highlightMatch(item.code) : item.code}
          </span>
          <span className={`${hasChildren ? "fr-text--bold" : ""}`}>
            {searchTerm ? highlightMatch(item.description) : item.description}
          </span>
        </label>
      </div>

      {expanded && hasChildren && (
        <div className="fr-ml-3w">
          {item.children.map((child: WasteItem) => (
            <WasteNode
              key={child.code}
              item={child}
              level={level + 1}
              selectedItems={selectedItems}
              searchTerm={searchTerm}
              matchesSearch={itemMatchesSearch}
            />
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * A component that renders the complete waste tree with search functionality
 */
const WasteTree: React.FC<WasteTreeProps> = ({
  wasteCodes,
}: WasteTreeProps): React.ReactElement => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [searchResults, setSearchResults] = useState<number>(0);

  const selectWasteCodesFilters = useSelector(
    (state: RootState) => state.searchFilters.wasteCodesFilter,
  );
  const selectedItems: string[] = selectWasteCodesFilters.root;

  // Count search matches when search term changes
  useEffect(() => {
    if (!searchTerm) {
      setSearchResults(0);
      return;
    }

    /**
     * Count the number of items that match the search term
     * @param items - The waste items to search through
     * @returns The number of matching items
     */
    const countMatches = (items: readonly WasteItem[]): number => {
      let count: number = 0;
      const term: string = searchTerm.toLowerCase();
      const normalizedTerm: string = normalizeCode(term);

      /**
       * Process a single item to check for matches
       * @param item - The waste item to check
       */
      const processItem = (item: WasteItem): void => {
        const codeMatch: boolean =
          item.code.toLowerCase().includes(term) ||
          normalizeCode(item.code.toLowerCase()).includes(normalizedTerm);

        const descriptionMatch: boolean = item.description
          .toLowerCase()
          .includes(term);

        if (codeMatch || descriptionMatch) {
          count++;
        }

        if (item.children && item.children.length > 0) {
          item.children.forEach(processItem);
        }
      };

      items.forEach(processItem);
      return count;
    };

    setSearchResults(countMatches(wasteCodes));
  }, [searchTerm, wasteCodes]);

  /**
   * Handle search input changes
   * @param e - The change event
   */
  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setSearchTerm(e.target.value);
  };

  return (
    <div>
      <div>
        <input
          type="text"
          placeholder="Recherche par code ou description..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="fr-input"
          aria-label="Rechercher des codes déchets"
        />
        {searchTerm && (
          <div className="fr-mt-1w fr-text--sm fr-text--muted">
            {searchResults} résultats trouvés
          </div>
        )}
      </div>

      {!!selectedItems.length && (
        <div className="fr-mt-2w">
          Codes sélectionnés: {selectedItems.join(", ")}
        </div>
      )}

      <div className="fr-mt-3w">
        {wasteCodes.map((item: WasteItem) => (
          <WasteNode
            key={item.code}
            item={item}
            level={0}
            selectedItems={selectedItems}
            searchTerm={searchTerm}
            matchesSearch={false}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * The main component that renders the waste codes tree
 */
const WasteCodes: React.FC = (): React.ReactElement => {
  return <WasteTree wasteCodes={WASTES_TREE} />;
};

export default WasteCodes;
