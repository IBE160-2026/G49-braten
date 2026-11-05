# PRD Quality Review — AI Study Buddy

*Reviewed: `prd.md` (updated 2026-11-01, ~5,260 words) and `addendum.md`. Calibrated for a solo IBE160 course project due 7 December 2026 that sits at the top of the chain (it feeds UX, architecture and epics) and is graded on brief → PRD → stories → code traceability. The confirmed Must / Should / Out split (§7) and the decision to leave technology to architecture are taken as given.*

## Overall verdict

A strong chain-top PRD for its stakes: the thesis is specific, the Must scope follows it, the Glossary is used consistently, and all 22 FRs have at least one testable consequence, so UX and architecture can start from it after one short round of fixes (none of the 25 `[ASSUMPTION]` tags blocks either phase). The risk is in what it leaves unsaid: where the Author's own instance runs and who can sign up there (UJ-2 and SM-1 depend on it), three SM-2 acceptance checks the Examiner can't perform in a README run as written, and no way to remove a generated item that passes the Reference check but is wrong. At ~5,260 words it is about four times the recorded 2–3 page target; about 850 words of restatement should go, and the rest is earned.

## Decision-readiness — adequate

Decisions are stated as decisions, usually with the reason and the cost attached. Multiple-choice grading happens in code "so grading needs no call to the AI provider" (FR-11). "The app shows no confidence score from the AI provider; trust in a generated item comes from its checked Reference" (FR-8). In Mock mode "no Study material is made up" for other Sources (FR-20). Word Locations are headings "because Word files have no fixed page numbers" (FR-5). Output language follows the Source, and the PRD names what that costs: "the Student cannot override it in v1" (FR-6). The "Changes from the product brief" table (§0) is the best decision tool in the document: it lists every departure from the brief with its reason, which is exactly the trace the Examiner grades. Both `[NOTE FOR PM]` callouts (§7.3) mark a real tension, since the Author asked for images and old exam tasks and both are cut. Open Questions 2 and 3 are genuinely open and each has an owner.

Two gaps: one decision that the rest of the PRD assumes was made, and one consequence of FR-15 that nobody chose on purpose.

### Findings

- **high** Where the Author's own instance runs, and who can sign up there, is never decided (§1, UJ-2, NFR-2, FR-1, SM-1). UJ-2 has Ida reviewing "On the phone" on a bus. SM-1 needs weekly use "until delivery". §1 says the app "must also run on the Examiner's machine", and the "also" implies a main instance somewhere else. NFR-2 keeps "the Author's hosted services" out of the Examiner's path. All of this assumes an instance a phone can reach over the internet, but no requirement says one exists. The follow-on product questions are therefore open too. FR-1 lets "A person" create an account, so on a public Real-mode instance any stranger could spend the Author's key and free-tier quota and push their own content through the Author's provider account. Nothing says the Author's semester of data must survive restarts and redeploys. Architecture can't choose storage, auth hardening or secrets handling without this, and it is a product decision, not a technology choice. *Fix:* add one Must FR or NFR: "The Author runs one hosted instance for personal use; sign-up there is limited to [the Author / invited users]; data survives restarts and redeploys." Keep the Examiner's local, keyless path as NFR-2 describes it. If there is no hosted instance, rewrite UJ-2 and SM-1 to match. If the access rule is still undecided, add a `[NOTE FOR PM]`.
- **medium** Every new Flashcard is due on the day it is made, with no daily cap (FR-15). The PRD says "A new Flashcard is due on the day it is generated." The Author will start in November with a backlog. Uploading, say, the first ten weeks of slides in two Courses puts every card from all of it into Due today at once. UJ-2 pictures 14 Due cards on a bus ride, and JTBD 4 is to keep a growing syllabus "under control through the semester". Spaced-repetition tools cap new cards per day for this reason. The PRD neither caps them nor says it accepts the backlog, and the line has no `[ASSUMPTION]` tag. *Fix:* choose one and state it: "at most N new cards enter Due today per day (default 20) `[ASSUMPTION]`", or "all new cards are due at once; accepted for v1".
- **low** Open Question 1 is answered, not open (§9). "Old exam tasks — resolved 2026-11-01" gives its answer in the same item. The same content is also in the §0 table, §7.3 and the addendum. *Fix:* delete §9 Q1, renumber the rest, and update the "§9 question 1/2" references in §7.3 and the addendum.

