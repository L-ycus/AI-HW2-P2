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
      I changed it so that it actually fit for the fanorona game, instead of just minmaxing specific values it now accounts for how the game is set up and returns the best next move based on the heuristic score that I'll implement later. Now that it's based on the board instead of just values, I can check whether the next state has white or black as the current player, if the next_state player and the current player match then you can continue playing (I originally had it stored as a boolean that you'd pass on but I realized that was redunant since you're doing the check each time) otherwise you switch back.

C. How did you verify the fix actually works? Describe with a concrete example, showing that it makes the *correct* choice
   at a point where continuing a capture chain and stopping it lead to
   different outcomes.
      I ran the code in the visualizer and I checked if the agents could perform multiple moves consecutively.

## 2. Your evaluation function

A. Describe what your evaluation function looks at, and why you chose
   those features. If you went through more than one version, say what
   the earlier version got wrong and what you changed.
      When I was learning about the fanorona game I looked up strategies people use to play (I lost a lot of games because I was thinking of it more like checkers where staying on the edges is more beneficial). It was mentioned that people try to stay in the middle of the board / on strong intersections. So my evaluation function iterates through the board checking the value at each position. If it's empty, it skips. Then it returns a sum of the number of your pieces you still have on the board, with an extra weight for those on strong intersections.

B. Having actually built and tested this, what turned out to be the
   hardest part of evaluating a Fanorona position well? (If you
   answered Phase 1's exercise 5 question 4 -- what you expected would
   be hardest, before writing any of this -- say whether that
   prediction held up.)
      Creating the heuristic wasn't incredibly hard but I kept calling the heuristic on the opponent. So after the opponent moved the heuristic would evaluate and return your opponent's strongest position and the agent would act to help the opponent. I also had an issue where it was originally counting empty tiles against the agent which made it prioritize maintaining as many tiles as possible even if they were on subpar / weak positions. 


## 3. Time management

How did you keep `choose_move` inside the time limit? How did you decide it was actually safe --
   i.e. what did you check, not just "it felt fast enough"?
      I added a depth limit, minimax_alpha_beta was only allowed to recusively call itself so many times before it had to make a decision -- it was only allowed  to look up to five moves ahead. I decided it was safe by repeatedly running it was increasingly larger numbers and seeing how long it would take each move / game.

## 4. Testing against `random` and `greedy`

Using `run_many.py`, play 10 games as White and 10 as Black
against each opponent (40 games total), per `exercises.md`. Report all
four counts separately:

| opponent | your color | wins | draws | losses |
|----------|------------|------|-------|--------|
|  random  |   White    |  10  |  0    |    0   |
|  random  |   Black    |  10  |  0    |    0   |
|  greedy  |   White    |   8  |  0    |    2   |
|  greedy  |   Black    |   6  |  0    |    4   |

A. Roughly how did your agent do? If it lost to `greedy` any noticeable fraction of the time, why do you think that's the case -- the search, the evaluation function, or the time budget? How would you tell which one it is?
   I ran the greedy algorithm a few times and my agent was always able to win the majority of the games. You can see if the search algorithm is the issue by increasing the depth, if the winning rate doesn't improve with greater depth that might indicate a problem since greedy doesn't account for long term moves. Examining the amount of time per game could give insight into if your time budget is an issue. Adding print functions to the SIGALRM area could alert you to how often your function runs out of time and if so, you might have to reduce the depth. Also printing out the results of different evaluation functions especially for manual games you can test good or purposefully bad moves and see what the heuristic returns.

B. Did your agent do noticeably better or worse as one color than the other, against either opponent? If so, what's your best guess for why -- something about your evaluation function, your search, or just noise from a sample this size? If you don't see a real difference, say that too.
   At first my agent performed better as black, which meant there was something wrong with my minimax_alpha_beta function because it was prioritizing a specific color rather than prioritizing the agent's moves. I altered my minimax_alpha_beta function to take a parameter that would keep in mind which player the agent is so the heuristic would go from the agent's pov, an issue I mentioned earlier. Now, I think my agent performs relatively similarly regardless of color.

C. Watch at least one game in `match_viewer.py` and give a specific example where your agent's choice surprised you (for better or worse), and your best explanation for why it made that choice.
   Toward the end of a game, my agent had a lot of pieces while my opponent only had a few and both sides stayed on opposing sides of the board. What surprised me was that one of my pieces stayed in a "weaker" board position while one piece was continuously moving around and the other pieces also stayed in "weaker" positions. I'd assume that most of the pieces would want to move toward "stronger" positions as it would be preferred by the heuristic function. I would guess this is because moving to a stronger position leaves it more vulnerable to being captured thus reducing the overall value of such a move. 
      4 pieces staying in place, -> ending heuristic value of 4
      3 pieces staying in place, one in a good spot (5) but gets captured -> ending heuristic value of 3

## AI disclosure

Per the AI policy in `exercises.md`/`CLAUDE.md`: did you ask an AI
assistant any general question about evaluation-function design or
search concepts while working on this phase? If so, for each one, say
what you asked and what you did with the response. ("None" is a
complete answer if true.)
   I google (and got a gemini response) general non-coding related strategies to win fanorona to help gain ideas on how a heuristic might work but I already had some prior ideas based on games like chess where you evaluate the strength of the positions of each piece on the board.
   After building my heuristic and altering my minimax I was facing a really high loss rate I asked "if minimax_alpha_beta is resulting in majority loss what might be the issue", I didn't feed it my code and it didn't provide pseudocode only highlevel phrases like "perspective mixups" and I used that to re-examine my heuristic. I knew my alpha_beta pruning worked in the earlier part so I knew it had to be an issue with my heuristic.