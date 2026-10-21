# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: game.spec.ts >> gameplay flow >> swipe gestures drive the player on touch devices
- Location: tests/e2e/game.spec.ts:86:3

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 0
Received: 2.033333333333332

Call Log:
- Timeout 5000ms exceeded while waiting on the predicate
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic "Game view" [ref=e2]
  - generic:
    - generic:
      - generic: SCORE
      - generic: "50"
      - generic: 1 BITS · 25 M
    - generic:
      - generic: SECTOR 01
      - generic "Speed"
    - generic:
      - generic: BEST
      - generic: "0"
      - generic:
        - button "Toggle sound (M)" [ref=e3] [cursor=pointer]
        - button "Pause (P)" [ref=e6] [cursor=pointer]
    - generic "Active power-ups"
```

# Test source

```ts
  11  |     await expect(page.locator('#btn-play')).toBeVisible();
  12  |     await expect(page.locator('#hud')).toBeHidden();
  13  |     const s = await pixelStats(page);
  14  |     expect(s.lit).toBeGreaterThan(0.1);
  15  |     expect(s.distinct).toBeGreaterThan(12);
  16  |     expect(errors).toEqual([]);
  17  |   });
  18  | 
  19  |   test('attract-mode demo runs behind the title and never crashes', async ({ page }) => {
  20  |     await openGame(page);
  21  |     const a = await page.evaluate(() => (window as any).__gridrun.demo.distance as number);
  22  |     await page.waitForTimeout(1500);
  23  |     const b = await page.evaluate(() => (window as any).__gridrun.demo.distance as number);
  24  |     expect(b).toBeGreaterThan(a + 5);
  25  |     const st = await page.evaluate(() => (window as any).__gridrun.demo.state as string);
  26  |     expect(st).toBe('playing');
  27  |   });
  28  | 
  29  |   test('has no horizontal scrollbars and the controls legend is listed', async ({ page }) => {
  30  |     await openGame(page);
  31  |     const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  32  |     expect(overflow).toBe(false);
  33  |     await expect(page.getByLabel('Controls')).toContainText('Jump');
  34  |   });
  35  | });
  36  | 
  37  | test.describe('gameplay flow', () => {
  38  |   test('Enter starts: 3-2-1 countdown, then HUD and a running game', async ({ page }) => {
  39  |     const errors = watchErrors(page);
  40  |     await openGame(page);
  41  |     await page.keyboard.press('Enter');
  42  |     await expect(page.locator('#title')).toBeHidden();
  43  |     await expect(page.locator('#countdown')).toBeVisible();
  44  |     expect(await phase(page)).toBe('countdown');
  45  |     await waitForPhase(page, 'playing', 30_000);
  46  |     await expect(page.locator('#hud')).toBeVisible();
  47  |     await expect.poll(async () => (await gameState(page))!.distance, { timeout: 15_000 }).toBeGreaterThan(5);
  48  |     await expect(page.locator('#score')).not.toHaveText('0');
  49  |     expect(errors).toEqual([]);
  50  |   });
  51  | 
  52  |   test('PLAY button works too', async ({ page }) => {
  53  |     await openGame(page);
  54  |     await page.locator('#btn-play').click();
  55  |     await waitForPhase(page, 'playing', 30_000);
  56  |   });
  57  | 
  58  |   test('keyboard: lanes, jump and slide change the player state', async ({ page }) => {
  59  |     await openGame(page);
  60  |     await startRun(page);
  61  |     // freeze obstacles out of the way so inputs can be tested deterministically
  62  |     await page.evaluate(() => {
  63  |       const g = (window as any).__gridrun.game;
  64  |       g.obstacles = [];
  65  |       g.rows = [];
  66  |     });
  67  |     await page.keyboard.press('ArrowLeft');
  68  |     await expect.poll(async () => (await gameState(page))!.lane).toBe(0);
  69  |     await page.keyboard.press('ArrowRight');
  70  |     await page.keyboard.press('ArrowRight');
  71  |     await expect.poll(async () => (await gameState(page))!.lane).toBe(2);
  72  |     await page.keyboard.press('a');
  73  |     await expect.poll(async () => (await gameState(page))!.lane).toBe(1);
  74  |     await page.keyboard.press('d');
  75  |     await expect.poll(async () => (await gameState(page))!.lane).toBe(2);
  76  | 
  77  |     await page.keyboard.press('ArrowUp');
  78  |     await expect.poll(async () => (await gameState(page))!.y, { timeout: 3000 }).toBeGreaterThan(0.3);
  79  |     await expect.poll(async () => (await gameState(page))!.y, { timeout: 5000 }).toBe(0);
  80  |     await page.keyboard.press('ArrowDown');
  81  |     await expect.poll(async () => (await gameState(page))!.sliding, { timeout: 3000 }).toBe(true);
  82  |     await page.keyboard.press('Space');
  83  |     await expect.poll(async () => (await gameState(page))!.y, { timeout: 3000 }).toBeGreaterThan(0.3);
  84  |   });
  85  | 
  86  |   test('swipe gestures drive the player on touch devices', async ({ page }) => {
  87  |     await openGame(page);
  88  |     await startRun(page);
  89  |     await page.evaluate(() => {
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
> 111 |     await expect.poll(async () => (await gameState(page))!.y, { timeout: 5000 }).toBe(0);
      |                                                                                  ^ Error: expect(received).toBe(expected) // Object.is equality
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
  190 |     await page.reload();
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
```