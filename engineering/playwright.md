# Playwright E2E Standards

**Prerequisite:** Also follow the rules in [Testing Philosophy](testing.md).

## Non-negotiables

1. **No runtime skips.** `test.skip(condition, ...)` only gates a tracked
   platform issue and names it:
   `test.skip(browserName === "webkit", "tracked in #[N]: [Reason]")`. A test
   that cannot meet its preconditions fails.
2. **No branching inside a test.** No `if`/`switch`/`try` for alternate product
   states; one test is one linear journey, and a product that behaves two ways
   gets two tests.
3. **No sleeps.** `page.waitForTimeout`, custom `sleep()` and `setTimeout` are
   banned. Wait for a UI effect through web-first assertions;
   `page.waitForResponse` is only for background work with no UI feedback.
4. **No URL assertions.** `toHaveURL`, `page.url()` and regexes on the address
   bar are banned as identity checks; assert what rendered. `page.waitForURL` is
   a wait, sanctioned only to sequence a multi-step redirect chain before the
   real assertion.
5. **Do the next thing instead of asserting arrival.** The next action's
   auto-wait verifies navigation; page-identity assertions (URL, heading,
   page-level testid) double the brittle surface. Only the terminal step asserts
   (see Selectors, job 3). A check that only confirms setup before continuing is
   hedging: drop it.
