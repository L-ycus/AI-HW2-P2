# Assignment 2, Phase 2 report

Name: Lauryn Hachiya

Fill in every section below, then submit this alongside your completed
`agent_<your-first-name>.<your-last-name>.py`.


## 1. Adapting for "go again"

A. In your own words, explain what the game tree should look like in order to correctly handle a case where the same player can move again. Show through a specific example what should happen instead of alternating MAX and MIN at each move.
   Instead of each level alternating between MAX and MIN at each move, the next move can either be the opposite node or it can be a continuation of the current node if it's still their turn at a second decision.

   For example in fanorona it usually switches between white and black's move but if white ends their turn next to more black pieces (and within the constraints of where they're allowed to move), white can continue their turn in another direction. If white chooses to end their move the game tree would resemble something like black (M) -- white (m) -- black (M), from root to leaf respectively. But if white decides to continue their turn it would look more like black (M) -- white (m) -- white (m). In this case you shouldn't rely on every odd / even layer being MAX / MIN in case someone continues their turn.

B. What did you actually change in your Phase 1 `minimax_alpha_beta` to
   fix this? Describe the change you implemented.
      I changed it so that it actually fit for the fanorona game, instead of just minmaxing specific values it now accounts for how the game is set up and returns the best next move based on the heuristic score that I'll implement later. Now that it's based on the board instead of just values, I can check whether the next state has white or black as the current player, if the next_state player and the current player match then you can continue playing otherwise you switch back.

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
