# React Standards

**Prerequisite:** Also follow the rules in [TypeScript Standards](typescript.md).

## Components
- **Function declarations:** Use `function ComponentName()`, not arrow functions assigned to variables.
- **No `FC`:** Do not use `React.FC` or `FC`. Type props directly on the function parameter with a `Props` interface.
- **Props:** Use `interface Props` or inline object types. Avoid `type` aliases for props.
- **Named imports:** Always use named imports from React (`import { useState } from 'react'`), never `import React`.

## i18n
- **All user-facing strings must be translatable.** Use `<FormattedMessage>` with `defaultMessage` and `description`.
- **No hardcoded strings** in JSX for anything a user reads.

## Styling
- **Vanilla Extract only.** No CSS modules, no Tailwind.
- **Co-locate styles:** `*.css.ts` files next to the component they style.
- **No `style` prop:** Never pass inline styles via the `style` prop.

## State
- **Server state:** Use `@tanstack/react-query`. Wrap queries in custom hooks.
- **Ambient data:** Use React Context for values needed deep in the tree.
- **Local state:** `useState` or `useReducer` for UI-only state.

## Forms & Validation
- **Valibot** for schema validation. Use `safeParse` and map issues to field errors.

## Context
- **Validate provider:** Context hooks must throw if called outside their provider.

## Composite Components
- **Namespace pattern:** Export related components from a `parts` module (`Root`, `Header`, `Title`). Re-export as a namespace from the barrel.
- **No object assignment:** Never use `Card.Root = Root`. Use `export * as Card from './parts.ts'` from the barrel for tree-shaking.