## Substance over theater — strong

There is little filler. The Vision admits that generating study material "is not new" and names a specific bet: "closing the loop between testing and repetition: every Answer decides what the Student practises next". You could not move that into another study-app PRD unchanged. There are two personas and both do work. Ida carries every Student journey, and Jonas carries the keyless Examiner path behind FR-20, FR-21 and NFR-2. The NFRs have bounds specific to this product (360 px, 15 minutes, 2 minutes per 20-page PDF, 15 seconds, 5 seconds), and NFR-5 lists exactly which logic must be tested without a key or network. The counter-metrics are real: SM-C2 names exactly how this product could fool its own Topic score.

The only mild filler is JTBD 5 ("As the Author: learn to build and reason about an AI app end to end"), a course learning goal that drives no FR. §2.1 and §2.2 also restate §1, the UJs and §6. That is a length problem, covered under Shape fit.

### Findings

- **low** "Salted hashes" sets a bar that a weak hash clears (NFR-4). "Passwords are stored only as salted hashes" is satisfied by a salted fast hash such as SHA-256, which is cheap to brute-force. *Fix:* write "Passwords are stored only with a hash function built for passwords (slow and salted)" and leave the choice of function to architecture.

## Strategic coherence — adequate

There is a thesis, and the scope follows it. The three loop mechanisms are all Must: the Retry round (FR-13), spaced repetition (FR-15), and Topic score with Weak topics (FR-16, FR-17). Features that don't close the loop are Should: Word files (FR-5), Exam mode (FR-18) and Simpler explanation (FR-19). OCR and old exam tasks are Out. FR-8 carries the trust half of the Vision and SM-3 measures it. This is a problem-solving MVP for one user, the scope logic matches that, and it does not read like a backlog.

Three things weaken the arc: the loop can't drop a bad item, the metrics count use instead of testing the bet, and the build order puts the thesis last.

### Findings

- **high** A wrong generated item can only be removed by deleting its whole Source (FR-8, FR-11, FR-13, FR-16, FR-2). FR-8 says the Reference check "does not judge whether the content is correct", and FR-11 grades against the stored correct option with no call to the AI provider. So a Question whose stored option is wrong passes the check. It then marks the Student wrong every time they answer correctly, comes back in every Retry round (these run "until every Question is correct", FR-13), and pulls its Topic toward Weak-topic status (FR-16, FR-17). A Flashcard with a wrong back keeps coming back in Due today all semester. The only way out is to delete the Source, and by FR-2 that also deletes its Answers. The product bets that "every Answer decides what the Student practises next", so bad items corrupt what the loop runs on. The Author will meet them when using the app every week (SM-1). *Fix:* add a Must consequence to FR-2: the Student can delete a single Key concept, Flashcard or Question; it then leaves Quizzes, Retry rounds and Due today, and its Answers stop counting toward the Topic score. If the Author declines, say so in §6 and give the reason.
- **medium** No success metric tests the bet (§8). SM-1 counts sessions ("at least three Quizzes or Reviews a week"), SM-2 is an acceptance checklist, and SM-3 measures Reference quality. None of them would change if the loop didn't help. This is the rubric's "metrics that just measure activity" pattern. The data needed to test the bet is already stored (Answers, Topic scores, Retry rounds). *Fix:* add one secondary metric computed from stored data. One option: "SM-4 Loop effect: a Topic that was a Weak topic rises above 60 % within two weeks of practising it." Another: "Questions missed and then retried are answered correct at least X % of the time when they next come up in a later Quiz (not a Retry round)." Tag the targets `[ASSUMPTION]` and let SM-C2 stand as the counterweight.
- **medium** The build order puts the thesis last and is the de facto cut line without saying so (§7.1). Step 2, "Practice over time", includes FR-8, which is about trust, not practice over time. FR-20 sits in step 1, but its consequence requires the Examiner to "take a Quiz with a Retry round and do a Review". Those are FR-13 and FR-15, both in step 2, so step 1 can't pass its own test. With five weeks left, step 2 is what gets cut if time runs out. That would be the Reference check, the Retry round, review dates and Weak topics: SM-2 checks 2, 5, 7 and 8 and most of the thesis. The order is tagged `[ASSUMPTION]` and will set the epic order. *Fix:* move FR-8 and FR-13 into step 1. Both are small, and FR-20's demo needs FR-13. State that FR-20 is fully checked at the end of step 2. Add one sentence naming the cut line: which Must FRs become Should if step 2 isn't done by a set date. Confirm the order with the Author before epics.

