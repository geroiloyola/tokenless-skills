# UI/UX digest (from ui-ux-pro-max)

One file so the agent decides design before writing UI. Replaces the ~75 files of
the upstream `ui-ux-pro-max` skill, which stays available when the searchable
catalog is wanted (§8). Read this file before writing UI code. Source:
nextlevelbuilder/ui-ux-pro-max-skill (SKILL.md + references).

## 1) When it applies
Yes: pages, components, design systems, accessibility, interaction, responsive,
typography, color, graphics, per-stack implementation.
No: pure backend, APIs, DB, infra, non-visual scripts.

## 2) Priority (1 = first)
| # | Category | Impact | Checks | Anti-patterns |
|---|---|---|---|---|
| 1 | Accessibility | CRITICAL | contrast 4.5:1, alt, keyboard, aria-label | remove focus ring, icon-only button without name |
| 2 | Touch & interaction | CRITICAL | >=44x44px, >=8px gap, loading feedback | relying on hover, 0ms state changes |
| 3 | Performance | HIGH | WebP/AVIF, lazy load, reserve space (CLS<0.1) | layout thrashing |
| 4 | Style selection | HIGH | coherence with product, SVG icons | mixing flat and skeuomorphic, emoji as icons |
| 5 | Layout & responsive | HIGH | mobile-first, meta viewport, no horizontal scroll | fixed px widths, disable zoom |
| 6 | Typography & color | MEDIUM | base 16px, line-height 1.5, semantic tokens | text <12px, gray-on-gray, raw hex in components |
| 7 | Animation | MEDIUM | timing per context, meaningful motion, reduced-motion | one duration for everything, animating width/height |
| 8 | Forms & feedback | MEDIUM | visible label, error next to field, helper text | placeholder as label, errors only at top |
| 9 | Navigation | HIGH | predictable back, bottom nav <=5, deep links | overloaded nav, broken back |
| 10 | Graphics & data | LOW | legends, tooltips, accessible colors | color as the only meaning carrier |

## 3) Choosing a direction (before coding)
1. Extract from the request: product type (SaaS, e-commerce, portfolio, dashboard,
   tool, content-first), audience, usage context.
2. Pick **one** aesthetic direction and write it down: reference, mood, density.
   "Modern with purple gradients" is not a direction; it is the absence of a decision.
3. Detect the stack, never assume it: `package.json` (react/next/vue/svelte),
   `pubspec.yaml` (Flutter), `Package.swift` (SwiftUI), `composer.json` (Laravel),
   `app.json` for react-native. If undetectable and it matters, ask.
4. Tokens before components.
5. If the upstream skill is installed, query §8 before inventing.

## 4) Minimum token set (copy and derive)
```
bg / surface / surface-2        # 3 levels, measurable contrast between them
text / text-muted / text-inverse
accent / accent-hover / on-accent
danger / success / warning / info
border / focus-ring
space: 4 8 12 16 24 32 48 64    # 4/8 scale
radius: 4 8 12 16 full
type: 12 14 16 20 24 32 40 56   # modular; body 16, line-height 1.5
shadow: sm md lg (<=3 levels)   # dark mode: use border + surface, not shadows
motion: fast 150ms / base 200ms / slow 300ms, ease-out in, ease-in out
```
Rules: one accent per view; color is never the only meaning carrier; dark mode is
designed, not inverted; zero raw hex in components.

## 5) Style families (pick one)
Minimal / Swiss · Editorial / Magazine · Brutalist · Neumorphic (contrast care) ·
Glass / Blur (legibility care) · Material 3 · Fluent · Neo-brutalism · Retro
terminal · Data-dense / Dashboard · Luxury / Serif · Playful / Illustrated ·
Bento grid · Claymorphism · Soft neumorphism · Corporate clean · Brutal-web ·
Dark-first productivity · Content-first reading.

## 6) Seed palettes (adjust contrast)
| Type | Suggested hex |
|---|---|
| SaaS productivity | #0F172A #1E293B #38BDF8 #F8FAFC |
| Fintech / trust | #0B1F3A #13315C #2DD4BF #F1F5F9 |
| Warm e-commerce | #1C1917 #292524 #F97316 #FAFAF9 |
| Health / calm | #0F3D3E #14532D #34D399 #F0FDF4 |
| Editorial | #FAF9F6 #111111 #B91C1C #6B7280 |
| Dark dashboard | #0A0A0B #17171A #A3E635 #E5E7EB |
| Playful / kids | #312E81 #4338CA #FBBF24 #FFF7ED |
Always pair with a real contrast verification (§2.1).

## 7) Typography pairings
| Role | Sans (UI) | Display (headings) | Mono (data) |
|---|---|---|---|
| Neutral product | Inter, Geist, Public Sans | same, 600-700 | JetBrains Mono, Geist Mono |
| Editorial | Source Sans 3 | Fraunces, Playfair, Lora | IBM Plex Mono |
| Technical | IBM Plex Sans | Space Grotesk | IBM Plex Mono |
| Warm / brand | Nunito Sans | Bricolage Grotesque | DM Mono |
| Data-dense | Roboto Flex | Inter Tight | Roboto Mono |
Rule: max 2 families + 1 mono; modular scale (1.125 or 1.25), no loose sizes.

## 8) Searchable (upstream repo)
Optional upstream tooling — `ui-ux-pro-max-cli` and its `search.py` are NOT
part of this kit. If the install below fails or the tool is absent, skip this
section, mark the searchable catalog as unavailable, and audit with the
digest above plus `contrast.mjs`.
If you need the full catalog (80 styles, 192 reasoned palettes, 74 pairings, 120
UX rules, 105 icons, 17 GSAP presets, 25 chart types, 22 stacks):
```bash
npm i -g ui-ux-pro-max-cli && uipro init --ai universal --global   # ~/.agents/skills/
python <skill-dir>/scripts/search.py "<query>" --domain ux|style|color|typography|product|icons|chart|gsap|stack
python <skill-dir>/scripts/search.py --design-system "<product>"
```
Query contract: one dominant intent, 2-5 terms, one constraint. Verify the result
against the product; if empty or off-topic, retry once with narrower terms; if it
fails, say so and mark the guide as fallback. Do not persist unverified results.
RTL: add `--rtl` and respect `rtl_level` (full/partial/caveats).

## 9) Pre-delivery checklist
- [ ] contrast >=4.5:1 text, >=3:1 components/icons
- [ ] visible focus, keyboard navigable
- [ ] 375px and 1440px without horizontal scroll or clipped text
- [ ] states: loading, empty, error, disabled, hover, focus
- [ ] forms: visible label, error next to field, focus on first error
- [ ] images with alt, SVG icons from one family
- [ ] reduced-motion respected, no width/height animation
- [ ] real copy, realistic data, no lorem ipsum
- [ ] a single accent, consistent tokens, zero loose hex
- [ ] dark mode reviewed if it exists

## 10) Anti-patterns that betray "made by AI"
Default purple gradients · three different shadows · emoji as icons ·
`text-gray-400` on white · everything centered without hierarchy · 1px light-gray
border as only separation · hover scale 1.05 everywhere · lorem ipsum ·
gray placeholders as label · components shipped without an empty state.
