import { fileURLToPath } from "node:url";
import { clarity } from "@block65/shared-config/oxlint";

// Only the rules an eval scores. Everything else stays off, so a finding always
// names a standard under test
export default {
	plugins: ["typescript"],
	categories: { correctness: "off" },
	jsPlugins: [
		...(clarity.jsPlugins ?? []),
		fileURLToPath(new URL("plugin.ts", import.meta.url)),
	],
	rules: {
		"block65/no-sentinel-fallback": "error",
		"block65/no-single-use-function": "error",
		"block65/no-filled-object-literal": "error",
		"eval/upper-snake-mutable": "error",
		"eval/loop-mutation": "error",
		"eval/side-effect-for-loop": "error",
		"eval/inline-object-param": "error",
		"block65/declaration-comments": "error",
		"block65/no-narrative-comment": "error",
		"block65/no-jsdoc-on-statement": "error",
		"typescript/consistent-type-assertions": [
			"error",
			{ assertionStyle: "never" },
		],
		"eval/nullish-default": "warn",
		"eval/nullable-param": "warn",
	},
};
