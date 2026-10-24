import type { On } from "claude-code";
import { registerCompactLast } from "./compact-last.ts";

export function register(on: On) {
	registerCompactLast(on);
}