## Done-ness clarity — adequate

This is better than most PRDs at this level. Every FR has at least one testable consequence, and many have bounds a test can check directly:
- 50 pages / 10 MB (FR-3)
- "at least 5 Key concepts, at least 10 Flashcards and at least 10 Questions" (FR-7)
- "within 1 second, with no call to the AI provider" (FR-11)
- "strictly longer intervals" (FR-15)
- an explicit Topic-score formula (FR-16)
- a seeded 40 / 55 / 80 % fixture (FR-17)
- FR-8's "one item fewer is shown and the removed count is 1"

Story acceptance criteria can be copied almost word for word.

The gaps are where pieces meet: how the acceptance checklist is verified, an Answer state the definitions skip, the mode rule on the Examiner's path, the edges of FR-8, and what a two-minute job does when the Student leaves.

### Findings

- **high** Three of the eight SM-2 checks can't be performed, as written, in "a run that follows the README" (§8 SM-2 checks 2, 7 and 8; FR-8, FR-15, FR-17, FR-20). In Mock mode the Examiner has only the Sample document.
  - Check 2 is visible only if the shipped recorded response contains a deliberately wrong Reference. FR-8's "With a recorded response that has one wrong page number" doesn't say whether that is a test fixture or shipped data.
  - Check 7 ("Review dates follow FR-15") needs days to pass.
  - Check 8 ("Weak topics are shown as in FR-17") needs at least 5 graded Answers in each of several Topics, with scores on both sides of 60 %, built by hand from one document.

  NFR-5's automated tests cover review dates and Topic scores, but SM-2 never says that a passing test counts as a passing check. This is the checklist the Examiner grades against, and stories will copy it into their acceptance criteria. *Fix:* give each SM-2 check a verification path, either "README walk-through" or "automated test (NFR-5)". Add to FR-20 that the Sample document's recorded response contains exactly one item with a wrong Reference, so the demo shows "1 removed". For checks 7 and 8, either add a seed command documented in the README (Topics with given Topic scores, cards with past review dates), or state that these checks pass by automated test.
- **medium** "Not graded" is an Answer state that the definitions don't cover (FR-12; Glossary entries Grade and Retry round; FR-13, FR-16). FR-12 marks a failed grading as "not graded". The Glossary's Grade has only three values, and FR-16's weights cover only correct, partially correct and incorrect. The Retry-round rule ("not graded correct") literally includes an ungraded Answer. Two of the six areas NFR-5 tests, Retry rounds and Topic scores, depend on how this state is handled. Grading every Free-text answer at once on Exam-mode submission (FR-18) makes such failures more likely. *Fix:* add "not graded" to the Grade entry. State in FR-16 that ungraded Answers don't count until they are graded, and in FR-13 whether an ungraded Question goes into the Retry round.
- **medium** The Mock/Real switch is described three different ways, and the Examiner's path depends on it (Glossary Real mode, FR-20, FR-21, UJ-5).
  - The Glossary says Real mode is "selected with a key".
  - FR-20 says "With no key configured, the app runs in Mock mode".
  - FR-21 says Real mode needs "the AI provider and a key", and that "A missing or rejected key gives a clear error message".

  In UJ-5, Jonas copies `.env.example` to `.env` "without adding a key". FR-21 says `.env.example` "lists every setting needed", so it will likely name a provider. In that case FR-21 calls for an error and FR-20 calls for Mock mode. *Fix:* state one rule, once, in FR-20. For example: "No key → Mock mode, whatever else is set; a key that is set but rejected → an error message, and the app keeps running." Make the Glossary entries match it.
