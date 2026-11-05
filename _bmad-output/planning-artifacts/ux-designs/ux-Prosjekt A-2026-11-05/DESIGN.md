---
name: AI Study Buddy
description: Calm, clear study app that turns a student's own course material into active self-testing. Light surfaces, one quiet blue accent, light and dark themes. Tokens are system-agnostic until architecture picks a UI library.
status: final
updated: 2026-11-05
colors:
  # Light theme. Every color token has a -dark twin below; components name the light token,
  # and the dark theme resolves each reference to its -dark twin.
  canvas: '#F5F6F8'
  surface: '#FFFFFF'
  surface-muted: '#EEF0F3'
  ink: '#1D1F24'
  ink-secondary: '#5A606C'
  ink-disabled: '#A3A8B2'
  hairline: '#E1E4E9'
  border-strong: '#80868F'
  accent: '#2C6BDB'
  accent-strong: '#2357B8'
  accent-soft: '#E8F0FD'
  on-accent: '#FFFFFF'
  focus-ring: '#2C6BDB'
  success: '#1E7A4C'
  success-soft: '#E6F4EC'
  warning: '#8A5800'
  warning-soft: '#FFF2D5'
  danger: '#B3362D'
  danger-soft: '#FCEBE9'
  course-1: '#DCE8FF'
  course-2: '#DCF2E3'
  course-3: '#E8E2FA'
  course-4: '#FDE6D3'
  course-5: '#FADDE6'
  course-6: '#D8F0EF'
  # Dark theme
  canvas-dark: '#111215'
  surface-dark: '#1A1C20'
  surface-muted-dark: '#24262B'
  ink-dark: '#F1F2F4'
  ink-secondary-dark: '#A5AAB4'
  ink-disabled-dark: '#5D626C'
  hairline-dark: '#2E3137'
  border-strong-dark: '#6E7480'
  accent-dark: '#74A3FF'
  accent-strong-dark: '#9BBCFF'
  accent-soft-dark: '#1C2A44'
  on-accent-dark: '#0B1426'
  focus-ring-dark: '#74A3FF'
  success-dark: '#57C994'
  success-soft-dark: '#13291D'
  warning-dark: '#F1B95A'
  warning-soft-dark: '#2E2513'
  danger-dark: '#FF8077'
  danger-soft-dark: '#301B1A'
  course-1-dark: '#22324F'
  course-2-dark: '#1E3829'
  course-3-dark: '#2D2747'
  course-4-dark: '#3F2E1F'
  course-5-dark: '#3F2430'
  course-6-dark: '#1D3A3A'
typography:
  display:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-mobile:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.15'
    letterSpacing: -0.015em
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 21px
    fontWeight: '600'
    lineHeight: '1.3'
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 17px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.45'
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 15px
    fontWeight: '600'
    lineHeight: '1.2'
  label-sm:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 13px
    fontWeight: '600'
    lineHeight: '1.2'
  caption:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.35'
rounded:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 18px
  full: 9999px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 20px
  '6': 24px
  '8': 32px
  '10': 40px
  '12': 48px
  '16': 64px
  margin-mobile: 16px
  margin-tablet: 24px
  margin-desktop: 32px
  content-max: 1040px
  reading-max: 680px
  touch-target: 44px
