# Playwright E2E Standards

E2E tests replace a human QA tester. Their job is to exercise real flows the way a real user does and fail loudly when the product is broken. Tests that exist only to be green are worse than no tests at all.

## Non-negotiables

1. **Never skip tests at runtime to make them pass.** `test.skip(someCondition, ...)` based on environment or runtime state is forbidden unless it gates a documented, tracked platform issue (e.g. `test.skip(browserName === 'webkit', 'tracked in #1234: webkit file picker bug')`). A test that can't meet its preconditions must fail, not vanish.

2. **Never branch inside a test.** No `if`/`switch`/`try` to handle alternate product states. One test = one linear user journey. If the product behaves two ways, write two tests.

3. **Never use arbitrary sleeps.** `page.waitForTimeout(N)`, custom `sleep()`, `setTimeout` — all banned. Playwright's web-first assertions auto-wait. Wait for _effects_ (visible element, network response), never for clocks. Use `expect.poll()` for polling patterns.

4. **Never match exact copy.** Use regex and `toContainText` for human-facing strings. Copy changes; tests should survive a marketing tweak.

5. **Never adjust an assertion downward to make a red test green.** If a test is flaky, assume the product has a race condition and investigate. `retries` is not a fix.

6. **Never refuse to add `data-testid`.** If a semantic locator (`getByRole`, `getByLabel`) can't uniquely identify an element, adding a `data-testid` is the correct response. Reaching for CSS or XPath means you skipped a step.

7. **Never fill only the required fields in a happy-path test.** A real user fills the form. Omission is a validation test, and gets its own test.

## Selector priority

Use the first option that works. Drop down only when the current tier genuinely fails.

| Priority | Locator                             | Use when                                                                              |
| -------- | ----------------------------------- | ------------------------------------------------------------------------------------- |
| 1        | `getByRole(role, { name })`         | Any interactive element with a name (buttons, links, inputs, headings)                |
| 2        | `getByLabel(text)`                  | Form fields with visible labels                                                       |
| 3        | `getByPlaceholder(text)`            | Fields without a label (last resort for forms)                                        |
| 4        | `getByText(text, { exact: false })` | Scoping to a region containing known copy                                             |
| 5        | `getByTestId(id)`                   | Icon buttons, decorative containers, list items without user-visible identifying text |
| 6        | CSS / XPath                         | **Banned.** If you reach here, you've skipped a step.                                 |

**Add `data-testid` proactively** when none of 1–4 work. Kebab-case, describes the thing not the location: `data-testid="listing-card"`, `data-testid="delete-confirm-button"`. Never `data-testid="div-2"`.

## Test structure

### Naming

Describe user-visible behaviour, not implementation.

```ts
// ✅
test('user can publish a draft listing and see it on their dashboard')
// ❌
test('POST /listings returns 200 and dashboard query refetches')
```

### Three phases with `test.step()`

Every test has three phases. Use `test.step()` to make them visible in the trace viewer. Do not use `console.log` as a substitute.

```ts
test('user can publish a draft listing', async ({ page, authedUser }) => {
  await test.step('create draft via API', async () => {
    await authedUser.api.createListing({ status: 'draft', title: 'Test cottage' });
  });

  await test.step('publish from dashboard', async () => {
    await page.goto('/dashboard');
    await page
      .getByRole('row', { name: /test cottage/i })
      .getByRole('button', { name: 'Publish' })
      .click();
    await page.getByRole('button', { name: 'Confirm publish' }).click();
  });

  await test.step('listing appears in public results', async () => {
    await page.goto('/listings');
    await expect(page.getByRole('link', { name: /test cottage/i })).toBeVisible();
  });
});
```

### Setup through the fastest reliable path

UI is for exercising the feature _under test_. Everything else — auth, seed data, account state — goes through the API or a fixture. Do not log in through the login form in every test; use `storageState`.

### Isolation

Every test creates its own data. No shared mutable state. Two parallel runs of the suite must never collide.

