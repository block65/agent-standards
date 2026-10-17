import type { On } from "claude-code";
import { registerRecycle } from "./recycle.ts";

export function register(on: On) {
	registerRecycle(on);
}