- **medium** FR-8 sets no minimum quote length and leaves its scope unclear (FR-8, Glossary Reference, §1, SM-3). FR-8's rule that "the quote must appear at that Location" is satisfied by a one-word quote, or by a slide footer that is repeated on every page. So a wrong Location can pass, and SM-3's 90 % can be reached trivially. The check also covers only "generated items" (Key concepts, Flashcards, Questions). The Summary has no Reference at all, even though §1 says "Every item points back to the page it came from" right after naming the Summary. The Explanations written during grading (FR-12) and Simpler explanations (FR-19) carry References that FR-8 doesn't say it checks. *Fix:* add a rule that the quote must be specific enough to place: "at least 5 words, and not text that repeats on most pages, such as headers and footers `[ASSUMPTION]`". List in FR-8 which outputs are checked. Say in §1, or in the Summary entry, that the Summary has no Reference in v1, or give it one Reference per paragraph.
- **medium** A two-minute generation job has no defined lifecycle (FR-9, NFR-3). NFR-3 allows 2 minutes for a 20-page PDF, and more at the 50-page limit, and the PRD expects phone use. FR-9 only says the Student "sees that generation is running". It doesn't say whether generation continues if the Student leaves the page, locks the phone or closes the tab, or what the Topic shows when they return. That choice decides between a synchronous request and a background job, and it is a state UX has to design. *Fix:* add to FR-9: "Generation continues if the Student leaves the page; on return the Source shows as generating, ready or failed."
- **low** Adjectives are used where bounds belong (FR-9, FR-21, NFR-1; Glossary Hint, Key concept, Simpler explanation; UJ-4). Examples: "a clear message" (FR-9), "a clear error message" (FR-21), "current desktop and mobile browsers" (NFR-1), Hint "a short nudge", Key concept "a short definition", Simpler explanation "shorter, plainer" (UJ-4 "a short, plain version"). *Fix:* say what each message contains (for example, "names what failed and offers Retry"). Name the browsers (for example, the latest Chrome, Safari and Firefox). Bound the texts (for example, a Hint is one sentence and doesn't contain the correct option; a Simpler explanation is shorter than the definition it replaces).
- **low** Edge cases that stories will run into (FR-3, FR-4, FR-7, FR-10, FR-15, FR-16):
  - (a) FR-3's page limit covers only PDFs. Plain-text files and pasted text have only the 10 MB cap, far above the free-tier token limits the limit exists to protect.
  - (b) FR-4's "the right page number": is that the PDF's page index or its printed page label? They differ for a chapter cut out of a book.
  - (c) Are FR-7's minimums counted before or after FR-8 removes items?
  - (d) FR-10: what happens if the Student asks for more Questions than the Topic has?
  - (e) FR-16 "updates when a Quiz ends": do Answers from an abandoned Quiz count?
  - (f) FR-15's "strictly longer intervals" fails once a capped scheme reaches its top interval. That includes Leitner, which the addendum says satisfies FR-15.

  *Fix:* add one consequence for each. Examples: a character limit for text Sources; "the page index as shown in a PDF viewer"; "the minimums apply after the check"; "capped at the number of Questions in the Topic"; "Answers are saved as they are given"; "up to a maximum interval".

## Scope honesty — strong

Omissions are explicit. §6 does real work: no payment, no native apps, no roles beyond Student, no free-form chat. §7.3 records what the Author asked for and didn't get, with a `[NOTE FOR PM]` on both items. The §0 table makes every departure from the brief visible, including the cuts. All 25 inline `[ASSUMPTION]` tags match entries in §10. That many tags, plus two notes and two genuinely open questions, is fine for a solo course project.

No tag blocks a phase. Most are config values (limits, windows, thresholds) that architecture can carry as defaults. Three are worth confirming in one sitting before UX and epics, because they shape screens or order:
- the four ratings (FR-15), which are also built into the Glossary's Review entry and UJ-2
- hiding versus flagging failed items (FR-8), which decides what the Topic screen shows
- the build order (§7), which decides the epic order

### Findings

- **low** A few omissions that a reader could fill in silently (§6): offline use (UJ-2 happens on a bus); password reset or account recovery (FR-1); export, for example of Flashcards to Anki; and the interface language. FR-6 sets the language of Study material, but nothing says whether buttons, messages and the privacy notice are in Norwegian or English, and UX needs that for every screen. *Fix:* add one §6 line each for offline use, password reset and export, and add one consequence or NFR for the interface language.
- **low** Some inferences carry no tag (Glossary Hint and Exam mode; FR-7, FR-11, FR-15, NFR-1). §0's rule is that every unconfirmed inference is tagged. The workspace memlog (`.memlog.md`) lists two inferences as assumptions: the Hint definition, and Exam mode hiding grades and Explanations until submission. Neither is among the points the Author confirmed, which were Multiple-choice grading in code, Retry rounds outside the Topic score, and no mock content for other Sources. Also untagged:
  - FR-11's "within 1 second"
  - FR-15's "due on the day it is generated" and "comes back before the Review ends"
  - NFR-1's 360 px
  - FR-7's "at least 10 Flashcards" (the FR-7 tag lists only Key concepts and Questions)

  *Fix:* tag and index these, or confirm them with the Author.

## Downstream usability — strong

This PRD is built so later steps can extract from it. The Glossary has 35 terms and they are used consistently. Lowercase uses of its nouns are almost all inside compound terms ("model answer", "Weak topics") or in ordinary English ("course project"). IDs are contiguous and unique, and every cross-reference resolves. Every FR has a "Realizes UJ-n" line or inherits one from its feature, and both UJ protagonists are named. The Must list in §7.1 and its two build steps cover every Must FR exactly once. SM-2 marks which checks come from the brief ("Checks 1–6 are the brief's functional criteria"), which gives the Examiner a ready-made trace.

UX will be missing one screen and two moments.

### Findings

- **medium** The Topic screen has no FR (UJ-1, FR-7, FR-8, FR-14). UJ-1 says "the Topic shows the Summary, Key concepts, Flashcards and Questions", and FR-8 puts the removed count there, but no FR says what the Student can see or do on that screen. Open questions:
  - With several Sources in one Topic (FR-3 makes that the normal case), is Study material shown per Source or merged?
  - Are Questions listed outside a Quiz? That would spoil the Quiz.
  - Where do Key concepts show their References?

  FR-14 covers browsing Flashcards, but nothing covers reading the Summary or Key concepts, and the Summary is the first thing §1 promises. *Fix:* add a new FR-23 "View Study material" with two or three consequences: material is grouped by Source; the Summary and Key concepts are shown with their Locations; Questions appear only in a Quiz `[ASSUMPTION]`.
- **low** Two flows appear in no UJ, and one UJ detail appears in no FR (§4.9, UJ-1, UJ-2, FR-15, FR-21, FR-22). §4.9 claims "Realizes UJ-5", but UJ-5 runs in Mock mode, so no journey shows the Real-mode privacy notice (FR-22) or the key error (FR-21). UX has no moment to design them from. UJ-2 ends with "the number of cards reviewed and when the next cards are due", but no FR-15 consequence requires that. *Fix:* add one sentence to UJ-1, such as "The first time, Ida reads and accepts the privacy notice". Add the end-of-Review summary as an FR-15 consequence.

## Shape fit — adequate

The shape fits a solo, chain-top PRD with an examiner: a capability spec with testable consequences, five UJs, and an acceptance checklist the Examiner can tick off. Each UJ adds a context UX needs: an evening on a laptop, a phone on a bus, the run-up to an exam, a concept that doesn't click, and the keyless Examiner. It isn't over-formalized for one user, and UJ-5 alone justifies the journeys section.

Size is the problem. The workspace memlog records a target of 2–3 pages, and the skill's guidance for solo PRDs is about two. The PRD is ~5,260 words, roughly four times that. Most of it is earned. The FR consequences and the Glossary are what stories and the Examiner rely on, and cutting them to hit a page count would trade the PRD's best dimension for a number. But about a sixth of the text restates other parts of the same document, and those copies have started to disagree.

### Findings

- **medium** The PRD is about four times the agreed length, and the repeated text already disagrees with itself (whole document). Examples:
  - Old exam tasks are described in four places (§0 table, §7.3, §9 Q1, addendum), and images in five.
  - The Glossary's Real mode ("selected with a key") disagrees with FR-21 ("the AI provider and a key").
  - FR-8 normalizes "whitespace and line breaks", while the addendum adds hyphenation.

  *Fix:* cut about 850 words, none of them FR consequences:
  1. Cut §0 to three sentences (readers, sources, tag convention). Saves about 120 words.
  2. In the nine feature "Description" paragraphs (§4.1–4.9), keep only "Realizes UJ-n" on each heading. Each paragraph restates the FRs under it. Saves about 240 words.
  3. Delete §2.1 JTBD, or keep one line of it in §1. Jobs 1–4 restate §1 and UJ-1–3; jobs 5–6 restate §0. Saves about 125 words.
  4. Fold §2.2 Non-Users into §6. Saves about 30 words.
  5. Replace §9 Q1 and the second description of old exam tasks in §7.3 with one line in §7.3 pointing to the addendum. Saves about 85 words.
  6. In the Glossary, keep each noun's meaning and leave the rules to the FRs. For example, "four options, exactly one correct" duplicates FR-7, and the Mock mode, Real mode and Exam mode entries restate FR-20, FR-21 and §4.7. Saves about 150 words.
  7. Shorten §10 to one line per tag, without repeating the reason given inline. Saves about 100 words.

  Keep the §0 change table, since it is the brief-to-PRD trace the Examiner grades. The remaining ~4,400 words are earned. Record in the memlog that the length target was revised, instead of cutting consequences to fit two pages.

## Mechanical notes

- **ID continuity.** FR-1–22, UJ-1–5, NFR-1–5, SM-1–3 and SM-C1–C2 are contiguous and unique. Every FR, UJ, NFR, SM and § reference resolves, and there are no "see above" pointers. Build steps 1 and 2 together cover exactly the Must FRs.
- **ID collision across files.** In the addendum, "SM-2 (classic, maps directly to four ratings)" and "hold for Leitner and SM-2" refer to the SuperMemo-2 algorithm, not the PRD's SM-2 acceptance checklist. A tool that links IDs will treat them as the same thing. Write "the SuperMemo-2 algorithm" instead.
- **Assumptions Index round-trip.** There are 25 inline tags and 22 index entries; the FR-3, FR-4 and SM-1/SM-3 entries each combine two tags. Every inline tag is indexed, and every entry has an inline tag. One gap: "at least 10 Flashcards" (FR-7) appears in neither the FR-7 tag nor its entry. Untagged inferences are listed under Scope honesty.
- **Glossary drift.**
  - "wrong" is used for the Grade "incorrect". §1's "Questions answered wrong return in a Retry round" is narrower than the actual rule, since Retry rounds also take partially correct Answers. The same usage appears in UJ-1 and FR-11.
  - "page" is used where Location is meant: §1 "points back to the page it came from", and JTBD 3. For Word and plain text the Location is a heading or a paragraph.
  - "key" is used about 15 times but is not in the Glossary. SM-2 check 3 says "without a paid key", while FR-20 and UJ-5 say "without a key", which is the stronger claim and the one FR-20 tests. Add a "Key" entry and drop "paid".
  - "generated items" is defined inside the Reference entry instead of as its own term. It is used in §4.3, FR-8, SM-3 and SM-C1.
  - Smaller ones: §6 says "the AI" where it means "AI provider", and the Retry round entry says "the round before" where it means "the Quiz before".
- **Trace lines.** FR-4, FR-5, FR-6, FR-9, FR-14, FR-21 and FR-22 inherit "Realizes" from their feature. FR-1 claims only UJ-5, although UJ-1 opens with Ida "Signed in". FR-14 inherits UJ-2, but UJ-2 reviews cards rather than browsing them. No UJ uses a Word file (FR-5).
- **UJ protagonists.** All five are named (Ida in UJ-1–4, Jonas in UJ-5), with context given inline.
- **Required sections.** Everything a solo chain-top PRD needs is present: Vision, users and UJs, Glossary, FRs, NFRs, Non-Goals, MVP scope, Success Metrics with counter-metrics, Open Questions and Assumptions Index.