```ts
const email = `qa-${crypto.randomUUID()}@example.test`;
const title = `Test listing ${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
```

## Filling forms

Fill forms the way a user does: all fields a user would reasonably fill, with realistic values. Use faker or inline realistic data — never `"a"`, `"test"`, `"123"` unless specifically testing minimum-length behaviour.

```ts
// ✅ Happy-path signup
await page.getByLabel('Full name').fill('Alex Tan');
await page.getByLabel('Work email').fill(`qa-${crypto.randomUUID()}@example.test`);
await page.getByLabel('Company').fill('Acme Corp');
await page.getByLabel('Password', { exact: true }).fill('CorrectHorseBatteryStaple!1');
await page.getByLabel(/i agree to the terms/i).check();
await page.getByRole('button', { name: 'Create account' }).click();

await expect(page).toHaveURL(/\/onboarding/);
await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();
```

Validation tests cover omission, but:
- One missing field per test, not combinatorial coverage.
- A representative sample (email format, password strength, terms unchecked) — not every field.
- Field-level validation is mostly unit/component territory. E2E validates that the product surfaces errors correctly for the **shapes** of failure, not every permutation.

## Assertions

### Shape, not literal value

```ts
// ❌ brittle
await expect(page.getByRole('alert')).toHaveText('Please enter a valid email address.');

// ✅ resilient
await expect(page.getByRole('alert')).toContainText(/valid email/i);
```

### Dynamic values: assert presence or pattern

```ts
// ❌ asserts a specific timestamp
await expect(page.getByTestId('created-at')).toHaveText('Nov 17, 2025 14:32');

// ✅ asserts the shape
await expect(page.getByTestId('created-at')).toHaveText(/\w+ \d{1,2}, \d{4}/);
```

### Web-first assertions only

`expect(locator).toBeVisible()`, `.toHaveURL(regex)`, `.toContainText(...)` all retry automatically. Never pre-wait manually.

```ts
// ❌ double-waiting, and isVisible() doesn't retry
await page.waitForTimeout(1000);
expect(await page.locator('.success').isVisible()).toBe(true);

// ✅
await expect(page.getByRole('status')).toContainText(/saved/i);
```

### Assert the outcome, not the mechanism

A user doesn't know the API was called. They know the toast appeared and the row showed up. Assert the toast and the row. Reach for `page.waitForResponse` only when the UI gives no feedback for something you need to verify.

## Coverage strategy

Test everything a real user can do. Within every flow, also cover:

- **Validation** — submit invalid data and assert the error appears. Not every permutation, but a representative shape.
- **Toasts and feedback** — assert success/error notifications appear after actions and contain the right shape of message.
- **Navigation** — assert the user lands on the right page after an action, that back-navigation works, and that protected routes redirect unauthenticated users.
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

## Flakiness

Flaky tests erode trust faster than missing tests.

1. First assumption on a flake: **the product has a race condition.** Fix the product before the test.
2. Second: the test is waiting on the wrong thing (loadstate instead of a specific response, timeout instead of a visible element). Rewrite the wait.
3. `retries: 1` in CI is acceptable for infrastructure blips, not for gluing broken tests together. A test that needs 3 retries is broken.
4. Never paper over a flake with `waitForTimeout`. Find the actual signal.

## Anti-patterns

```ts
// ❌ Skip to hide a failure
test.skip(Math.random() > 0.5, 'sometimes flaky');
// ✅ Fix the cause or delete the test
```

```ts
// ❌ Branch inside test
if (await page.getByText('Promo banner').isVisible()) {
  await page.getByRole('button', { name: 'Apply' }).click();
}
// ✅ Two tests: "checkout without promo" and "checkout with active promo banner"
```

```ts
// ❌ CSS selector reaching into implementation
await page.locator('div.card > div:nth-child(2) button.primary').click();
// ✅ Role-based, or add a testid
await page
  .getByRole('article', { name: /test cottage/i })
  .getByRole('button', { name: 'Publish' })
  .click();
```

```ts
// ❌ Minimum-viable form fill
await page.getByLabel('Email').fill('a@b.c');
await page.getByLabel('Password').fill('x');
// ✅ Realistic user input
await page.getByLabel('Email').fill(`qa-${crypto.randomUUID()}@example.test`);
await page.getByLabel('Password').fill('CorrectHorseBatteryStaple!1');
```

```ts
// ❌ Sleep-based wait
await page.getByRole('button', { name: 'Save' }).click();
await page.waitForTimeout(2000);
await expect(page.locator('.toast')).toBeVisible();
// ✅ Effect-based
await page.getByRole('button', { name: 'Save' }).click();
await expect(page.getByRole('status')).toContainText(/saved/i);
```

```ts
// ❌ networkidle on a SaaS app with long-poll or websockets
await page.waitForLoadState('networkidle');
// ✅ Wait on the specific thing you care about
await expect(page.getByRole('table')).toBeVisible();
await expect(page.getByRole('row')).toHaveCount(expected);
```

## Config baseline

```ts
export default defineConfig({
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html'], ['list']],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },
  projects: [
    { name: 'chromium', use: devices['Desktop Chrome'] },
    // add webkit/firefox only if you ship there
  ],
});
```

## Mental model

A user:
- Doesn't know the DOM — navigates by roles, labels, visible text.
- Doesn't reload to check — the UI updates.
- Fills realistic values, not minimum placeholders.
- Reads error messages and corrects them.
- Expects feedback within a reasonable latency, not a fixed sleep.

A test is a recording of what that user did, written so that future-you can read it in 30 seconds and know exactly what broke when it fails. If you can't tell from the name and the trace what the user was trying to do — the test is wrong, regardless of whether it is passing today.