components:
  top-bar:
    background: '{colors.surface}'
    foreground: '{colors.ink}'
    border-bottom: '{colors.hairline}'
    height: 56px
    typography: '{typography.label}'
  mode-banner:
    background: '{colors.accent-soft}'
    foreground: '{colors.ink}'
    typography: '{typography.body-sm}'
    padding: '{spacing.3}'
  breadcrumb:
    foreground: '{colors.ink-secondary}'
    current-foreground: '{colors.ink}'
    typography: '{typography.body-sm}'
  button-primary:
    background: '{colors.accent}'
    background-hover: '{colors.accent-strong}'
    foreground: '{colors.on-accent}'
    typography: '{typography.label}'
    radius: '{rounded.full}'
    height: '{spacing.touch-target}'
    padding-x: '{spacing.6}'
  button-secondary:
    background: '{colors.surface-muted}'
    foreground: '{colors.ink}'
    typography: '{typography.label}'
    radius: '{rounded.full}'
    height: '{spacing.touch-target}'
    padding-x: '{spacing.6}'
  button-quiet:
    background: transparent
    foreground: '{colors.accent}'
    typography: '{typography.label}'
    height: '{spacing.touch-target}'
  button-destructive:
    background: '{colors.danger}'
    foreground: '{colors.on-accent}'
    typography: '{typography.label}'
    radius: '{rounded.full}'
    height: '{spacing.touch-target}'
    padding-x: '{spacing.6}'
  text-input:
    background: '{colors.surface}'
    border: '{colors.border-strong}'
    border-focus: '{colors.focus-ring}'
    border-error: '{colors.danger}'
    radius: '{rounded.sm}'
    height: '{spacing.touch-target}'
    typography: '{typography.body}'
  segmented-control:
    track: '{colors.surface-muted}'
    selected-background: '{colors.surface}'
    selected-border: '{colors.border-strong}'
    foreground: '{colors.ink-secondary}'
    selected-foreground: '{colors.ink}'
    typography: '{typography.label}'
    radius: '{rounded.full}'
    height: 36px
  card:
    background: '{colors.surface}'
    border: '{colors.hairline}'
    radius: '{rounded.lg}'
    padding: '{spacing.6}'
  course-card:
    background: '{colors.surface}'
    border: '{colors.hairline}'
    border-hover: '{colors.border-strong}'
    marker: '{colors.course-1}'
    radius: '{rounded.lg}'
    padding: '{spacing.6}'
    title: '{typography.headline}'
    meta: '{typography.caption}'
  topic-row:
    background: '{colors.surface}'
    divider: '{colors.hairline}'
    min-height: 64px
    title: '{typography.body}'
    meta: '{typography.caption}'
  score-meter:
    track: '{colors.surface-muted}'
    fill: '{colors.accent}'
    fill-weak: '{colors.warning}'
    height: 6px
    radius: '{rounded.full}'
    value: '{typography.label}'
  status-badge:
    radius: '{rounded.full}'
    typography: '{typography.label-sm}'
    padding-x: '{spacing.2}'
    ready-background: '{colors.success-soft}'
    ready-foreground: '{colors.success}'
    generating-background: '{colors.accent-soft}'
    generating-foreground: '{colors.accent-strong}'
    failed-background: '{colors.danger-soft}'
    failed-foreground: '{colors.danger}'
    weak-background: '{colors.warning-soft}'
    weak-foreground: '{colors.warning}'
    demo-background: '{colors.surface-muted}'
    demo-foreground: '{colors.ink-secondary}'
  due-today-panel:
    background: '{colors.accent-soft}'
    foreground: '{colors.ink}'
    count: '{typography.display}'
    radius: '{rounded.lg}'
    padding: '{spacing.6}'
  source-row:
    background: '{colors.surface}'
    divider: '{colors.hairline}'
    progress: '{colors.accent}'
    title: '{typography.body}'
    meta: '{typography.caption}'
  upload-panel:
    background: '{colors.surface}'
    border: '{colors.border-strong}'
    border-active: '{colors.accent}'
    background-active: '{colors.accent-soft}'
    radius: '{rounded.lg}'
    padding: '{spacing.8}'
  dialog:
    background: '{colors.surface}'
    radius: '{rounded.lg}'
    padding: '{spacing.6}'
    max-width: 480px
    title: '{typography.headline}'
  summary-block:
    foreground: '{colors.ink}'
    typography: '{typography.body}'
    max-width: '{spacing.reading-max}'
  key-concept-item:
    divider: '{colors.hairline}'
    term: '{typography.headline}'
    definition: '{typography.body}'
    meta: '{typography.caption}'
    explanation-background: '{colors.surface-muted}'
    explanation-radius: '{rounded.md}'
  reference:
    background: '{colors.surface-muted}'
    rule: '{colors.border-strong}'
    radius: '{rounded.md}'
    padding: '{spacing.3}'
    location: '{typography.label-sm}'
    quote: '{typography.body-sm}'
  session-header:
    background: '{colors.canvas}'
    progress-track: '{colors.surface-muted}'
    progress-fill: '{colors.accent}'
    typography: '{typography.label}'
  question-card:
    background: '{colors.surface}'
    radius: '{rounded.lg}'
    padding: '{spacing.8}'
    padding-mobile: '{spacing.6}'
    question: '{typography.headline}'
    meta: '{typography.caption}'
  option-row:
    background: '{colors.surface}'
    border: '{colors.border-strong}'
    radius: '{rounded.md}'
    min-height: 52px
    typography: '{typography.body}'
    hover-background: '{colors.surface-muted}'
    selected-border: '{colors.accent}'
    selected-background: '{colors.accent-soft}'
    correct-border: '{colors.success}'
    correct-background: '{colors.success-soft}'
    incorrect-border: '{colors.danger}'
    incorrect-background: '{colors.danger-soft}'
  free-text-answer:
    background: '{colors.surface}'
    border: '{colors.border-strong}'
    border-focus: '{colors.focus-ring}'
    radius: '{rounded.md}'
    min-height: 120px
    typography: '{typography.body}'
  feedback-panel:
    radius: '{rounded.lg}'
    padding: '{spacing.6}'
    heading: '{typography.headline}'
    body: '{typography.body}'
    correct-background: '{colors.success-soft}'
    correct-foreground: '{colors.success}'
    partial-background: '{colors.warning-soft}'
    partial-foreground: '{colors.warning}'
    incorrect-background: '{colors.danger-soft}'
    incorrect-foreground: '{colors.danger}'
    not-graded-background: '{colors.surface-muted}'
    not-graded-foreground: '{colors.ink-secondary}'
  result-summary:
    background: '{colors.surface}'
    radius: '{rounded.lg}'
    padding: '{spacing.8}'
    score: '{typography.display}'
  flashcard:
    background: '{colors.surface}'
    radius: '{rounded.lg}'
    padding: '{spacing.8}'
    min-height: 280px
    face: '{typography.title}'
    face-mobile: '{typography.headline}'
    shadow: '0 2px 8px rgba(16, 24, 40, 0.08)'
  rating-bar:
    background: '{colors.surface-muted}'
    foreground: '{colors.ink}'
    radius: '{rounded.full}'
    height: 48px
    gap: '{spacing.2}'
    typography: '{typography.label}'
  topic-picker:
    row-background: '{colors.surface}'
    divider: '{colors.hairline}'
    checkbox-border: '{colors.border-strong}'
    checkbox-checked: '{colors.accent}'
    checkbox-radius: '{rounded.xs}'
    min-height: 52px
  empty-state:
    headline: '{typography.title}'
    body: '{typography.body}'
    foreground-secondary: '{colors.ink-secondary}'
    max-width: 420px
  inline-message:
    radius: '{rounded.md}'
    padding: '{spacing.4}'
    typography: '{typography.body-sm}'
    info-background: '{colors.accent-soft}'
    info-foreground: '{colors.ink}'
    error-background: '{colors.danger-soft}'
    error-foreground: '{colors.ink}'
    error-icon: '{colors.danger}'
  skeleton:
    background: '{colors.surface-muted}'
    radius: '{rounded.sm}'
