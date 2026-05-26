# Playwright E2E Standards

**Prerequisite:** Also follow the rules in [Testing Philosophy](testing.md).

E2E tests replace a human QA tester. Their job is to exercise real flows the way a real user does and fail loudly when the product is broken. Tests that exist only to be green are worse than no tests at all.

## Non-negotiables

1. **Never skip tests at runtime to make them pass.** `test.skip(someCondition, ...)` based on environment or runtime state is forbidden unless it gates a documented, tracked platform issue (e.g. `test.skip(browserName === 'webkit', 'tracked in #1234: webkit file picker bug')`). A test that can't meet its preconditions must fail, not vanish.

2. **Never branch inside a test.** No `if`/`switch`/`try` to handle alternate product states. One test = one linear user journey. If the product behaves two ways, write two tests.

3. **Never use arbitrary sleeps.** `page.waitForTimeout(N)`, custom `sleep()`, `setTimeout` — all banned. Playwright's web-first assertions auto-wait. Wait for *UI effects* (a visible element, a status message, a row appearing). Do not wait on network responses as a primary synchronisation strategy — `page.waitForResponse` is an escape hatch for silent background work only, see the assertions section.

4. **Never match exact copy.** Use regex and `toContainText` for human-facing strings when copy genuinely is the thing under test. For identity assertions (which page am I on, which row is this), don't match copy at all — see the selector rules below.

5. **Never adjust an assertion downward to make a red test green.** If a test is flaky, assume the product has a race condition and investigate. `retries` is not a fix.

6. **ABSOLUTE: Never assert on URLs.** `toHaveURL`, `expect(page).toHaveURL(...)`, `page.url()`, `page.waitForURL`, and any regex match against the address bar are **banned without exception** for identity assertions. URLs are an implementation detail; they get restructured during routing refactors, they don't survive locale prefixes, and users don't read them. Assert on what rendered, not where the router thinks you are. There is no scenario in which a URL assertion is the right tool for "did the user end up on the right page". If this rule blocks your test, invoke rule 11.

