# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: game.spec.js >> crashing shows results, saves the best score and allows a retry
- Location: tests/e2e/game.spec.js:126:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:4173/?seed=3
Call log:
  - navigating to "http://localhost:4173/?seed=3", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | // Seeds chosen from the deterministic generator:
  4   | //  - FAST_CRASH: an idle player hits the first obstacle row after ~3s.
  5   | //  - SLOW_CRASH: an idle player survives ~7s, leaving time to test controls.
  6   | const FAST_CRASH = 3;
  7   | const SLOW_CRASH = 35;
  8   | 
  9   | const snapshot = (page) => page.evaluate(() => window.__gridRunner.snapshot());
  10  | 
  11  | function trackErrors(page) {
  12  |   const errors = [];
  13  |   page.on('pageerror', (err) => errors.push(err.message));
  14  |   page.on('console', (msg) => {
  15  |     if (msg.type() === 'error') errors.push(msg.text());
  16  |   });
  17  |   return errors;
  18  | }
  19  | 
  20  | async function boot(page, query = '') {
> 21  |   await page.goto(`/${query}`);
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:4173/?seed=3
  22  |   await expect(page.getByTestId('title')).toBeVisible();
  23  |   await page.waitForFunction(() => window.__gridRunner?.phase === 'title');
  24  | }
  25  | 
  26  | async function startRun(page) {
  27  |   await page.getByTestId('start').click();
  28  |   await page.waitForFunction(() => window.__gridRunner.phase === 'playing');
  29  | }
  30  | 
  31  | test('boots to the title screen with a running attract demo and no errors', async ({ page }) => {
  32  |   const errors = trackErrors(page);
  33  |   await boot(page);
  34  |   await expect(page).toHaveTitle('GRID RUNNER');
  35  |   await expect(page.locator('h1')).toContainText('GRID');
  36  |   const a = await snapshot(page);
  37  |   // the attract demo keeps running behind the menu
  38  |   await expect.poll(async () => (await snapshot(page)).distance).toBeGreaterThan(a.distance);
  39  |   const hasGl = await page.evaluate(() => {
  40  |     const c = document.getElementById('game');
  41  |     return c.width > 0 && c.height > 0;
  42  |   });
  43  |   expect(hasGl).toBe(true);
  44  |   await expect(page.locator('#hud')).toBeHidden();
  45  |   expect(errors).toEqual([]);
  46  | });
  47  | 
  48  | test('starting a run shows the HUD and the score climbs', async ({ page }) => {
  49  |   const errors = trackErrors(page);
  50  |   await boot(page, `?seed=${SLOW_CRASH}`);
  51  |   await startRun(page);
  52  |   await expect(page.locator('#hud')).toBeVisible();
  53  |   await expect(page.getByTestId('title')).toBeHidden();
  54  |   await expect.poll(async () => (await snapshot(page)).score).toBeGreaterThan(0);
  55  |   expect((await snapshot(page)).seed).toBe(SLOW_CRASH);
  56  |   await expect(page.getByTestId('score')).not.toHaveText('0');
  57  |   expect(errors).toEqual([]);
  58  | });
  59  | 
  60  | test('keyboard controls: lanes, jump and slide', async ({ page, isMobile }) => {
  61  |   test.skip(isMobile, 'keyboard test runs on desktop');
  62  |   await boot(page, `?seed=${SLOW_CRASH}`);
  63  |   await page.keyboard.press('Enter');
  64  |   await page.waitForFunction(() => window.__gridRunner.phase === 'playing');
  65  | 
  66  |   await page.keyboard.press('ArrowLeft');
  67  |   await expect.poll(async () => (await snapshot(page)).lane).toBe(0);
  68  |   await page.keyboard.press('ArrowLeft'); // already at the edge
  69  |   await expect.poll(async () => (await snapshot(page)).lane).toBe(0);
  70  |   await page.keyboard.press('KeyD');
  71  |   await page.keyboard.press('ArrowRight');
  72  |   await expect.poll(async () => (await snapshot(page)).lane).toBe(2);
  73  | 
  74  |   await page.keyboard.press('ArrowUp');
  75  |   await expect.poll(async () => (await snapshot(page)).y).toBeGreaterThan(0.3);
  76  |   await expect.poll(async () => (await snapshot(page)).y).toBe(0);
  77  | 
  78  |   await page.keyboard.press('ArrowDown');
  79  |   await expect.poll(async () => (await snapshot(page)).sliding).toBe(true);
  80  | });
  81  | 
  82  | test('swipe controls work with pointer drags', async ({ page }) => {
  83  |   await boot(page, `?seed=${SLOW_CRASH}`);
  84  |   await startRun(page);
  85  |   const vp = page.viewportSize();
  86  |   const cx = vp.width / 2;
  87  |   const cy = vp.height / 2;
  88  |   const swipe = async (dx, dy) => {
  89  |     await page.mouse.move(cx, cy);
  90  |     await page.mouse.down();
  91  |     await page.mouse.move(cx + dx / 2, cy + dy / 2, { steps: 2 });
  92  |     await page.mouse.move(cx + dx, cy + dy, { steps: 2 });
  93  |     await page.mouse.up();
  94  |   };
  95  |   await swipe(120, 0);
  96  |   await expect.poll(async () => (await snapshot(page)).lane).toBe(2);
  97  |   await swipe(-120, 0);
  98  |   await expect.poll(async () => (await snapshot(page)).lane).toBe(1);
  99  |   await swipe(0, -120);
  100 |   await expect.poll(async () => (await snapshot(page)).y).toBeGreaterThan(0.3);
  101 | });
  102 | 
  103 | test('pause freezes the run and resume continues it', async ({ page }) => {
  104 |   await boot(page, `?seed=${SLOW_CRASH}`);
  105 |   await startRun(page);
  106 |   await page.waitForTimeout(300);
  107 |   await page.locator('#btn-pause').click();
  108 |   await expect(page.getByTestId('paused')).toBeVisible();
  109 |   const a = await snapshot(page);
  110 |   await page.waitForTimeout(500);
  111 |   const b = await snapshot(page);
  112 |   expect(b.distance).toBe(a.distance);
  113 |   expect(b.phase).toBe('paused');
  114 |   await page.getByRole('button', { name: 'Resume' }).click();
  115 |   await expect(page.getByTestId('paused')).toBeHidden();
  116 |   await expect.poll(async () => (await snapshot(page)).distance).toBeGreaterThan(b.distance);
  117 | });
  118 | 
  119 | test('losing focus auto-pauses', async ({ page }) => {
  120 |   await boot(page, `?seed=${SLOW_CRASH}`);
  121 |   await startRun(page);
```