---

## Brand & Style

AI Study Buddy should give the Student a sense of safety, calm and overview. Those are the Author's own words: «trygghet, ro og oversiktlighet». The visual language takes its cue from the Author's reference, Apple's website: generous whitespace, large plain headings, neutral light surfaces and one quiet accent. What stands out is the content, the Student's own Summary, Key concepts, Questions and Flashcards, not the interface around it.

Calm means nothing competes for attention: one accent color, no gradients, no red notification dots, no celebration animations. Safety means the app never surprises: every Generated item shows where it came from, every Grade is said in words as well as color, and nothing is deleted without asking. Overview means one clear heading per screen, and grouping by space and tone rather than by lines and boxes.

The palette is light, as the Author asked. The dark theme keeps the same calm, with deep neutral grey instead of pure black and the same accent lifted to a lighter blue.

## Colors

Every color token has a `-dark` twin, and both values are in the frontmatter. Components name the light token, and the dark theme resolves each reference to its twin.

| Token | Used for | Never for |
|---|---|---|
| `canvas` | Page background behind cards | Text |
| `surface` | Cards, dialogs, top-bar, question-card, flashcard | — |
| `surface-muted` | button-secondary, segmented-control track, reference, skeleton | Large page areas |
| `ink` | All primary text | — |
| `ink-secondary` | Metadata: Locations, counts, helper text | Text the Student must act on |
| `ink-disabled` | Disabled controls; below 4.5:1 on purpose | Readable text |
| `hairline` | Dividers between rows, card edges | Boundaries that identify a control |
| `border-strong` | Boundaries that identify a control: text-input, option-row, free-text-answer, checkboxes, upload-panel | Decoration |
| `accent` | The one brand color: button-primary, links, selection, progress and score fills | Headings, illustration, decoration |
| `accent-strong` | Hover and pressed accent; accent-colored text on `accent-soft` | — |
| `accent-soft` | Selected option-row, due-today-panel, mode-banner, info inline-message | Text |
| `on-accent` | Text on `accent` and `danger` fills | — |
| `focus-ring` | Keyboard focus on every interactive element | — |
| `success`, `success-soft` | The Grade correct; Source status ready | Buttons |
| `warning`, `warning-soft` | The Grade partially correct; Weak topics | — |
| `danger`, `danger-soft` | The Grade incorrect; failed generation; errors; button-destructive | Weak topics, the Again rating, the Exam-mode timer |
| `course-1` to `course-6` | One light tint per Course, as a marker next to its name `[ASSUMPTION]` | Large fills; the only way to tell Courses apart |

