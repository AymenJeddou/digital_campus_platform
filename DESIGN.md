---
name: FSB Nexus
description: Sourced answers about the Faculté des Sciences de Bizerte, in French and Arabic.
colors:
  van-white: "#f4f4f1"
  surface: "#ffffff"
  sunken: "#ebebe6"
  ink: "#16171b"
  ink-2: "#474a52"
  ink-3: "#686c75"
  line: "#d9d9d2"
  line-strong: "#b9bab2"
  louage-red: "#d2272d"
  louage-red-ink: "#a3191e"
  red-wash: "#fbe9e9"
  sodium-amber: "#b97700"
  amber-wash: "#fdf3dc"
  ok: "#1d7a46"
  focus: "#1d4ed8"
  night-asphalt: "#111215"
  night-surface: "#1a1c21"
  night-ink: "#f1f0ec"
  night-red: "#e5484d"
  night-amber: "#ffc14d"
typography:
  display:
    fontFamily: "Lalezar, Rubik, sans-serif"
    fontSize: "clamp(2.4rem, 6.4vw, 4.9rem)"
    fontWeight: 400
    lineHeight: 1
  headline:
    fontFamily: "Lalezar, Rubik, sans-serif"
    fontSize: "clamp(1.8rem, 4vw, 2.8rem)"
    fontWeight: 400
    lineHeight: 1
  title:
    fontFamily: "Rubik, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Rubik, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Rubik, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  stub: "4px"
  sm: "5px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.louage-red}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "44px"
  button-ghost:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "40px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
  placard:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.headline}"
    rounded: "{rounded.md}"
    padding: "12px 14px 10px"
  ticket-stub:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.stub}"
  composer:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "6px 6px 6px 12px"
---

# Design System: FSB Nexus

## Overview

**Creative North Star: "The Louage Station"**

The faculty as the shared-taxi station every Tunisian student knows: you pick your line, say where you're going, and keep your ticket. Each question boards a line (Orientation, Études, Administration, Mes cours) and arrives with its ticket, the source.

The world is carried by three things only: hand-painted bilingual destination placards, the louage-red band, and perforated ticket stubs for sources. Everything else is a plain, fast, friendly chat app. The metaphor never touches the answer text itself.

It refuses the blue SaaS split hero and the neon "AI terminal". It also refuses theme-park overreach: no vans, no road illustrations, no departure-time gimmicks.

**Key Characteristics:**
- Bilingual by construction: placards always show French and Arabic, the interface language first and large.
- One structural colour: louage red, used for the band, primary actions and the active state. Never decorative.
- Sources are objects (ticket stubs) you can open, not footnotes.
- Day station (van white) and night station (asphalt), each designed, neither an inversion.

## Colors

### Primary
- **Louage Red** (#d2272d; night #e5484d): the 5px band at the top of every surface, primary buttons, the pressed placard's bottom bar, the active nav marker, unread counts, the caret and text selection.
- **Deep Louage Red** (#a3191e; night #ff9a9d): red used as text (links, error copy) where the brighter red would fail contrast.

### Secondary
- **Sodium Amber** (#b97700; night #ffc14d): the station-lamp colour. "À vérifier" warnings, course-scope banner wash, calendar items, departures-board column heads.

### Neutral
- **Van White** (#f4f4f1): the page ground (day). Night: **Asphalt** (#111215).
- **Surface** (#ffffff / #1a1c21): cards, inputs, placards, the app rail.
- **Sunken** (#ebebe6 / #0b0c0e): active nav row, auth side panel, code.
- **Ink** (#16171b / #f1f0ec): text, placard borders, user message bubbles, the departures board.
- **Ink 2 / Ink 3**: secondary and tertiary text (≥4.5:1 on their grounds).
- **Line / Line Strong**: hairlines and control borders.

### Named Rules
**The One Red Rule.** Red marks structure and the one action that matters on a screen. If two red buttons compete, one becomes secondary.

**The Lamp Rule.** Amber means "look again" (unverified, scoped, dated). It never decorates.

## Typography

**Display Font:** Lalezar (Arabic + Latin, Google Fonts), the hand-painted signage voice.
**Body Font:** Rubik (Arabic + Latin), a rounded, friendly workhorse.

### Hierarchy
- **Display** (Lalezar 400, clamp(2.4rem, 6.4vw, 4.9rem), 1.0): page heroes only ("Pose ta question…", greetings, page titles).
- **Headline** (Lalezar 400, clamp(1.8rem, 4vw, 2.8rem), 1.0): section titles and placard primaries.
- **Title** (Rubik 600, 1.125rem): section headings inside app pages.
- **Body** (Rubik 400, 15px, 1.65): answers and forms; answers sit in a 48rem column.
- **Label** (Rubik 500, 0.875rem): form labels, nav.

### Named Rules
**The Sign Rule.** Lalezar is for things a station would paint: placards, page titles, the brand. Never for body copy, buttons or labels.

## Layout

App: a 240px rail on desktop (≥1024px); on phones a top bar plus a 5-item bottom tab bar with 44px+ targets. Content columns cap at 64rem (pages) and 48rem (chat). Landing stacks full-width bands: station board → ask form → example answer → dark departures board → honest-refusal → close. All spacing uses logical properties (start/end) so RTL mirrors without overrides.

## Elevation & Depth

Flat, with borders doing the work. One soft lift for interactive placards (`0 6px 14px -8px rgb(0 0 0 / .35)` on hover and pressed) and one for floating layers (popover and dialog: `0 18px 40px -16px rgb(0 0 0 / .4)`). No glass, no blur.

## Shapes

Small, sign-like corners (4–8px). Placards and the composer carry a 2px ink border, the thickest line in the system. Ticket stubs have a semicircular notch on their leading edge (CSS mask), mirrored in RTL.

## Components

### Buttons
- **Shape:** 6px radius, 44px tall (40px ghost).
- **Primary:** louage red with white text; hover brightens, press nudges down 1px.
- **Secondary:** surface with a strong line border; hover darkens the border to ink.
- **Ghost:** text-only for toolbars and toggles.

### Placard
Bilingual destination sign: Lalezar primary line, the other script under it, optional hint. As a button it lifts on hover; pressed shows a red border and a red bar along its bottom edge.

### Ticket stub
Numbered source chip: ink number block, dashed tear line, document name and page. Opens the source passage in a native dialog. Stubs "print in" (a clip-path reveal, 420ms, staggered 70ms), the system's one authored motion; off under reduced motion.

### Inputs / Composer
Surface fill, strong line border, ink border on focus, red caret. The chat composer is a 2px ink-bordered box with an auto-growing textarea and a square send / stop button.

### Navigation
Rail rows with a 3px red marker at the start edge for the current page; bottom tabs use red text for the current tab.

## Do's and Don'ts

- **Do** show both scripts on every placard; **don't** put Arabic only in Arabic mode.
- **Do** keep sources as stubs that open the passage; **don't** render citations as plain footnote text.
- **Don't** add kicker/eyebrow labels above headings, icon-tile feature grids, or hero metrics.
- **Don't** use red for decoration or amber for anything but "look again".
- **Don't** extend the metaphor into answers, errors or forms.
