import { defineConfig } from "@block65/shared-config/oxlint";

export default defineConfig({
	// Eval fixtures hold banned patterns on purpose
	ignorePatterns: ["evals/fixture/**", "evals/tasks/**"],
});
