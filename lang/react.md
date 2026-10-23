# React Standards

**Prerequisite:** Also follow the rules in
[TypeScript Standards](typescript.md).

## Components

- **Named imports:** `import { useState } from 'react'`, never `import React`.
- **Composite components:** Export related components (`Root`, `Header`,
  `Title`) individually from a `parts.ts` module, and re-export them from the
  barrel as `export * as Card from './parts.ts'`.
- **Context hooks throw** when called outside their provider, never return
  `undefined`.

## i18n

- **Every string a user reads is translatable.** Use `<FormattedMessage>` with
  `defaultMessage` and a mandatory `description` for translator context.
- **Never set explicit message IDs;** a build-time plugin generates them.
- **Message declaration:** `<FormattedMessage>` in components where possible;
  `defineMessage` for a single string used as a placeholder or property;
  `defineMessages` only for fixed enum lookup tables. Export shared messages
  individually, never grouped. Shared strings such as "Saved" live in a central
  `i18n.ts`.

## Files and Styling

- **Components:** `Component.tsx`, styled by a co-located `Component.css.ts`.
- **Hooks:** `use-[name].ts`.
- **Vanilla Extract only,** no CSS modules or Tailwind.

## State

- **TanStack Start:** Route `loader` functions with `createServerFn` own initial
  route data, read via `Route.useLoaderData()`. Never fetch route data through
  `@tanstack/react-query` on first render; use Query for mutations, polling and
  optimistic updates.
- **SPA:** `@tanstack/react-query` with custom hooks.
- **Forms:** Validate with valibot and map its issues to field errors.
