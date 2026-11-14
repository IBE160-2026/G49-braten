# Success metrics

## Primary

- **SM-1 Personal use.** From the first working version until delivery, the Author completes ≥ 3 Quizzes or Reviews a week in ≥ 2 Courses, measured from stored Answers and Reviews. Target judged at delivery. Validates CAP-7 to CAP-10.
- **SM-2 Acceptance checklist.** Every check passes, by following the README (R) or by an automated test (T). Checks 1–6 are the brief's functional criteria.
  1. (R) The Sample document gives the Study material in FR-7.
  2. (R) The Generated item with a wrong Reference is removed (FR-8).
  3. (R) The app runs in Mock mode without a Key (FR-20, NFR-2).
  4. (R) Uploads over the limits are rejected (FR-3).
  5. (R) Quizzes are graded; incorrect and partially correct Questions go into a Retry round (FR-11 to FR-13).
  6. (R) Data is stored per Student, Course and Topic and survives signing in again (FR-1, FR-2).
  7. (T) Review dates follow FR-15.
  8. (T) Weak topics show as in FR-17.
  9. (T) Generation calls stop at the NFR-7 limit.
  10. (T) The Next step follows the FR-28 order.

## Secondary

- **SM-3 Reference quality.** On the Author's own material in Real mode, ≥ 90% of Generated items pass FR-8. Validates CAP-5.
- **SM-4 Loop effect.** Of Questions the Author answers incorrectly or partially correctly, ≥ 60% are answered correctly the next time they appear in a later non-Retry Quiz, from stored Answers. Validates the bet and CAP-8, CAP-10. Dropped if the 30 November cut is used.

## Counter-metrics (do not optimize)

- **SM-C1 Number of Generated items.** Beyond FR-7's minimums, more items are not better if fewer pass FR-8.
- **SM-C2 Topic score.** High scores can come from repeated exposure. Do not make Questions easier or repeat them to raise scores.
