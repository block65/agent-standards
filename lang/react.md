# React Standards

**Prerequisite:** Also follow the rules in [TypeScript Standards](typescript.md).

## Components
- **Function declarations:** Use `function ComponentName()`, not arrow functions assigned to variables.
- **No `FC`:** Do not use `React.FC` or `FC`. Type props directly on the function parameter.
- **Props:** Use `interface Props` or inline object types. Avoid `type` aliases for props.

## i18n
- **All user-facing strings must be translatable.** Use `<FormattedMessage>` with `defaultMessage` and `description`.
- **No hardcoded strings** in JSX for anything a user reads.

## Styling
- **Vanilla Extract only.** No CSS modules, no inline styles, no Tailwind.
- **Co-locate styles:** `*.css.ts` files next to the component they style.

## State
- **Server state:** Use `@tanstack/react-query`. Wrap queries in custom hooks.
- **Ambient data:** Use React Context for values needed deep in the tree.
- **Local state:** `useState` or `useReducer` for UI-only state.

## Forms & Validation
- **Valibot** for schema validation. Use `safeParse` and map issues to field errors.