Weak topics use amber, not red. A Weak topic means "practice this", not failure, and red would break the calm the Author asked for. The accent is a calm blue rather than green, so it never competes with the green of a correct Grade.

Contrast, computed for these values against WCAG 2.2 AA:

| Pair | Light | Dark | Required |
|---|---|---|---|
| `ink` on `surface` / `canvas` | 16.5 / 15.3 | 15.2 / 16.7 | 4.5 |
| `ink-secondary` on `surface` / `canvas` / `surface-muted` | 6.3 / 5.8 / 5.5 | 7.3 / 8.0 / 6.5 | 4.5 |
| `on-accent` on `accent` | 5.0 | 7.4 | 4.5 |
| `accent` as text on `surface` / `canvas` | 5.0 / 4.6 | 6.9 / 7.5 | 4.5 |
| Accent text on `accent-soft` (`accent-strong` in light, `accent` in dark) | 5.9 | 5.8 | 4.5 |
| `success` / `warning` / `danger` on their `-soft` | 4.7 / 5.4 / 5.2 | 7.5 / 8.5 / 6.6 | 4.5 |
| `on-accent` on `danger` | 6.0 | 7.5 | 4.5 |
| `ink` on `course-1` to `course-6` | 13.0 or more | 10.9 or more | 4.5 |
| `border-strong` on `surface` / `canvas` | 3.7 / 3.4 | 3.6 / 4.0 | 3.0 |
| `focus-ring` on `surface-muted` | 4.4 | 6.1 | 3.0 |

## Typography

One family: the system font stack `system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`. That gives SF on Apple devices, Segoe UI on Windows and Roboto on Android. It stays close to the Apple reference without copying a brand typeface, and there is nothing to download. `[ASSUMPTION]` Sizes, line heights and weights are in the frontmatter.

| Role | Used for |
|---|---|
| `display` (`display-mobile` below 600 px) | At most one per screen: the screen title on Course overview and Topic, the count in the due-today-panel on Home, and the score in result-summary |
| `title` | Section headings inside a screen; the flashcard face from 600 px |
| `headline` | Question text, course-card title, Key concept term, feedback-panel heading, dialog title, the flashcard face below 600 px |
| `body` | Summary, definitions, options, Explanations, free text |
| `body-sm` | Reference quotes, helper text, inline-message, breadcrumb |
| `label` | Buttons, segmented-control, session-header |
| `label-sm` | status-badge, the Location in a reference |
| `caption` | Metadata: counts, page numbers, «Ikke nok data ennå» |

Rules:
- Sentence case everywhere; never all caps.
- Tabular figures for the timer, scores and counts, so the digits do not jump.
- Study material keeps the language of its Source and uses the same roles.
- Body text is never wider than `{spacing.reading-max}`.

## Layout & Spacing

The scale is 4 px based, from `{spacing.1}` to `{spacing.16}`. Space does the grouping: 32 to 48 px between sections, 16 to 24 px inside cards, and 8 to 12 px between related items.

- **Side margins:** `{spacing.margin-mobile}` below 600 px, `{spacing.margin-tablet}` from 600 to 1023 px, and `{spacing.margin-desktop}` from 1024 px.
- **Page width:** content is centered and at most `{spacing.content-max}` wide.
- **Reading width:** Summary, Quiz, Review and Flashcards keep text within `{spacing.reading-max}`.
- **Columns:** from 1024 px the Topic splits two thirds to one third. What goes where, and at which width, is in EXPERIENCE.md, Responsive & Platform.
- **Touch targets:** every target is at least `{spacing.touch-target}`.

## Elevation & Depth

Flat by default. Surfaces sit on `canvas` and are told apart by tone, space and a `hairline` edge. Shadows appear only where something floats or behaves like a physical object:

- **dialog:** `0 8px 32px rgba(16, 24, 40, 0.16)` over a scrim of `rgba(17, 18, 21, 0.40)`.
- **Account menu** in the top-bar: `0 4px 16px rgba(16, 24, 40, 0.12)`.
- **flashcard:** `0 2px 8px rgba(16, 24, 40, 0.08)`, the one card that behaves like a card.

The dark theme uses no shadows. Floating surfaces use `surface-muted` with a `hairline` edge, over a scrim of `rgba(0, 0, 0, 0.60)`.

## Shapes

Soft and friendly, never childish. Pills mean "you can press this"; rounded rectangles hold content.

- `{rounded.xs}`: checkboxes.
- `{rounded.sm}`: text-input and skeleton.
- `{rounded.md}`: option-row, free-text-answer, reference and inline-message.
- `{rounded.lg}`: card, course-card, question-card, flashcard, dialog, upload-panel, due-today-panel and result-summary.
- `{rounded.full}`: buttons, segmented-control, status-badge and score-meter.

## Components

Visual specs only; behavior lives in EXPERIENCE.md, Component Patterns. Token values are in the frontmatter. Every interactive component shows a 2 px `{colors.focus-ring}` ring with a 2 px offset on keyboard focus. The key-screen mocks in [`mockups/`](mockups/) show these specs applied in both themes; EXPERIENCE.md lists what each one illustrates.

- **top-bar:** `surface`, 56 px high, `hairline` bottom edge. App name on the left in `label`. On the right: «I dag» with the count, and the account menu, which opens as a `surface` panel with `{rounded.md}` corners.
- **mode-banner:** a full-width strip under the top-bar, `accent-soft` with `ink` text in `body-sm` and an info icon on the left.
- **breadcrumb:** `body-sm`. Parents are links in `ink-secondary`, the current level is in `ink`, and the separator is «›».
- **button:** four variants, all 44 px pills:
  - `button-primary`: `accent` fill, `on-accent` text, `accent-strong` on hover and press.
  - `button-secondary`: `surface-muted` fill, `ink` text.
  - `button-quiet`: no fill, `accent` text, underline on hover.
  - `button-destructive`: `danger` fill, `on-accent` text.

  While loading, the label stays and a small spinner sits to its left.
- **text-input:** `surface`, 1 px `border-strong`, `{rounded.sm}`, 44 px, label above in `label`. On error, the border becomes 2 px `danger`, and the message sits below in `body-sm` and `danger`.
- **segmented-control:** a `surface-muted` pill track. The selected segment is `surface` with a 1 px `border-strong` edge and `ink` text; the others use `ink-secondary`.
- **card:** `surface`, 1 px `hairline` edge, `{rounded.lg}`, padding `{spacing.6}`.
- **course-card:** a card with a 6 px strip on the left in the Course's color (`course-1` to `course-6`). Title in `headline`; course code and counts in `caption`. On hover, the edge turns `border-strong`.
- **topic-row:** at least 64 px high, title in `body`, `hairline` divider. The score-meter sits on the right from 600 px and below the title under 600 px. A status-badge follows the title.
- **score-meter:** a 6 px pill track in `surface-muted`, filled with `accent`, or `warning` for a Weak topic. The value is always written next to it in `label` («45 %»). With too little data, only the caption is shown.
- **status-badge:** a pill in `label-sm`. Text is always present; an icon is optional. Color pairs:
  - ready: `success` on `success-soft`
  - generating: `accent-strong` on `accent-soft`
  - failed: `danger` on `danger-soft`
  - «Trenger øving»: `warning` on `warning-soft`
  - «Demo»: `ink-secondary` on `surface-muted`
