# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: game.spec.ts >> death, retry, records >> retry via Enter starts a fresh run immediately; best score persists across reload
- Location: tests/e2e/game.spec.ts:176:3

# Error details

```
Test timeout of 60000ms exceeded.
```

```
Error: page.reload: Test timeout of 60000ms exceeded.
Call log:
  - waiting for navigation until "load"
    - navigated to "http://<REDACTED_IP>:4173/?debug&seed=7"

```

# Test source

```ts
  90  |       const g = (window as any).__gridrun.game;
  91  |       g.obstacles = [];
  92  |       g.rows = [];
  93  |     });
  94  |     const swipe = (dx: number, dy: number) =>
  95  |       page.evaluate(
  96  |         ({ dx, dy }) => {
  97  |           const c = document.getElementById('scene')!;
  98  |           const opts = (x: number, y: number) => ({ pointerId: 3, pointerType: 'touch', clientX: x, clientY: y, bubbles: true, isPrimary: true });
  99  |           c.dispatchEvent(new PointerEvent('pointerdown', opts(300, 300)));
  100 |           c.dispatchEvent(new PointerEvent('pointermove', opts(300 + dx, 300 + dy)));
  101 |           c.dispatchEvent(new PointerEvent('pointerup', opts(300 + dx, 300 + dy)));
  102 |         },
  103 |         { dx, dy },
  104 |       );
  105 |     await swipe(-80, 5);
  106 |     await expect.poll(async () => (await gameState(page))!.lane).toBe(0);
  107 |     await swipe(80, -4);
  108 |     await expect.poll(async () => (await gameState(page))!.lane).toBe(1);
  109 |     await swipe(2, -90);
  110 |     await expect.poll(async () => (await gameState(page))!.y, { timeout: 3000 }).toBeGreaterThan(0.3);
  111 |     await expect.poll(async () => (await gameState(page))!.y, { timeout: 5000 }).toBe(0);
  112 |     await swipe(0, 90);
  113 |     await expect.poll(async () => (await gameState(page))!.sliding, { timeout: 3000 }).toBe(true);
  114 |   });
  115 | 
  116 |   test('autopilot survives and collects bits through the real render loop', async ({ page }) => {
  117 |     const errors = watchErrors(page);
  118 |     await openGame(page, 'seed=21');
  119 |     await startRun(page);
  120 |     await page.evaluate(() => (window as any).__gridrun.setAutopilot(true));
  121 |     await page.evaluate(() => (window as any).__gridrun.advance(45));
  122 |     await frames(page, 5);
  123 |     const s = (await gameState(page))!;
  124 |     expect(s.state).toBe('playing');
  125 |     expect(s.time).toBeGreaterThan(44);
  126 |     expect(s.bits).toBeGreaterThan(20);
  127 |     expect(s.score).toBeGreaterThan(1500);
  128 |     const stats = await pixelStats(page);
  129 |     expect(stats.lit).toBeGreaterThan(0.1);
  130 |     expect(errors).toEqual([]);
  131 |   });
  132 | 
  133 |   test('hazards appear on the track as orange; player and grid as cyan', async ({ page }) => {
  134 |     await openGame(page, 'seed=21');
  135 |     await startRun(page);
  136 |     const centre = { x0: 0.38, y0: 0.3, x1: 0.62, y1: 0.6 };
  137 |     await page.evaluate(() => {
  138 |       const g = (window as any).__gridrun.game;
  139 |       g.pause(); // freeze the world so the frame is stable
  140 |       g.obstacles = [];
  141 |       g.pickups = [];
  142 |     });
  143 |     await frames(page, 6);
  144 |     const empty = await pixelStats(page, centre);
  145 |     expect(empty.orange).toBeLessThan(0.0005);
  146 |     expect((await pixelStats(page)).cyan).toBeGreaterThan(0.002);
  147 |     await page.evaluate(() => {
  148 |       const g = (window as any).__gridrun.game;
  149 |       g.addObstacle('block', 1, g.distance + 14);
  150 |       g.addObstacle('low', 0, g.distance + 14);
  151 |       g.addObstacle('high', 2, g.distance + 14);
  152 |     });
  153 |     await frames(page, 6);
  154 |     const withHazards = await pixelStats(page, centre);
  155 |     expect(withHazards.orange).toBeGreaterThan(0.002);
  156 |     expect(withHazards.orange).toBeGreaterThan(empty.orange * 5);
  157 |   });
  158 | });
  159 | 
  160 | test.describe('death, retry, records', () => {
  161 |   test('standing still crashes into an obstacle -> game over screen with stats', async ({ page }) => {
  162 |     const errors = watchErrors(page);
  163 |     await openGame(page);
  164 |     await startRun(page);
  165 |     await page.evaluate(() => (window as any).__gridrun.advance(120));
  166 |     await waitForPhase(page, 'over', 15_000);
  167 |     await expect(page.locator('#over')).toBeVisible({ timeout: 10_000 });
  168 |     await expect(page.locator('#over')).toContainText('CONNECTION LOST');
  169 |     const score = Number((await page.locator('#f-score').textContent())!.replace(/,/g, ''));
  170 |     expect(score).toBeGreaterThan(0);
  171 |     await expect(page.locator('#f-dist')).toContainText('M');
  172 |     await expect(page.locator('#hud')).toBeHidden();
  173 |     expect(errors).toEqual([]);
  174 |   });
  175 | 
  176 |   test('retry via Enter starts a fresh run immediately; best score persists across reload', async ({ page }) => {
  177 |     await openGame(page);
  178 |     await startRun(page);
  179 |     await page.evaluate(() => (window as any).__gridrun.advance(120));
  180 |     await expect(page.locator('#over')).toBeVisible({ timeout: 15_000 });
  181 |     const best = await page.evaluate(() => (window as any).__gridrun.records.bestScore as number);
  182 |     expect(best).toBeGreaterThan(0);
  183 |     await page.waitForTimeout(400);
  184 |     await page.keyboard.press('Enter');
  185 |     await waitForPhase(page, 'playing', 5_000);
  186 |     const s = (await gameState(page))!;
  187 |     expect(s.score).toBeLessThan(200);
  188 |     expect(s.state).toBe('playing');
  189 | 
> 190 |     await page.reload();
      |                ^ Error: page.reload: Test timeout of 60000ms exceeded.
  191 |     await expect(page.locator('#records')).toContainText(String(best.toLocaleString('en-US')));
  192 |     await expect(page.locator('#records')).toContainText('RUNS');
  193 |   });
  194 | 
  195 |   test('menu button returns to the title and the demo resumes', async ({ page }) => {
  196 |     await openGame(page);
  197 |     await startRun(page);
  198 |     await page.evaluate(() => (window as any).__gridrun.advance(120));
  199 |     await expect(page.locator('#over')).toBeVisible({ timeout: 15_000 });
  200 |     await page.locator('#btn-menu').click();
  201 |     await expect(page.locator('#title')).toBeVisible();
  202 |     expect(await phase(page)).toBe('title');
  203 |   });
  204 | 
  205 |   test('pressing Enter right after a crash cannot instantly skip the game over screen', async ({ page }) => {
  206 |     await openGame(page);
  207 |     await startRun(page);
  208 |     await page.evaluate(() => (window as any).__gridrun.advance(120));
  209 |     await waitForPhase(page, 'over');
  210 |     await page.keyboard.press('Enter');
  211 |     expect(await phase(page)).toBe('over');
  212 |   });
  213 | });
  214 | 
  215 | test.describe('pause, sound, quality', () => {
  216 |   test('P pauses the world, resume counts down and continues', async ({ page }) => {
  217 |     await openGame(page);
  218 |     await startRun(page);
  219 |     await page.evaluate(() => (window as any).__gridrun.setAutopilot(true));
  220 |     await page.keyboard.press('p');
  221 |     await expect(page.locator('#pause')).toBeVisible();
  222 |     expect(await phase(page)).toBe('paused');
  223 |     const a = (await gameState(page))!;
  224 |     await page.waitForTimeout(900);
  225 |     const b = (await gameState(page))!;
  226 |     expect(b.distance).toBe(a.distance);
  227 |     expect(b.state).toBe('paused');
  228 |     await page.keyboard.press('Enter'); // confirm = resume
  229 |     expect(await phase(page)).toBe('countdown');
  230 |     await waitForPhase(page, 'playing', 30_000);
  231 |     await expect.poll(async () => (await gameState(page))!.distance, { timeout: 15_000 }).toBeGreaterThan(a.distance + 3);
  232 |   });
  233 | 
  234 |   test('Escape pauses and the RESUME / RESTART / QUIT buttons work', async ({ page }) => {
  235 |     await openGame(page);
  236 |     await startRun(page);
  237 |     await page.keyboard.press('Escape');
  238 |     await expect(page.locator('#pause')).toBeVisible();
  239 |     await page.locator('#btn-resume').click();
  240 |     await waitForPhase(page, 'playing', 30_000);
  241 |     await page.locator('#btn-pause').click();
  242 |     await expect(page.locator('#pause')).toBeVisible();
  243 |     await page.locator('#btn-restart').click();
  244 |     await waitForPhase(page, 'playing', 5_000);
  245 |     expect((await gameState(page))!.time).toBeLessThan(2);
  246 |     await page.keyboard.press('Escape');
  247 |     await page.locator('#btn-quit').click();
  248 |     await expect(page.locator('#title')).toBeVisible();
  249 |   });
  250 | 
  251 |   test('hiding the tab auto-pauses', async ({ page }) => {
  252 |     await openGame(page);
  253 |     await startRun(page);
  254 |     await page.evaluate(() => {
  255 |       Object.defineProperty(document, 'hidden', { value: true, configurable: true });
  256 |       document.dispatchEvent(new Event('visibilitychange'));
  257 |     });
  258 |     expect(await phase(page)).toBe('paused');
  259 |   });
  260 | 
  261 |   test('sound toggle (M key and button) persists across reloads', async ({ page }) => {
  262 |     await openGame(page);
  263 |     expect(await page.evaluate(() => (window as any).__gridrun.muted)).toBe(false);
  264 |     await page.keyboard.press('m');
  265 |     expect(await page.evaluate(() => (window as any).__gridrun.muted)).toBe(true);
  266 |     await expect(page.locator('#tgl-sound')).toHaveText('SOUND: OFF');
  267 |     await page.reload();
  268 |     expect(await page.evaluate(() => (window as any).__gridrun.muted)).toBe(true);
  269 |     await page.locator('#tgl-sound').click();
  270 |     expect(await page.evaluate(() => (window as any).__gridrun.muted)).toBe(false);
  271 |   });
  272 | 
  273 |   test('graphics toggle switches between high and low and still renders', async ({ page }) => {
  274 |     const errors = watchErrors(page);
  275 |     await openGame(page, 'seed=7', 'high');
  276 |     expect(await page.evaluate(() => (window as any).__gridrun.quality)).toBe('high');
  277 |     await frames(page, 4);
  278 |     const high = await pixelStats(page);
  279 |     expect(high.lit).toBeGreaterThan(0.1);
  280 |     await page.keyboard.press('g');
  281 |     expect(await page.evaluate(() => (window as any).__gridrun.quality)).toBe('low');
  282 |     await frames(page, 4);
  283 |     const low = await pixelStats(page);
  284 |     expect(low.lit).toBeGreaterThan(0.1);
  285 |     expect(errors).toEqual([]);
  286 |   });
  287 | });
  288 | 
  289 | test.describe('audio & render budget', () => {
  290 |   test('audio context starts on the first user gesture without errors', async ({ page }) => {
```