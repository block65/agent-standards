import { describe, it } from "node:test";
import { RuleTester } from "oxlint/plugins-dev";
import plugin from "./plugin.ts";

RuleTester.describe = describe;
RuleTester.it = it;

const tester = new RuleTester({
	languageOptions: { parserOptions: { lang: "ts" } },
});

tester.run("upper-snake-mutable", plugin.rules["upper-snake-mutable"], {
	valid: [
		"const MAX_SIZE = 10;",
		"const LABEL = `x`;",
		"const KINDS = ['a', 'b'] as const;",
		"const FROZEN_MAP = Object.freeze({ a: 1 });",
		"const allowed = new Set(['a']);",
		"const KINDS = ['a'] as const satisfies readonly string[];",
		"const STATUS = 'open' satisfies string;",
	],
	invalid: [
		{ code: "const ALLOWED_KINDS = new Set(['a']);", errors: 1 },
		{ code: "const PATTERN = /x/;", errors: 1 },
		{ code: "const DEFAULTS = { a: 1 };", errors: 1 },
	],
});

tester.run("loop-mutation", plugin.rules["loop-mutation"], {
	valid: [
		"const doubled = [1].map((n) => n * 2);",
		"[1].forEach((n) => console.log(n));",
	],
	invalid: [
		{
			code: "const out = []; for (const n of [1]) { out.push(n); }",
			errors: 1,
		},
		{
			code: "const out = []; [1].forEach((n) => { out.push(n); });",
			errors: 1,
		},
		{
			code: "const map = {}; for (const k of ['a']) { map[k] = 1; }",
			errors: 1,
		},
	],
});

tester.run("side-effect-for-loop", plugin.rules["side-effect-for-loop"], {
	valid: [
		"async function run(items) { for (const item of items) { await item; } }",
		"function find(items) { for (const item of items) { if (item) { return item; } } }",
	],
	invalid: [
		{ code: "for (const item of [1]) { console.log(item); }", errors: 1 },
	],
});

tester.run("inline-object-param", plugin.rules["inline-object-param"], {
	valid: [
		"type Params = { id: string }; export function load({ id }: Params) {}",
		"function load({ id }: { id: string }) {}",
		"export function load(id: string, { limit }: { limit: number }) {}",
	],
	invalid: [
		{ code: "export function load({ id }: { id: string }) {}", errors: 1 },
		{
			code: "export const load = ({ id = 'a' }: { id?: string } = {}) => id;",
			errors: 1,
		},
	],
});

tester.run("nullish-default", plugin.rules["nullish-default"], {
	valid: ["const a = b || c;"],
	invalid: [{ code: "const a = b ?? c;", errors: 1 }],
});

tester.run("nullable-param", plugin.rules["nullable-param"], {
	valid: ["function f(name: string) {}", "const a: string | null = null;"],
	invalid: [{ code: "function f(name: string | null) {}", errors: 1 }],
});
