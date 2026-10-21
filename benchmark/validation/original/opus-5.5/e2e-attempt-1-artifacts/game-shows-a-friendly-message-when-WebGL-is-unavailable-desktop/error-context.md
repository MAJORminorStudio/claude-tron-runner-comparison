# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: game.spec.js >> shows a friendly message when WebGL is unavailable
- Location: tests/e2e/game.spec.js:163:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:4173/
Call log:
  - navigating to "http://localhost:4173/", waiting until "load"

```

# Test source

```ts
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
  122 |   await page.evaluate(() => window.dispatchEvent(new Event('blur')));
  123 |   await expect(page.getByTestId('paused')).toBeVisible();
  124 | });
  125 | 
  126 | test('crashing shows results, saves the best score and allows a retry', async ({ page }) => {
  127 |   const errors = trackErrors(page);
  128 |   await boot(page, `?seed=${FAST_CRASH}`);
  129 |   await startRun(page);
  130 |   await expect(page.getByTestId('gameover')).toBeVisible({ timeout: 15_000 });
  131 |   const finalScore = await page.getByTestId('final-score').textContent();
  132 |   expect(Number(finalScore.replace(/,/g, ''))).toBeGreaterThan(0);
  133 |   await expect(page.locator('#final-best')).toHaveText(finalScore);
  134 | 
  135 |   await page.getByTestId('retry').click();
  136 |   await page.waitForFunction(() => window.__gridRunner.phase === 'playing');
  137 |   await expect(page.getByTestId('gameover')).toBeHidden();
  138 | 
  139 |   await page.reload();
  140 |   await expect(page.locator('#best-title')).toHaveText(finalScore);
  141 |   expect(errors).toEqual([]);
  142 | });
  143 | 
  144 | test('menu button returns to the title screen', async ({ page }) => {
  145 |   await boot(page, `?seed=${FAST_CRASH}`);
  146 |   await startRun(page);
  147 |   await expect(page.getByTestId('gameover')).toBeVisible({ timeout: 15_000 });
  148 |   await page.getByRole('button', { name: 'Menu' }).click();
  149 |   await expect(page.getByTestId('title')).toBeVisible();
  150 |   await page.waitForFunction(() => window.__gridRunner.phase === 'title');
  151 | });
  152 | 
  153 | test('mute toggle persists across reloads', async ({ page }) => {
  154 |   await boot(page);
  155 |   const btn = page.locator('#btn-mute');
  156 |   await expect(btn).toHaveAttribute('aria-pressed', 'false');
  157 |   await btn.click();
  158 |   await expect(btn).toHaveAttribute('aria-pressed', 'true');
  159 |   await page.reload();
  160 |   await expect(page.locator('#btn-mute')).toHaveAttribute('aria-pressed', 'true');
  161 | });
  162 | 
  163 | test('shows a friendly message when WebGL is unavailable', async ({ page }) => {
  164 |   await page.addInitScript(() => {
  165 |     const orig = HTMLCanvasElement.prototype.getContext;
  166 |     HTMLCanvasElement.prototype.getContext = function (type, ...rest) {
  167 |       if (String(type).startsWith('webgl')) return null;
  168 |       return orig.call(this, type, ...rest);
  169 |     };
  170 |   });
> 171 |   await page.goto('/');
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:4173/
  172 |   await expect(page.getByText('Grid offline')).toBeVisible();
  173 |   await expect(page.getByTestId('title')).toBeHidden();
  174 | });
  175 | 
  176 | test('works without localStorage', async ({ page }) => {
  177 |   const errors = trackErrors(page);
  178 |   await page.addInitScript(() => {
  179 |     Object.defineProperty(window, 'localStorage', {
  180 |       get() {
  181 |         throw new Error('blocked');
  182 |       },
  183 |     });
  184 |   });
  185 |   await boot(page, `?seed=${FAST_CRASH}`);
  186 |   await startRun(page);
  187 |   await expect(page.getByTestId('gameover')).toBeVisible({ timeout: 15_000 });
  188 |   expect(errors).toEqual([]);
  189 | });
  190 | 
```