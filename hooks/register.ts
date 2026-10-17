import type { On } from "claude-code";

import { registerRecycle } from "./recycle";

export function register(on: On) {
  registerRecycle(on);
}