- **due-today-panel:** `accent-soft`, `{rounded.lg}`. The count is in `display` and «kort i dag» in `body`. Counts per Course appear as `surface` chips, each with a 10 px dot in the Course's color outlined in 1 px `border-strong`, followed by a button-primary.
- **source-row:** file icon, name in `body`, meta in `caption` (pages, Detail level), and a status-badge. While generating, a 2 px `accent` line runs along the bottom edge; it stays still when reduced motion is on.
- **upload-panel:** a 1.5 px dashed `border-strong` edge, `{rounded.lg}`, with a centered icon, text in `body` and the limits in `caption`. While a file is dragged over it, the edge is `accent` and the fill is `accent-soft`.
- **dialog:** `surface`, `{rounded.lg}`, at most 480 px wide, title in `headline`. Actions are right-aligned, with the primary action rightmost. Below 600 px it is a full-width sheet from the bottom, with rounded top corners.
- **summary-block:** plain text in `body` within the reading width, no box. The Detail level segmented-control sits in its header.
- **key-concept-item:** the term in `headline`, the definition in `body` and the Location in `caption`. Actions are button-quiet. The Simpler explanation opens below in a `surface-muted` panel with `{rounded.md}` corners and `body-sm` text, headed «Enklere forklaring».
- **reference:** a `surface-muted` box with `{rounded.md}` corners and a 3 px `border-strong` rule on the left. The Location is in `label-sm`, followed by the quote in `body-sm` inside «».
- **session-header:** on `canvas`, with no edge. On the left, the exit as a button-quiet. In the middle, the progress as text in `label` and a 4 px bar. On the right in Exam mode, the timer in `label` with tabular figures and in `ink`, never red.
- **question-card:** `surface`, `{rounded.lg}`, padding `{spacing.8}` (`{spacing.6}` below 600 px). The question type is in `caption` and the Question in `headline`. The Hint opens as `body-sm` in `ink-secondary`, with a lightbulb icon.
- **option-row:** full width, at least 52 px high, `{rounded.md}`, 1 px `border-strong` edge. Each has a letter A to D in a 28 px circle on the left. States:
  - hover: `surface-muted`
  - selected: 2 px `accent` edge, `accent-soft` fill and a filled radio dot
  - correct: 2 px `success` edge, `success-soft` fill, a check icon and the words «Riktig svar»
  - incorrect (the chosen one): 2 px `danger` edge, `danger-soft` fill, a cross icon and the words «Ditt svar»

  After grading, the other options keep full `ink` text and are never dimmed.
- **free-text-answer:** `surface`, 1 px `border-strong`, `{rounded.md}`, at least 120 px high. On focus, the edge is 2 px `focus-ring`.
- **feedback-panel:** `{rounded.lg}`, padding `{spacing.6}`, with a soft fill for each Grade:
  - correct: `success-soft`
  - partially correct: `warning-soft`
  - incorrect: `danger-soft`
  - not graded: `surface-muted`

  The heading is in `headline` with an icon in the Grade's color. The Explanation is in `body` and `ink`. A reference and the actions follow.
- **result-summary:** a card with the score in `display` («7 av 10»). In Exam mode, a row per Topic with a score-meter. Below, one row per Question with its Grade written out.
- **flashcard:** `surface`, `{rounded.lg}`, at least 280 px high, with a shadow in the light theme only. The face text is centered, in `title` from 600 px and `headline` below. The back adds a reference below a `hairline`. Flipping is a turn around the vertical axis in 300 ms; with reduced motion on, the card changes instantly.
- **rating-bar:** four equally wide `surface-muted` pills, 48 px high, with `{spacing.2}` between them. Each has a label and a small key hint (1 to 4) in `caption`. No color coding.
- **topic-picker:** 52 px rows, each with a 20 px checkbox (`{rounded.xs}`, `border-strong` edge, `accent` fill with a white check when checked). The Topic name is in `body` and the Topic score in `caption`, with a status-badge for Weak topics.
- **empty-state:** centered, at most 420 px wide. A heading in `title`, one sentence in `body` and `ink-secondary`, and one button-primary. No illustration. `[ASSUMPTION]`
- **inline-message:** `{rounded.md}`, padding `{spacing.4}`, with an icon on the left. Info uses `accent-soft` with `ink` text. Error uses `danger-soft` with `ink` text and a `danger` icon. An optional action appears as a button-quiet.
- **skeleton:** `surface-muted` blocks with `{rounded.sm}` corners, pulsing gently in opacity from 1 to 0.6 over 1.2 s. They stay still when reduced motion is on.

## Do's and Don'ts

| Do | Don't |
|---|---|
| One accent (`{colors.accent}`) for the next step, links, selection and focus | Use the accent for headings, decoration or illustrations |
| Group by space and tone: `surface` on `canvas` | Put boxes inside boxes, use heavy borders, or use shadows for hierarchy |
| Say every Grade and status in words, with color as support | Signal with color alone, or with red and green alone |
| Amber (`{colors.warning}`) for Weak topics | Red for Weak topics, the Again rating or the Exam-mode timer |
| At most one `display` heading per screen | Several competing large headings |
| System font, sentence case | Web fonts or all-caps labels |
| Deep neutral grey in the dark theme | Pure black backgrounds or neon accents |
| Pills for actions, rounded rectangles for content | Pill-shaped content cards |
| Course colors as small markers next to the Course name | Course colors as large fills or as the only label |
