# Delivery plan

Split and build order confirmed by the Author 2026-11-01; cut lines revised 2026-11-13 after the teacher's feedback.

## Scope

- **Must (7 December 2026):** CAP-1 to CAP-13 (FR-1 to FR-4, FR-6 to FR-17, FR-20 to FR-24, FR-27, FR-28) and NFR-1 to NFR-7.
- **Should:** CAP-14 to CAP-18 (FR-5, FR-18, FR-19, FR-25, FR-26). Built only after every Must is done and tested.

## Build order

1. **Core loop, done and tested by 20 November 2026:** FR-1 to FR-4, FR-6 to FR-13, FR-20 to FR-24, NFR-7 (its limit guards the generation built here).
2. **Practice over time, done by 30 November 2026:** FR-14 to FR-17, FR-27, FR-28. FR-20 is fully checked here, since the Examiner's path includes a Review.

A step is **done and tested** when both hold:
- Every Key-free testable consequence of the step's FRs and NFRs has an automated test, and all pass.
- The step's SM-2 checks pass in Mock mode: step 1 checks 1–6 and 9 (check 3 up to the Retry round); step 2 checks 7, 8, 10 and check 3 in full.

Real-mode measurements (NFR-3, NFR-5 content check, SM-3) are made before delivery, not at step end.

## Cut lines

The Author records either cut when it happens.
- **20 November:** if step 1 is not done and tested, FR-24 moves to Should. The bet stays intact.
- **30 November:** if step 2 is not done, FR-16 and FR-17 move to Should, taking the Course score and Next-step rule 2 with them. UJ-3 becomes Should; SM-4 and SM-2 check 8 are dropped.

## Deferred beyond v1 (context for later)

- **Images and handwriting (OCR).** Two routes: a vision-capable model reads the image, or OCR runs before the call. Not researched; handwriting quality unknown; both affect Mock mode and References, since an image has no page. Revisit if Musts finish early, after the images open question.
- **Old exam tasks.** The Author's words (2026-11-01): «appen skal gjøre at studenten får mer kontroll over oppgavene til eksamensoppgavene. Komme med deloppgaver som gjør det enklere å svare på de større og vanskeligere oppgavene». Break a large exam task into sub-tasks that build to the whole. Open: whether each sub-task is answered and graded alone, and whether sub-tasks draw on the Course's Sources. Revisit if Musts finish early.
