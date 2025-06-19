interface LocaleConfig {
  decimal: string;
  thousands: string;
  grouping: number[];
  currency: [string, string];
}

class NumberFormatter {
  private config: LocaleConfig;

  constructor(config: LocaleConfig) {
    this.config = config;
  }

  private addThousandsSeparator(numStr: string): string {
    const parts = numStr.split(this.config.decimal);
    const integerPart = parts[0];
    const decimalPart = parts[1] || "";

    // Add thousands separator every 3 digits from right to left
    const formatted = integerPart.replace(
      /\B(?=(\d{3})+(?!\d))/g,
      this.config.thousands,
    );

    return decimalPart
      ? `${formatted}${this.config.decimal}${decimalPart}`
      : formatted;
  }

  // Mimics d3's ",.2s" format (SI notation with 2 significant digits)
  formatInt(num: number): string {
    const abs = Math.abs(num);
    const sign = num < 0 ? "-" : "";

    const siUnits = [
      { value: 1e12, symbol: "T" },
      { value: 1e9, symbol: "G" },
      { value: 1e6, symbol: "M" },
      { value: 1e3, symbol: "k" },
      { value: 1, symbol: "" },
    ];

    for (const unit of siUnits) {
      if (abs >= unit.value) {
        const scaledValue = abs / unit.value;
        const rounded = Number(scaledValue.toPrecision(2));
        const formatted = this.addThousandsSeparator(rounded.toString());
        return `${sign}${formatted} ${unit.symbol}`;
      }
    }

    return `${sign}0`;
  }

  // Mimics d3's ",.2f" format (2 decimal places with thousands separator)
  formatFloat(num: number): string {
    const formatted = num.toFixed(2);
    return this.addThousandsSeparator(formatted);
  }

  // Mimics d3's ",.2%" format (percentage with 2 decimal places)
  formatPercentage(num: number): string {
    const percentage = (num * 100).toFixed(2);
    return `${this.addThousandsSeparator(percentage)} %`;
  }
}

// Create the locale configuration
const locale = new NumberFormatter({
  decimal: ".",
  thousands: " ",
  grouping: [3],
  currency: ["", "€"],
});

// Create the formatters (equivalent to d3's formatters)
const formatInt = (num: number) => locale.formatInt(num);
const formatFloat = (num: number) => locale.formatFloat(num);
const formatPercentage = (num: number) => locale.formatPercentage(num);

// Export for use in other modules
export { NumberFormatter, formatInt, formatFloat, formatPercentage };
