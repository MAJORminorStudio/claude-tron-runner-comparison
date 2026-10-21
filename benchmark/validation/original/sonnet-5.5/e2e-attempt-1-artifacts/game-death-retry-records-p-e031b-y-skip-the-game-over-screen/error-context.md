# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: game.spec.ts >> death, retry, records >> pressing Enter right after a crash cannot instantly skip the game over screen
- Location: tests/e2e/game.spec.ts:205:3

# Error details

```
Error: Test timeout of 60000ms exceeded
```

# Test source

```ts
  1   | import { expect, type Page } from '@playwright/test';
  2   | import { PNG } from 'pngjs';
  3   | 
  4   | /** Collect console errors and uncaught exceptions for the whole test. */
  5   | export function watchErrors(page: Page): string[] {
  6   |   const errors: string[] = [];
  7   |   page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
  8   |   page.on('console', (m) => {
  9   |     if (m.type() === 'error') errors.push(`console.error: ${m.text()}`);
  10  |   });
  11  |   page.on('requestfailed', (r) => errors.push(`requestfailed: ${r.url()}`));
  12  |   page.on('response', (r) => {
  13  |     if (r.status() >= 400) errors.push(`http ${r.status()}: ${r.url()}`);
  14  |   });
  15  |   return errors;
  16  | }
  17  | 
  18  | /** Use low graphics so software-rendered CI frames stay fast (unless a test overrides). */
  19  | export async function openGame(page: Page, query = 'seed=7', quality: 'low' | 'high' = 'low'): Promise<void> {
  20  |   await page.addInitScript((q) => {
  21  |     try {
  22  |       if (!localStorage.getItem('gridrun.quality')) localStorage.setItem('gridrun.quality', JSON.stringify(q));
  23  |     } catch {
  24  |       /* ignore */
  25  |     }
  26  |   }, quality);
  27  |   await page.goto(`/?debug&${query}`);
  28  |   await expect(page.locator('#title')).toBeVisible();
  29  | }
  30  | 
  31  | export const phase = (page: Page): Promise<string> => page.evaluate(() => (window as any).__gridrun.phase as string);
  32  | 
  33  | export async function waitForPhase(page: Page, want: string, timeout = 20_000): Promise<void> {
> 34  |   await expect.poll(() => phase(page), { timeout }).toBe(want);
      |                                                     ^ Error: Test timeout of 60000ms exceeded
  35  | }
  36  | 
  37  | export async function startRun(page: Page): Promise<void> {
  38  |   await page.keyboard.press('Enter');
  39  |   await waitForPhase(page, 'playing', 30_000);
  40  | }
  41  | 
  42  | export const gameState = (page: Page) =>
  43  |   page.evaluate(() => {
  44  |     const g = (window as any).__gridrun.game;
  45  |     return g
  46  |       ? {
  47  |           state: g.state as string,
  48  |           distance: g.distance as number,
  49  |           score: g.score as number,
  50  |           bits: g.bits as number,
  51  |           lane: g.player.lane as number,
  52  |           y: g.player.y as number,
  53  |           sliding: g.player.sliding as boolean,
  54  |           speed: g.speed as number,
  55  |           time: g.time as number,
  56  |         }
  57  |       : null;
  58  |   });
  59  | 
  60  | export interface PixelStats {
  61  |   width: number;
  62  |   height: number;
  63  |   /** fraction of pixels that are not near-black */
  64  |   lit: number;
  65  |   cyan: number;
  66  |   orange: number;
  67  |   /** distinct coarse colours: crude "is something interesting on screen" metric */
  68  |   distinct: number;
  69  | }
  70  | 
  71  | export interface Crop {
  72  |   x0: number;
  73  |   y0: number;
  74  |   x1: number;
  75  |   y1: number;
  76  | }
  77  | 
  78  | /** Colour statistics of the current frame, optionally of a sub-rectangle given in 0..1 fractions. */
  79  | export async function pixelStats(page: Page, crop: Crop = { x0: 0, y0: 0, x1: 1, y1: 1 }): Promise<PixelStats> {
  80  |   const buf = await page.screenshot();
  81  |   const png = PNG.sync.read(buf);
  82  |   let lit = 0;
  83  |   let cyan = 0;
  84  |   let orange = 0;
  85  |   const seen = new Set<number>();
  86  |   const xa = Math.floor(crop.x0 * png.width);
  87  |   const xb = Math.floor(crop.x1 * png.width);
  88  |   const ya = Math.floor(crop.y0 * png.height);
  89  |   const yb = Math.floor(crop.y1 * png.height);
  90  |   const total = Math.max(1, (xb - xa) * (yb - ya));
  91  |   for (let y = ya; y < yb; y++) {
  92  |     for (let x = xa; x < xb; x++) {
  93  |       const i = (y * png.width + x) * 4;
  94  |       const r = png.data[i]!;
  95  |       const g = png.data[i + 1]!;
  96  |       const b = png.data[i + 2]!;
  97  |       if (r + g + b > 60) lit++;
  98  |       if (b > 170 && g > 170 && r < 140) cyan++;
  99  |       if (r > 190 && g > 60 && g < 200 && b < 100) orange++;
  100 |       seen.add(((r >> 5) << 6) | ((g >> 5) << 3) | (b >> 5));
  101 |     }
  102 |   }
  103 |   return { width: png.width, height: png.height, lit: lit / total, cyan: cyan / total, orange: orange / total, distinct: seen.size };
  104 | }
  105 | 
  106 | /** Let a bunch of real frames render. */
  107 | export const frames = (page: Page, n = 4): Promise<void> =>
  108 |   page.evaluate(
  109 |     (count) =>
  110 |       new Promise<void>((resolve) => {
  111 |         let i = 0;
  112 |         const f = (): void => {
  113 |           if (++i >= count) resolve();
  114 |           else requestAnimationFrame(f);
  115 |         };
  116 |         requestAnimationFrame(f);
  117 |       }),
  118 |     n,
  119 |   );
  120 | 
```