7. **Don't assert you arrived at a page. Do the next thing.** Navigation is verified implicitly by the auto-wait on the next action. If you clicked through to a listings page to publish a listing, the assertion is the publish button becoming actionable — that can't happen unless the page rendered. Explicit page-identity assertions (URL, heading, page-level testid) are ceremony, not signal, and double the brittle surface area. Terminal steps (the test's last action with nothing to click afterward) do need an assertion — see the assertions section.

8. **Never refuse to add `data-testid` when the rules require it.** If a role-based selector can't uniquely identify an element (one menu item among several with the same role, an icon button with no accessible name, a custom widget with no semantic equivalent), adding a `data-testid` is the correct response. Testid is an earned disambiguator, not a default — reach for it when role + name genuinely can't pick the element out, and never as a substitute for a role that should exist.

9. **Never fill only the required fields in a happy-path test.** A real user fills the form. Omission is a validation test, and gets its own test.

10. **ABSOLUTE: `page.goto` is only permitted at points where a real user arrives at the app from outside it.** Two sanctioned forms: (a) `page.goto('/')` or the configured `baseURL`, to enter the app as a user opening it fresh; (b) navigating to an external-entry URL the test obtained from a simulated external system — password reset and email verification links read from a test mail server, magic-link tokens fetched from the API, OAuth callback URLs from the auth provider's test mode. Banned without exception: `page.goto('/dashboard')`, `page.goto('/settings/profile')`, `page.goto('/items/123')`, and any other mid-app route the test author constructed from a guessed route shape. The test for whether a goto is sanctioned: did the URL come from a system that simulates how a real user would have received it (an email, an SMS, an OAuth redirect), or did the test author type it in? If the latter, the goto is a deep-link shortcut and is banned. If this rule blocks your test, invoke rule 11.

11. **If the rules give no workable path, stop and ask.** Do not substitute a worse selector to satisfy a ban. Surface the problem with: what you were trying to assert, which rule blocked the obvious path, alternatives you considered, your forced choice. Wait for a decision.

## Selectors

The right selector depends on the job. Three jobs, three rules.

### Job 1: interactive elements (buttons, inputs, links, form controls)

Use the first that works. Drop down only when the current tier genuinely fails to uniquely identify the element.

| Priority | Locator                       | Use when                                                |
| -------- | ----------------------------- | ------------------------------------------------------- |
| 1        | `getByRole(role, { name })`   | Any interactive element with an accessible name         |
| 2        | `getByLabel(text)`            | Form fields with visible labels                         |
| 3        | `getByPlaceholder(text)`      | Fields without a label (last resort for forms)          |
| 4        | `getByTestId(id)`             | Icon buttons, ambiguous controls, decorative containers |
| —        | `getByText` as a primary find | **Banned.** Text matches product copy; copy churns.     |
| —        | CSS / XPath                   | **Banned.** If you reach here, you've skipped a step.   |

Role-first is not just stability. `getByRole('button', { name: /submit/i })` also confirms the element is an actual button with an accessible name, which a screen reader can find. `getByTestId('submit-btn')` doesn't, which is why testid on interactive elements is a downgrade when a role works.

### Job 2: finding a specific item in a list, table, or grid

Use a role-based collection selector and filter by user-supplied data the test itself produced.

```ts
await page
  .getByRole("row")
  .filter({ hasText: itemTitle }) // itemTitle was typed by the test
  .getByRole("button", { name: "Delete" })
  .click();
```

Filtering by data the test created is consistent with the no-text-matching rule: the string is yours, not the product's. Do not invent dynamic testids like `data-testid={`row-${user.id}`}` to avoid this pattern — that's testid sprawl, and role-based collection selection is the correct tool.

This is also how navigation is *implicitly* verified in most tests. After clicking "Listings" in the nav, the test's next action is typically to find a specific listing — `page.getByRole("row").filter({ hasText: listingTitle })`. The row can't be found unless the listings page mounted and the data loaded. The find *is* the navigation check; no separate page-identity assertion is needed.

### Job 3: terminal-step assertions (the test's last action)

When the test's last step has no follow-up action whose auto-wait would verify success, assert on what the user came to see. Prefer role-based structural elements; reach for a testid only if no role disambiguates.

```ts
// ✅ Terminal step: confirm the user's data appears where they expect
await page.getByRole("link", { name: "View invoice" }).click();
await expect(
  page.getByRole("article").filter({ hasText: invoiceNumber }),
).toBeVisible();
```

For "did the user leave page X" (logout, cancel, close modal), use the negative form on something the previous page contained — typically a role-based element, falling back to a testid if no role fits:

```ts
await page.getByRole("button", { name: "Log out" }).click();
await expect(page.getByRole("navigation", { name: "Primary" })).not.toBeVisible();
```

### When a page-level testid is the right tool

Most pages don't need one. A test that navigates to a page and then does something on that page is verified by the doing — no marker required. A testid on a page-level component is justified only when:

- The test is a terminal step *and* the page has no structural role or content that uniquely identifies it (a dashboard of mixed widgets, a profile page, a status screen with no specific list or form).
- After all other options — role of the structural element, role + filter on user data, role of the primary content region — none can pick out "the user reached this page" without ambiguity.

Even then, the testid is the assertion of *last resort* for a terminal step, not a routine identity marker for every page. The `ListingsPage` and `OrgPage` style of page-wide testid is mostly unnecessary; the things on the listings page have roles, and the things in the org have data the test produced.

### Roles before testids when adding semantics

Before adding a testid to a button-shaped div, a custom dropdown, an unnamed nav, or any other element with a clear semantic role it currently lacks: **fix the role first.** A `<div onClick>` should become a `<button>`. A custom combobox needs `role="combobox"` and the required ARIA properties. A page with multiple `<nav>` regions needs `aria-label` on each.

Genuine double win: accessibility correctness *and* testability, with the test improvement as a side effect of fixing the real problem. Testid is the right tool when role + accessible name genuinely can't pick out the element (one of several menu items, an icon button with no name, a state container that needs disambiguation); roles are the right tool for *what kind of thing* (a button, a navigation region, a heading). Never invent ARIA roles for application-specific concepts — the role taxonomy is fixed, and roles that lie are worse than testids.

### Adding testids: convention

Kebab-case, describes the thing not the location: `data-testid="listing-action-edit"`, `data-testid="delete-confirm-button"`. Never `data-testid="div-2"` or position-based names.

### Third-party iframes (Stripe, Auth0, reCAPTCHA, OAuth providers, embedded checkouts)

Inside `frameLocator()`, the rules above are suspended. You don't control the markup, so the ladder doesn't apply. Use whatever selector works, keep the scope as narrow as possible, and add a comment naming the third-party origin so the relaxation is explicit.

```ts
// Stripe Elements iframe — selectors below match Stripe's DOM, which we don't control
const cardFrame = page.frameLocator('iframe[name^="__privateStripeFrame"]');
await cardFrame.locator('[name="cardnumber"]').fill("4242424242424242");
```

This is an explicit escape hatch, not a general permission. Outside the `frameLocator()`, the normal rules resume.

### File uploads and downloads

The native OS file picker cannot be driven through the DOM, and clicking the visible "Upload" button will hang in headless CI. Use Playwright's dedicated APIs.

**Uploads:** find the underlying `<input type="file">` and call `setInputFiles`. Do not click the visible upload button and then try to interact with the OS dialog.

```ts
// ✅ Drive the file input directly
await page
  .getByLabel("Upload avatar")
  .setInputFiles("./fixtures/avatar.png");
await expect(page.getByTestId("avatar-preview")).toBeVisible();
```

If the file input is visually hidden behind a styled button, the label association still works; `getByLabel` finds the input. If there is no label, add one (and an `aria-label` on the button), or as a last resort use a testid on the input itself.

**Downloads:** use the `download` event. The user-visible action (click) and the assertion (file received) are two separate things, and Playwright gives you a promise for the latter.

```ts
// ✅ Wait for the download event triggered by the click
const downloadPromise = page.waitForEvent("download");
await page.getByRole("button", { name: "Export CSV" }).click();
const download = await downloadPromise;

expect(download.suggestedFilename()).toMatch(/\.csv$/);
// If the test needs to inspect contents, save and read; otherwise the event firing is the signal.
```

This is the one place `waitForEvent` is the right tool rather than an escape hatch — downloads have no DOM effect by design, so a UI assertion is impossible.

## Navigation and synchronisation

Navigation is verified by the next action's auto-wait, not by a separate assertion. The action you're about to perform can't complete unless the navigation succeeded and the destination rendered. That's the verification.

```ts
// ✅ The auto-wait on the row filter does the navigation check for free
await page.getByRole("link", { name: "Listings" }).click();
await page
  .getByRole("row")
  .filter({ hasText: listingTitle })
  .getByRole("button", { name: "Edit" })
  .click();
```

A navigation event firing doesn't prove the right destination was reached — error pages, login redirects, and onboarding detours all fire `framenavigated` too. Explicit `waitForURL`, `waitForLoadState`, or `waitForEvent('framenavigated')` are only correct for the narrow case of multi-step redirect chains where you need to wait for the *final* navigation before asserting. Even then, the actual verification is done by the next action you perform.

`waitForLoadState('networkidle')` is banned outright on any app with websockets, long-polling, analytics beacons, or background refresh — which is most SaaS apps. It will either time out or pass meaninglessly. Wait on the specific thing you care about.

### External entry points

Password reset, email verification, magic-link auth, OAuth callbacks, and shareable links sent over email or SMS all involve a user arriving at the app at a URL they didn't type. Tests for these flows obtain the URL from the same source the user would (a test mail server, the API response that would normally be emailed, the auth provider's test mode) and then navigate to it. The URL is data, not a guess.

