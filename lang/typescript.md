# TypeScript Standards

**Prerequisite:** Also follow the rules in
[JavaScript Standards](javascript.md).

## Running and Checking

- **No emit, no transpilers:** TypeScript is source and type-checking only.
  Verify with `tsc -b --noEmit` or equivalent. Run TypeScript on current Node
  directly, never through `tsx`, `ts-node` or another transpiler.

## Type Safety

- **No `as unknown`:** Widening to `unknown` discards the type the checker had.
  `as const` and `satisfies` are fine: they assert or check without overriding
  the checker.
- **Infer types, exported return types included.** Annotate a return type only
  when it defines an intended contract, enables recursion, or is a type
  predicate or assertion signature.
- **Name the parameter type of an exported function that takes one object.**
  Declare the type, then destructure and set defaults against it, so the
  contract does not sit inside the destructuring pattern.

  BAD:

  ```ts
  export function [action]({ [a], [b] = 1 }: { [a]: string; [b]?: number }) {}
  ```

  GOOD:

  ```ts
  type [Action]Params = { [a]: string; [b]?: number };

  export function [action]({ [a], [b] = 1 }: [Action]Params) {}
  ```

- **`satisfies` over type annotation:** `const x = { ... } satisfies T` keeps
  the inferred literal types that `const x: T = { ... }` discards.
- **`const` type parameters:** Use `function<const T>` to preserve literal types
  from arguments.
- **Fix the type, never add a runtime hack** to avoid a type error.
- **`as const` objects and derived unions instead of enums:** enums are not
  erasable and fail under Node's type stripping.
- **Conditional spreads:** `{ ...(cond && { foo: bar }) }` satisfies a strict
  `?: T` target; where the target declares `?: T | undefined`, pass the value
  directly. Spread a maybe-object as is (`...maybeObj`); a maybe-array needs
  `...(arr ?? [])`, since a nullish array spread throws.

## Compiler Configuration

- **Extend the shared config.** `tsconfig.json` extends the `@block65/tsconfig`
  variant matching the target: `nodejs<major>` for a Node runtime, otherwise
  `vite-react`, `cloudflare-worker`, `nextjs`, or `vanilla` (`-projref` variants
  for project references). Check the package for the majors it publishes rather
  than assuming one.
- **Never loosen a flag locally;** fix the type. A target the shared config does
  not cover is a change to that package.
- **`exactOptionalPropertyTypes` is always on.**

## Optional Properties

- **`?: T` is the default.** Absent or a value, no third state: `"foo" in obj`
  narrows `obj.foo` to `T`.
- **`?: T | undefined` is a declared opt-in** for where `prop={maybe}` reads
  better than `{ ...(maybe && { prop: maybe }) }`, in practice JSX props on leaf
  components. It costs narrowing: `"foo" in obj` leaves `T | undefined`.
- **Properties only, not parameters.** See Nullability in
  [JavaScript Standards](javascript.md).
- **Test the key, not truthiness.** `!obj.prop` also matches `0`, `""` and
  `false`. Use `"prop" in obj` to ask whether it was specified, and a value
  comparison to ask what it holds.
- **Make the invalid value unrepresentable.** When `""` or `0` is invalid for a
  field, constrain it with a valibot-validated or branded type.

## Untyped Input

- **`unknown` only where the data is unknown:** bytes off the wire, parsed JSON,
  `postMessage` payloads, third-party webhook bodies. Internal callers are
  already typed; do not re-validate them.
- **Parse `unknown` with valibot before use,** and handle the parse failure.

## Imports and Files

- **Extensions:** Use `.ts` in all import specifiers (`'./foo.ts'`), never `.js`
  or bare.
- **Types near the top:** Declare every `interface` and `type` after imports and
  module constants, before any implementation.