6. **`page.goto` only where a user arrives from outside the app:** `/` (or
   `baseURL`), or a URL the test obtained from a simulated external system (a
   reset link from a test mail server, a magic-link token from the API, an OAuth
   callback from the provider's test mode). A mid-app route the author typed
   (`page.goto("/[route]")`) is a banned deep-link shortcut. Trace the URL back
   one step: from a system simulating how the user receives it, or a string
   literal?
7. **Happy paths fill every field a user would,** with realistic values (faker),
   never `"a"`, `"test"` or `"123"`. Omission is a validation test.
8. **When the rules give no workable path, stop and ask** instead of
   substituting a worse selector. State what you were asserting, which rule
   blocked it, the alternatives considered and your forced choice.

## Selectors

### Job 1: interactive elements

Use the first tier that uniquely identifies the element.

| Priority | Locator                       | Use when                                                |
| -------- | ----------------------------- | ------------------------------------------------------- |
| 1        | `getByRole(role, { name })`   | Any interactive element with an accessible name         |
| 2        | `getByLabel(text)`            | Form fields with visible labels                         |
| 3        | `getByPlaceholder(text)`      | Fields without a label (last resort for forms)          |
| 4        | `getByTestId(id)`             | Icon buttons, ambiguous controls, decorative containers |
| —        | `getByText` as a primary find | **Banned.** Text matches product copy; copy churns.     |
| —        | CSS / XPath                   | **Banned.** If you reach here, you've skipped a step.   |

Role-first also proves a screen-reader-findable control exists. Scope a region
by its landmark (`getByRole("region", { name })`), not by text plus `".."`.

A testid is earned on one of three axes, never on speculation:

- **Ambiguity**: role plus name cannot pick it out (one of several menu items,
  an unnamed icon button).
- **Locale independence**: the accessible name varies across languages or
  per-client deployments.
- **Volatility**: the label is designed to churn (marketing CTAs, A/B copy).

When one applies, add the testid; do not refuse. Testids are kebab-case and name
the thing, not its position: `[thing]-[action]`, never `div-2`.

**Fix the role before adding a testid.** A `<div onClick>` becomes a `<button>`,
a custom combobox gets `role="combobox"` and its ARIA properties, and multiple
`<nav>`s each get an `aria-label`. Use a testid for an application concept
with no ARIA role; an invented role misleads assistive technology.

### Job 2: an item in a list, table or grid

Filter a role-based collection by data the test itself produced; that string is
the test's, not the product's. Do not add dynamic testids like
`row-${[id]}` to avoid this.

```ts
await page
	.getByRole("row")
	.filter({ hasText: itemTitle })
	.getByRole("button", { name: /delete/i })
	.click();
```

### Job 3: terminal-step assertions

The last step, with no follow-up action to auto-wait on, asserts what the user
came to see: a role-based element, filtered by test data where needed. For "the
user left page X" (logout, cancel, close), assert `.not.toBeVisible()` on an
element the previous page contained. A page-level testid is the last resort,
only when no role, content or filter identifies the page.

### Escapes

Inside a third-party `frameLocator()` (payment, auth, captcha), any selector
that works is allowed, scoped as narrowly as possible, with a comment naming the
third-party origin.

A locator that steps outside the priority order carries a one-line comment at
the call site saying why; one that follows the order
carries none. A plain stem regex needs no comment; comment a regex whose shape
encodes a disambiguation:

```ts
getByRole("button", { name: /^[name]$/i }); // anchored because "[longer name]" is also on the page
```

### Files and browser events

- **Uploads:** `setInputFiles` on the `<input type="file">`, found by
  `getByLabel` even when visually hidden. With no label, add one; fall back to a
  testid on the input, then to `page.waitForEvent("filechooser")` registered
  before the click.
- **Downloads, file choosers, popups:** `page.waitForEvent` is the right tool
  for browser-level events with no DOM effect. For outcomes the UI reflects, it
  stays an escape hatch.

## Copy and locale

Bind tests to an element's identity, not one locale's rendering of it.

- **Unit and component tests** resolve copy by message key
  (`messages.[key].defaultMessage`), already in scope where the component
  renders.
- **E2E** matches pinned-locale rendered copy with a regex:
  `getByRole("button", { name: /save/i })`. Do not export `defineMessages`
  blocks for e2e to import: production ships per-locale catalogs with
  `defaultMessage` stripped, so imported keys match nothing there. Only shared
  strings already centralised in `i18n.ts` may be referenced by key.
- **Assert text only when the words are the behaviour**: an error's meaning,
  confirmation copy the user must trust. Match the fragment, not the sentence.
  When text stands in for structure or state, assert the structure or state.

GOOD: pass and fail render the same toast, so only the words distinguish them.

```ts
test("[behaviour]", async () => {
	await expect(toast).toContainText(/[expected reason]/i);
	await expect(toast).not.toContainText(/failed precondition/i);
});
```

## Navigation and synchronisation

A navigation event does not prove the destination: error pages, login redirects
and onboarding detours all fire `framenavigated`, so the next action verifies
it. `waitForURL`, `waitForLoadState` and `waitForEvent("framenavigated")` are
only for waiting out a multi-step redirect chain. Wait on the specific element
or response, never the `networkidle` load state, which on an app with
websockets, polling, beacons or background refresh times out or passes
meaninglessly.

Click through instead of deep-linking. When many tests pay the same navigation
cost to one page, push the variations down to component tests: fewer tests on
better journeys.

## Test structure

- **Phases in `test.step()`**: arrange, act, assert as named steps, visible in
  the trace viewer; no `console.log` in their place.
- **Setup through the API or a fixture.** UI only for the feature under test;
  log in with `storageState`, not the login form.
- **Bounded randomness.** Constrain faker to a known locale and character class
  for fields the product parses (names, emails, phones, addresses); opaque
  strings (passwords, titles) stay unconstrained. Prefix generated values with
  `qa-` so they are findable in the database and logs. A faker value that
  reveals a bug becomes a regression fixture.

## Assertions

- **Web-first only.** `expect(locator).*` retries; never pre-wait, and never
  wrap a one-shot read like `isVisible()` in `expect()`.
- **Patterns for dynamic values**: dates, counts and IDs match a regex, not a
  literal.
- **Assert the outcome, not the mechanism**: the toast and the row, not the API
  call.
- **State is what the user can do.** Never expose internal state as `data-*`
  attributes for e2e to read. Built-in ARIA-state matchers (`toBeDisabled`,
  `toBeChecked`, `toBeExpanded`, `toBeFocused`) are fine. A state with no UI
  consequence belongs in another layer.

BAD: reads state through an attribute.

```ts
test("[behaviour]", async () => {
	await expect(card).toHaveAttribute("data-status", "active");
});
```

GOOD: acts on the user-visible consequence of the state.

```ts
await card.getByRole("button", { name: /pause/i }).click();
```

### Toasts

Read the toast component for its role before assuming `getByRole("alert")`. To
assert a toast does _not_ contain something, use `.not.toContainText()` on the
live toast locator; `toHaveCount(0)` on a free-floating locator passes the
moment the toast dismisses.

## Coverage

Test everything a real user can do. Within each flow cover validation (one
missing field per test, a representative sample of failure shapes), success and
error feedback, back-navigation and protected-route redirects, disabled state
while a request is in flight (a form that double-submits has a bug), and
confirmations before destructive actions, unsaved-changes warnings, and
recovery from errors. Push down to unit or component tests:
validation permutations, client-only toggles isolated from data, copy and
translations, styling and layout.

## Fixtures

- Write a fixture for anything reused 3+ times. Keep single-use locators inline;
  promote a flow to a page-object helper only at 3+ tests, as a function, not a
  class hierarchy.
- **One fixture per user role** (`adminUser`, `viewerUser`). The fixture body
  may take parameters; the test never asks which role it received.

## Flakes

First assume a product race and fix the product; second, the test waits on the
wrong thing. `retries: 1` in CI absorbs infrastructure blips only; a test that
needs more is broken.

## Config baseline

```ts
export default defineConfig({
	fullyParallel: true,
	forbidOnly: Boolean(process.env.CI),
	retries: process.env.CI ? 1 : 0,
	reporter: [["html"], ["list"]],
	use: {
		baseURL: process.env.BASE_URL ?? "http://localhost:3000",
		trace: "on-first-retry",
		screenshot: "only-on-failure",
		video: "retain-on-failure",
		actionTimeout: 10_000,
		navigationTimeout: 30_000,
	},
	projects: [{ name: "chromium", use: devices["Desktop Chrome"] }],
});
```