```ts
// ✅ Reset link comes from the mail server, not the test author's keyboard
await test.step("request reset", async () => {
  await page.goto("/");
  await page.getByRole("link", { name: "Forgot password" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send reset link" }).click();
  await expect(page.getByRole("status")).toContainText(/check your email/i);
});

await test.step("follow reset link from email", async () => {
  const resetEmail = await mailServer.waitForEmail({ to: email });
  const resetLink = resetEmail.extractLink({ name: /reset password/i });
  await page.goto(resetLink); // sanctioned: URL came from the email, not the test
  // No page-identity assertion here — the next action verifies the reset page mounted
  await page.getByLabel("New password").fill(faker.internet.password({ length: 20 }));
  await page.getByRole("button", { name: "Set new password" }).click();
});
```

The test for whether a `goto` is sanctioned: trace the URL back one step. Did it come from a system simulating how the user would have received it, or from a string literal the test author wrote? Only the former is allowed.

### A note on navigation cost

Clicking through the app instead of deep-linking costs DOM render and network time per test. If a single page accumulates many E2E tests that all pay the same navigation tax, that is usually the rule surfacing a coverage smell: exhaustive variation on one page is component-test territory, not E2E. Push validation permutations, state-toggle combinations, and copy variations down to component tests. E2E covers user journeys; if you have ten genuinely distinct journeys ending at the same page, the navigation is real testing surface and worth the cost. The fix for slow E2E suites is fewer tests on better journeys, not deep-linking shortcuts.

