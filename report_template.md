# Assignment 2, Phase 2 report

Name:

Fill in every section below, then submit this alongside your completed
`agent_<your-first-name>.<your-last-name>.py`.


## 1. Adapting for "go again"

A. In your own words, explain what the game tree should look like in order to correctly handle a case where the same player can move again. Show through a specific example what should happen instead of alternating MAX and MIN at each move.

B. What did you actually change in your Phase 1 `minimax_alpha_beta` to
   fix this? Describe the change you implemented.

C. How did you verify the fix actually works? Describe with a concrete example, showing that it makes the *correct* choice
   at a point where continuing a capture chain and stopping it lead to
   different outcomes.


## 2. Your evaluation function

A. Describe what your evaluation function looks at, and why you chose
   those features. If you went through more than one version, say what
   the earlier version got wrong and what you changed.

B. Having actually built and tested this, what turned out to be the
   hardest part of evaluating a Fanorona position well? (If you
   answered Phase 1's exercise 5 question 4 -- what you expected would
   be hardest, before writing any of this -- say whether that
   prediction held up.)


## 3. Time management

How did you keep `choose_move` inside the time limit? How did you decide it was actually safe --
   i.e. what did you check, not just "it felt fast enough"?


## 4. Testing against `random` and `greedy`

Using `run_many.py`, play 10 games as White and 10 as Black
against each opponent (40 games total), per `exercises.md`. Report all
four counts separately:

| opponent | your color | wins | draws | losses |
|---|---|---|---|---|
| random | White |   |   |   |
| random | Black |   |   |   |
| greedy | White |   |   |   |
| greedy | Black |   |   |   |

A. Roughly how did your agent do? If it lost to `greedy` any noticeable fraction of the time, why do you think that's the case -- the search, the evaluation function, or the time budget? How would you tell which one it is?

B. Did your agent do noticeably better or worse as one color than the other, against either opponent? If so, what's your best guess for why -- something about your evaluation function, your search, or just noise from a sample this size? If you don't see a real difference, say that too.

C. Watch at least one game in `match_viewer.py` and give a specific example where your agent's choice surprised you (for better or worse), and your best explanation for why it made that choice.


## AI disclosure

Per the AI policy in `exercises.md`/`CLAUDE.md`: did you ask an AI
assistant any general question about evaluation-function design or
search concepts while working on this phase? If so, for each one, say
what you asked and what you did with the response. ("None" is a
complete answer if true.)
