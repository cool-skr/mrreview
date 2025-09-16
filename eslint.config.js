// eslint.config.js

// This imports the recommended ruleset from the official ESLint plugin for JavaScript.
import js from "@eslint/js";
import globals from "globals";

export default [
  // This line applies all the rules from the "eslint:recommended" set.
  js.configs.recommended,

  {
    // This section applies these settings to all files.
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        // Defines global variables available in different environments.
        ...globals.browser,
        ...globals.node
      }
    }
  }
];