## Test structure

### Naming

Describe user-visible behaviour, not implementation.

```ts
// ✅
test("user can submit a draft item and see it on their dashboard");
// ❌
test("POST /items returns 200 and dashboard query refetches");
```

### Three phases with `test.step()`

Every test has three phases: arrange, act, assert. Use `test.step()` to make them visible in the trace viewer. Do not use `console.log` as a substitute.

```ts
test("user can submit a draft item", async ({ page, authedUser }) => {
  await test.step("create draft via API", async () => {
    await authedUser.api.createItem({ status: "draft", title: itemTitle });
  });

  await test.step("submit from dashboard", async () => {
    await page.goto("/");
    await page.getByRole("link", { name: "Dashboard" }).click();
    // No page-identity assertion — the row filter below verifies the dashboard rendered
    await page
      .getByRole("row")
      .filter({ hasText: itemTitle })
      .getByRole("button", { name: "Submit" })
      .click();
    await page.getByRole("button", { name: "Confirm submit" }).click();
  });

  await test.step("item appears in public results", async () => {
    await page.getByRole("link", { name: "Browse items" }).click();
    // Terminal step — assert what the user came to see
    await expect(
      page.getByRole("link").filter({ hasText: itemTitle }),
    ).toBeVisible();
  });
});
```

### Setup through the fastest reliable path

UI is for exercising the feature *under test*. Everything else — auth, seed data, account state — goes through the API or a fixture. Do not log in through the login form in every test; use `storageState`.

### Isolation

Every test creates its own data. No shared mutable state. Two parallel runs of the suite must never collide.

