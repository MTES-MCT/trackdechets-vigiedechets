import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { 
    ignores: [
    "dist",                  // Code compilé (illisible)
    ".venv/**",              // Libs Python/Django (évite le crash RAM)
    "node_modules/**",       // Libs JS externes
    "**/static/admin/**",    // Code source admin Django
    "**/static/grappelli/**" // Code source thème Grappelli
  ]
  },

  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["src/static/ui_app_ts/src/**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  },
);