```ts
const email = `qa-${crypto.randomUUID()}@example.test`;
const title = `Test item ${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
```

## Filling forms

Fill forms the way a user does: all fields a user would reasonably fill, with realistic values. Use faker or inline realistic data — never `"a"`, `"test"`, `"123"` unless specifically testing minimum-length behaviour.

```ts
// ✅ Happy-path signup
await page.getByLabel("Full name").fill(faker.person.fullName());
await page.getByLabel("Work email").fill(`qa-${crypto.randomUUID()}@example.test`);
await page.getByLabel("Company").fill(faker.company.name());
await page.getByLabel("Password", { exact: true }).fill(faker.internet.password({ length: 20 }));
await page.getByLabel(/i agree to the terms/i).check();
await page.getByRole("button", { name: "Create account" }).click();

// Next action verifies arrival on the onboarding flow
await page.getByRole("button", { name: "Get started" }).click();
```

Validation tests cover omission, but:

- One missing field per test, not combinatorial coverage.
- A representative sample (email format, password strength, terms unchecked) — not every field.
- Field-level validation is mostly unit/component territory. E2E validates that the product surfaces errors correctly for the **shapes** of failure, not every permutation.

### Bounded randomness

Faker is correct for shape (a random email-looking string, a random number in range) but can produce values that hit real parsing edge cases (names with apostrophes, non-ASCII addresses, locale-specific phone formats). If a faker-generated value reveals a bug, the bug is real and the value should be captured as a regression fixture — but unconstrained faker in every test means flakes that vanish on re-run because the random input changed.

For fields the product parses (names, emails, phone numbers, addresses), constrain faker to a known locale and character class. For fields that are opaque strings (passwords, titles, descriptions), unconstrained faker is fine. When in doubt, prefix random values with a recognisable marker (`qa-`, `test-`) so the data is queryable in the database and obvious in logs.

## Assertions

### Shape, not literal value

```ts
// ❌ brittle
await expect(page.getByRole("alert")).toHaveText("Please enter a valid email address.");

// ✅ resilient
await expect(page.getByRole("alert")).toContainText(/valid email/i);
```

### Dynamic values: assert presence or pattern

```ts
// ❌ asserts a specific timestamp
await expect(page.getByTestId("created-at")).toHaveText("Nov 17, 2025 14:32");

// ✅ asserts the shape
await expect(page.getByTestId("created-at")).toHaveText(/\w+ \d{1,2}, \d{4}/);
```

### Web-first assertions only

`expect(locator).toBeVisible()`, `.toContainText(...)` and the rest of the `expect(locator).*` family all retry automatically. Never pre-wait manually, and never wrap a non-retrying check like `isVisible()` in an `expect()`.

```ts
// ❌ double-waiting, and isVisible() doesn't retry
await page.waitForTimeout(1000);
expect(await page.locator(".success").isVisible()).toBe(true);

// ✅
await expect(page.getByRole("status")).toContainText(/saved/i);
```

### Assert the outcome, not the mechanism

A user doesn't know the API was called. They know the toast appeared and the row showed up. Assert the toast and the row. Reach for `page.waitForResponse` only when the UI gives no feedback for something you need to verify.

### State is what the user can do

If a state change matters, it changes the UI — different buttons appear, different layouts render, different feedback shows. Assert on that, not on the state itself. Never expose internal state via `data-*` attributes for the purpose of letting E2E read it; that's introspection masquerading as testing, and it's solving a problem that shouldn't exist at this layer.

```ts
// ❌ Reading state through an attribute
await expect(
  page.getByRole("article").filter({ hasText: title }),
).toHaveAttribute("data-status", "active");

// ✅ The user-visible consequence of "active" is that Pause exists
await page
  .getByRole("article")
  .filter({ hasText: title })
  .getByRole("button", { name: "Pause" })
  .click();
```

If the state has no user-visible consequence, you're testing internal behaviour and the test belongs in a different layer (unit, component, or contract tests on the state machine). If the state *does* have a UI consequence but you're tempted to skip checking it because "I just want to confirm the listing is active before continuing", that's not a test, it's hedging against your own setup — drop it. The next step will fail loudly if the setup was wrong.

The exception is Playwright's built-in ARIA-state assertions: `toBeDisabled()`, `toBeChecked()`, `toBeFocused()`, `toBeExpanded()`. These check states that *are* user-visible by definition (a disabled button looks disabled to a screen reader and to a user) and use ARIA, not custom data attributes.

## Coverage strategy

Test everything a real user can do. Within every flow, also cover:

- **Validation** — submit invalid data and assert the error appears. Not every permutation, but a representative shape.
- **Toasts and feedback** — assert success/error notifications appear after actions and contain the right shape of message.
- **Navigation** — verified implicitly by the next action's auto-wait. Don't add explicit page-identity assertions for intermediate steps. For terminal steps (the last action of the test), assert on what the user came to see — usually a role-based structural element containing the user's data. Back-navigation and protected-route redirects work the same: the next action verifies arrival.
- **Disabled and loading states** — assert that buttons are disabled while a request is in flight and re-enable after. A form that can be double-submitted has a bug.
- **Idiot-proofing** — confirm dialogs before destructive actions, unsaved-changes warnings, recovery from errors.

**Push down to unit/component:**

- Exhaustive validation permutations (every field's every error message)
- Pure client-side state toggles (tabs, accordions, dropdown open/close) when isolated from any data flow
- Copy and translations
- Styling and layout

If a user could encounter it in a real session, it belongs in E2E.

## Fixtures

Write Playwright fixtures for anything reused 3+ times.

```ts
type Fixtures = {
  authedUser: { page: Page; api: ApiClient; user: User };
};

export const test = base.extend<Fixtures>({
  authedUser: async ({ browser }, use) => {
    const user = await createUserViaApi();
    const context = await browser.newContext({
      storageState: await user.storageState(),
    });
    const page = await context.newPage();
    await use({ page, api: user.api, user });
    await context.close();
    await user.cleanup();
  },
});
```

Keep locators inline in the test when used once. Promote to a page-object helper only when the same flow appears in 3+ tests — and even then keep it thin: a function, not a class hierarchy.

### Multiple user roles

When the product has distinct user types (admin, viewer, member, expired-trial, etc.), write a fixture per role. Do not parameterise a single `authedUser` fixture and branch inside the test on which role it produced — that violates the no-branching rule. The fixture *body* can take parameters and call `createUserViaApi({ role: 'admin' })`; the *test* receives a fully-formed `adminUser` and never asks what role it is.

## Flakiness

Flaky tests erode trust faster than missing tests.

1. First assumption on a flake: **the product has a race condition.** Fix the product before the test.
2. Second: the test is waiting on the wrong thing (loadstate instead of a specific response, timeout instead of a visible element). Rewrite the wait.
3. `retries: 1` in CI is acceptable for infrastructure blips, not for gluing broken tests together. A test that needs 3 retries is broken.
4. Never paper over a flake with `waitForTimeout`. Find the actual signal.
5. **Never raise `actionTimeout`, `navigationTimeout`, or `testTimeout` to absorb a flake.** SLOW = FAIL — see `engineering/testing.md`.

## Anti-patterns

```ts
// ❌ Skip to hide a failure
test.skip(Math.random() > 0.5, "sometimes flaky");
// ✅ Fix the cause or delete the test
```

```ts
// ❌ Branch inside test
if (await page.getByText("Promo banner").isVisible()) {
  await page.getByRole("button", { name: "Apply" }).click();
}
// ✅ Two tests: "checkout without promo" and "checkout with active promo banner"
```

```ts
// ❌ URL assertion to verify navigation
await page.getByRole("link", { name: "Dashboard" }).click();
await expect(page).toHaveURL(/\/dashboard/);
// ✅ The next action verifies arrival
await page.getByRole("link", { name: "Dashboard" }).click();
await page.getByRole("row").filter({ hasText: itemTitle }).click();
```

```ts
// ❌ Heading as page identity (copy and locale fragile)
await page.getByRole("button", { name: "Save" }).click();
await expect(page.getByRole("heading", { name: /welcome/i })).toBeVisible();
// ✅ Terminal step — assert what the user came to see, by role + their data
await page.getByRole("button", { name: "Save" }).click();
await expect(page.getByRole("status")).toContainText(/saved/i);
```

```ts
// ❌ Defence-in-depth identity
await expect(page).toHaveURL(/\/dashboard/);
await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
await expect(page.getByTestId("dashboard")).toBeVisible();
// ✅ No identity assertion — do the next thing
await page.getByRole("row").filter({ hasText: itemTitle }).getByRole("button", { name: "Edit" }).click();
```

```ts
// ❌ Ceremonial page-identity testid before doing the next thing
await page.getByRole("link", { name: "Listings" }).click();
await expect(page.getByTestId("ListingsPage")).toBeVisible();
await page.getByRole("row").filter({ hasText: title }).getByRole("button", { name: "Edit" }).click();
// ✅ Drop the assertion — the row filter's auto-wait verifies the listings page rendered
await page.getByRole("link", { name: "Listings" }).click();
await page.getByRole("row").filter({ hasText: title }).getByRole("button", { name: "Edit" }).click();
```

```ts
// ❌ Text-scoping a region
await page.getByText("Account settings").locator("..").getByRole("button", { name: "Save" }).click();
// ✅ Scope by a landmark role, not by copy
await page.getByRole("region", { name: "Account settings" }).getByRole("button", { name: "Save" }).click();
```

```ts
// ❌ CSS selector reaching into implementation
await page.locator("div.card > div:nth-child(2) button.primary").click();
// ✅ Role-based, or add a testid
await page
  .getByRole("article")
  .filter({ hasText: itemTitle })
  .getByRole("button", { name: "Publish" })
  .click();
```

```ts
// ❌ Dynamic testid per row
<tr data-testid={`row-${item.id}`}>
await page.getByTestId(`row-${item.id}`).click();
// ✅ Role-based collection + filter by data
await page.getByRole("row").filter({ hasText: item.title }).click();
```

```ts
// ❌ Reading internal state through a data attribute
await expect(
  page.getByRole("article").filter({ hasText: title }),
).toHaveAttribute("data-status", "active");
await page.getByRole("button", { name: "Edit" }).click();
// ✅ The state's UI consequence is the assertion — and the next step
await page
  .getByRole("article")
  .filter({ hasText: title })
  .getByRole("button", { name: "Pause" }) // "Pause" only exists when active
  .click();
```

```ts
// ❌ "Continue-checking" — hedging against your own setup
await expect(page.getByRole("heading", { name: title })).toBeVisible();
await page.getByRole("button", { name: "Publish" }).click();
// ✅ Just do the next thing — it'll fail loudly if setup was wrong
await page.getByRole("button", { name: "Publish" }).click();
```

```ts
// ❌ Minimum-viable form fill
await page.getByLabel("Email").fill("a@b.c");
await page.getByLabel("Password").fill("x");
// ✅ Realistic user input
await page.getByLabel("Email").fill(`qa-${crypto.randomUUID()}@example.test`);
await page.getByLabel("Password").fill(faker.internet.password({ length: 20 }));
```

```ts
// ❌ Sleep-based wait
await page.getByRole("button", { name: "Save" }).click();
await page.waitForTimeout(2000);
await expect(page.locator(".toast")).toBeVisible();
// ✅ Effect-based
await page.getByRole("button", { name: "Save" }).click();
await expect(page.getByRole("status")).toContainText(/saved/i);
```

```ts
// ❌ networkidle on a SaaS app with long-poll or websockets
await page.waitForLoadState("networkidle");
// ✅ Wait on the specific thing you care about
await expect(page.getByRole("row").filter({ hasText: itemTitle })).toBeVisible();
```

```ts
// ❌ page.goto to a mid-app route
await page.goto("/settings/profile/security");
await page.getByRole("button", { name: "Change password" }).click();
// ✅ Navigate the way a user would; the final click verifies arrival
await page.goto("/");
await page.getByRole("button", { name: /account menu/i }).click();
await page.getByRole("menuitem", { name: "Settings" }).click();
await page.getByRole("link", { name: "Profile" }).click();
await page.getByRole("link", { name: "Security" }).click();
await page.getByRole("button", { name: "Change password" }).click();
```

```ts
// ❌ Explicit navigation wait as verification
await page.getByRole("button", { name: "Create" }).click();
await page.waitForURL(/\/items\//);
// ✅ The next action auto-waits through the navigation
await page.getByRole("button", { name: "Create" }).click();
await page.getByRole("button", { name: "Publish" }).click();
```

## Config baseline

```ts
export default defineConfig({
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  // 1 retry to absorb infra blips only — not flaky tests. A test that needs 2+ retries is broken.
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
  projects: [
    { name: "chromium", use: devices["Desktop Chrome"] },
    // add webkit/firefox only if you ship there
  ],
});
```

## Mental model

A user:

- Doesn't know the DOM — navigates by roles, labels, and what's visibly on screen.
- Doesn't type URLs into the address bar to get around the app — clicks links and buttons.
- Doesn't read the address bar to confirm they're on the right page — they see the page and they act.
- Doesn't reload to check — the UI updates.
- Fills realistic values, not minimum placeholders.
- Reads error messages and corrects them.
- Expects feedback within a reasonable latency, not a fixed sleep.

A test recording that user's session doesn't need to pause and ask "am I on the right page?" between every step. The user knows they're on the right page because they can see the button they came to click. So does the test: clicking the button is the proof.

A test is a recording of what that user did, written so that future-you can read it in 30 seconds and know exactly what broke when it fails. If you can't tell from the name and the trace what the user was trying to do — the test is wrong, regardless of whether it is passing today.