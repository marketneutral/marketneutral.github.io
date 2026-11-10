---
title: Can an AI exceed its training data?
date: 2026-11-10T00:00:00.000Z
tag: ESSAY
description: >-
  How can a machine trained on human data end up smarter than the humans? Can AI
  be creative? A first-principles answer for readers without a machine learning
  background. Record imperfect human attempts, freeze the data, and ask better
  questions of it. The learner climbs past the average human, past the best
  human, past any walk in the data, and then, once it can check its own ideas,
  past the data itself. Part one of two.
jupyter: python3
execute:
  echo: false
  warning: false
  message: false
fig-format: svg
---

How could superintelligence arise in a machine trained on data that humans produced? It seems impossible, and you will hear the objection put two ways.

> *“AI is just the average of its training data.”*
>
> *“AI can’t do anything it hasn’t seen in its training data.”*

Neither is precise as stated, so here is the sharpest version of each. The first says a model is the mean of what people did. The second comes in a weak form and a strong form. The weak form: at best, a model finds the best thing a person did and copies it. The strong form: a model can only rearrange pieces it has already seen, so it cannot be creative. Put that way, all three are claims about what a learner computes from its data, and they can be tested.

This post builds the smallest world in which to test them. Six hundred people try to cross a small grid, badly, and every step they take is recorded. The recording never changes. Then four learners take their turn, each asking a better question than the last: four rungs on a ladder. The first three read nothing but the frozen recording. The bottom one scores what the crowd scores. The third beats every human, on a route no human walked. The fourth is allowed one new thing: it may try its own ideas in the world and see what happens. It ends up somewhere no human ever stood. It is superhuman in a world of 25 cells, which is a low bar, but the mechanism is the one that matters.

This is the first of two posts. **Each rung has a counterpart in how modern language models are trained**, and each rung below ends with a short note naming it. Some of those matches are tight and some are loose. Part two makes that case in depth. This post is about the mechanism, from first principles, for readers with no background in AI or machine learning.

## The world

A 5×5 grid. Everyone, human or robot, starts at START, and the goal is to reach the TREASURE.

<figure class="diagram">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/world-plot-output-1.svg" alt="The world. Start bottom-left. The treasure can only be entered from its right. The humans’ route runs along the bottom through the mud, up the right edge and across the top. The hatched cell is never visited in the recordings: whenever a person was about to step into it, the recording stopped.">
<figcaption>The world. Start bottom-left. The treasure can only be entered from its right. The humans’ route runs along the bottom through the mud, up the right edge and across the top. The hatched cell is never visited in the recordings: whenever a person was about to step into it, the recording stopped.</figcaption>
</figure>

Cells are named by their coordinates $(x, y)$, counted from the bottom-left corner: $x$ is the column, $y$ is the row, and both start at 0. The start is $(0, 0)$; the treasure is $(2, 4)$; the exit is $(0, 2)$.

- The **treasure** (+10, and the walk ends) is at the top-middle.
- A **safe exit** (+1, and the walk ends) is two steps up from the start.
- Three cells are **fire** (−10, and the walk ends).
- One cell on the bottom row is **mud**: crossing it costs 1 extra point.
- Every step costs half a point, so short routes matter.
- The hatched cell marked **unknown** is not a feature of the world. It is a gap in the recordings.

**A walk’s score is the sum of its steps. Every step costs 0.5. Stepping into the mud costs 1 more. The walk ends when it reaches the treasure (+10), the exit (+1), or a fire (−10).** For example, a ten-step walk through the mud that ends at the treasure scores 10 × (−0.5) − 1 + 10 = **4.0**.

Fire sits on two sides of the treasure, so the only way in is from the cell to its right.

## The people

Six hundred people attempt the grid. Each of them has been told the same route: **“go all the way right along the bottom, up the right edge, then left along the top to the treasure.”** It is the route everyone is taught, and it goes straight through the mud. Nobody has a map. And people err. They misstep, they get turned around, they wander off the route and find their way back to it by habit, and some of those detours run through the middle of the grid without anyone noticing that the middle is a better way.

Here are all six hundred attempts as the log records them, drawn the way people actually walk. The route everyone was taught is the bright band. The faint strands are people who got lost, and the habits that brought them back.

<figure class="diagram">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/humans-paths-output-1.svg" alt="Every one of the 600 attempts, as the log records them, drawn the way a person walks: everyone starts from the same point, each later cell visit lands somewhere near the centre of the cell, and each step wanders a little on the way. Blue walks reached the treasure, red ones ended in fire, amber took the exit. Nearly all of them trace the loop through the mud. The recordings that stop short at its edge are the ones cut there.">
<figcaption>Every one of the 600 attempts, as the log records them, drawn the way a person walks: everyone starts from the same point, each later cell visit lands somewhere near the centre of the cell, and each step wanders a little on the way. Blue walks reached the treasure, red ones ended in fire, amber took the exit. Nearly all of them trace the loop through the mud. The recordings that stop short at its edge are the ones cut there.</figcaption>
</figure>

The humans are not perfect, even when told the plan: each of them veers off course in error, some more often than others, and an error can be fatal. Fire “ends” a walk. Apologies for the morbid turn, but it is simply a feature here, to make sure the data holds many examples that are complete failures. Of the six hundred, 408 reached the treasure, 6 gave up at the exit, and 108 burned, most of them in the fire beside the mud. The remaining 78 recordings stop at the edge of the unknown cell.

Imagine every one of them wore a Garmin. The log is the pile of activity files: where each person was, which way they went, and where they ended up, step by step. The watch does not record points, and it does not need to. Points can be read off the track afterward: half a point for each step, one more for the mud, and the ending scored by where the walk ended, treasure, fire or exit. A single row of the log has four items:

$$
(s, a, r, s') = (\text{cell},\ \text{direction},\ \text{points read off afterward},\ \text{next cell}).
$$

One cell, marked **unknown** on the map, just right of the fire beside the treasure, is missing from every recording. Whenever a person was about to step into it, the watch stopped recording. Seventy-eight recordings end that way. The people kept walking; only the recording stopped. Whatever happens in that cell, the log does not know. This is deliberate, to make the job harder for an eventual AI: the data holds fire where people died, and a part of the map that was never explored.

The scoreboard, starting with the humans. Each person is scored on the walk they actually took, treasure, fire or exit. For the 78 whose recording stopped early, that includes the part the watch never saw.

<img src="2026-11-10-exceed-training-data_files/figure-commonmark/ladder-humans-output-1.svg" id="ladder-humans" />

A walk of the route without a single error scores **4.0**, and that is the tall bar: 152 attempts did exactly that, and twelve more reached 4.0 after errors that happened to cost nothing. Two of those twelve were knocked off the bottom row before the mud, wandered up through the middle and back onto the route above it, and reached the treasure in twelve steps without ever paying for the mud. Neither of them knew. Nobody scored better than 4.0. The average is about **−1.1**, dragged down by a long tail of wasted steps, mud paid twice, and walks into fire.

There are better routes: ten-step routes that skip the mud, worth 5.0, and an 8-step route straight through the middle, worth 6.0. In this crowd nobody walked any of them. **No route worth more than 4.0 appears in the log, the training data.** That is partly arranged: the notebook would delete any recording worth 5.0 or more, to keep the test clean, and for this crowd it had nothing to delete. Rung 2 comes back to this.

## Rung 0: learn to be the average human

Now we bring in the AI. Imagine a little robot. It never sees a map of the grid. It cannot try a route, cannot run a simulation, cannot ask a question. **The only thing the AI has, and can learn from, is the recorded human log.**

One piece of notation first. A **policy** is a rule for choosing a move, written $\pi$. For each cell $s$ it gives a probability to each direction $a$, and $\pi(a \mid s)$ reads “the probability of going $a$ from cell $s$.” The four probabilities in a cell add up to one. A policy can spread its probability over several directions or put all of it on one. **Every learner in this post is a different way of turning the log into a $\pi$.**

The most literal way to learn from people is to become them. For every cell, count which direction the humans went, turn the counts into probabilities, and when you’re in that cell, roll the dice the same way they did. This is **behavioral cloning**, and it is the ordinary meaning of “imitation” \[1\].

$$
\pi_{\text{copy}}(a \mid s) = \frac{\#\{\text{times humans went } a \text{ from } s\}}{\#\{\text{times humans were in } s\}}.
$$

The clone averages **−0.6**, against the humans’ **−1.1**. It is a faithful statistical portrait of the crowd: it takes the outside route through the mud because they did, and in every cell where some humans veered toward fire, it veers toward fire in the same proportion. It has learned *what people do*, and what people do, on average, is lose.

This is the “average of its training data.” The first claim is true of this learner, and it is what a learner gets when the only question it asks of the data is *what did they do here?*

The clone comes out a little ahead of the crowd, and the reason has nothing to do with skill. Stepping into the unknown cell was always a misstep, and it is the one misstep the recordings left out, so the clone never makes it. (Part of the gap in this run is also plain sampling noise across six hundred walks.) Record everything and the gap closes.

<div class="note">

**In a language model: pre-training.** A language model starts by learning to predict the next word of text that people wrote. Sample from it faithfully and you get the crowd back, its knowledge and its mistakes, each in proportion. Counting moves per cell is the same idea with a much smaller table.

</div>

The scoreboard so far. The clone rolls dice, so its walks vary as much as the humans’ do, from disasters to the occasional lucky walk.

<img src="2026-11-10-exceed-training-data_files/figure-commonmark/ladder-0-output-1.svg" id="ladder-0" />

## Rung 1: learn to be the best human

Now the AI tries a different learning strategy. Same counts from the same log, one change: instead of learning each action as the fraction of humans who took it, take the **most common** move in each cell. In rung 0 the AI sampled a move from what the humans did, so its walks had some randomness; here it always takes the majority’s move, so the randomness is gone.

That’s it. No new data. No rewards. No idea what a treasure is. Just: when the humans disagreed about a cell, go with the majority.

<figure class="wide">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/rung1-plot-output-1.svg" alt="Left: rung 0’s policy. Each arrow’s length is the probability of that move, so the arrows in any cell add up to the same total: a 60/40 cell shows two solid arrows, an 85/5/5/5 cell one long arrow and three ticks. Every cell where humans veered toward fire keeps a tick toward fire. Right: rung 1’s policy: the most common move only. It is the humans’ route, walked perfectly, mud included.">
<figcaption>Left: rung 0’s policy. Each arrow’s length is the probability of that move, so the arrows in any cell add up to the same total: a 60/40 cell shows two solid arrows, an 85/5/5/5 cell one long arrow and three ticks. Every cell where humans veered toward fire keeps a tick toward fire. Right: rung 1’s policy: the most common move only. It is the humans’ route, walked perfectly, mud included.</figcaption>
</figure>

The consensus robot scores **4.0**, every time: it never veers, and the world does what it is told. That is a perfect walk of the humans’ route. Only 152 of the 600 human attempts managed it, twelve more got there by luck, and nobody did better. **The AI now matches the best human attempt in the data.** That is the weak form of the second claim made real: find the best thing a person did and copy it. Consensus does exactly that and nothing else. It removes the crowd’s errors and walks the route they were taught, mud included.

Why does this work? Because errors are noise, and noise is different for everyone. In any given cell, one human veered left, another up, a third down, but most of them did the planned thing. The planned thing is what they agree on; their mistakes are what they don’t. Taking the majority keeps the agreement and throws away the mistakes. Six hundred people who each err 10 to 35% of the time contain, collectively, a person who never errs. The clone just has to be decoded the right way to find her.

The consensus robot was trained on nothing but what people did. It never saw a score. It is, in the most literal sense, a model of the training data, and it does on every walk what only 164 of the 600 people managed even once. The average was never the ceiling. It is one of several things you can compute from the same distribution, and the mode is a better one.

This has been measured outside toy worlds. Zhang and co-authors trained a model on nothing but chess games between modest players and found that, when it always played its likeliest move, it could play better than every player in its data \[2\]. They called it transcendence, and their explanation is the one above: individual errors are scattered, so the majority has fewer of them.

<div class="note">

**In a language model: decoding.** Turning the “temperature” down makes a model take its likeliest next word and not a sampled one. Asking the same question many times and keeping the majority answer is the same move at a larger scale. Nothing about the training changes. Only the question asked of it does.

</div>

The scoreboard so far. Consensus never varies: it walks the same route every time.

<img src="2026-11-10-exceed-training-data_files/figure-commonmark/ladder-1-output-1.svg" id="ladder-1" />

## Rung 2: learn to exceed the best human

Look again at a row of the log: $(s, a, r, s')$. Rungs 0 and 1 used the first two entries, where the human was and what they did. They threw away the other half of every row: what it cost, and where it led.

Rung 2 uses the whole row. It asks not *what did people do here?* but *what happened next?*, and it keeps score.

### The table

The learner keeps a table with one entry for every (cell, direction) pair: 25 cells × 4 directions = 100 numbers. Call the entry $Q(s,a)$. It is meant to answer one question: *if I’m in cell $s$ and go direction $a$, how many points will I have collected by the time the episode ends?*

Every entry starts at zero. That is not a belief that every move is worthless; it is *I know nothing yet*. Everything the table will ever contain comes from the log.

### One pass

A pass means: read every row of the log once, and for each row, overwrite one cell of the table with this rule \[3\]:

$$
Q(s, a) \leftarrow r + \max_{a'} Q(s', a').
$$

In words: *the value of going this way from here is the points it paid right now, plus the value of the best move anyone ever made from where you landed.* The word that matters is **max**, and it is a max over single moves, one cell at a time, never over whole walks. Rung 0 took a mean over what people did. Rung 1 took a mode. Rung 2 asks, in each cell, which one move led to the best result from there, and it does not care how many people made that move, only that someone did and it went well. **No human has to have walked the whole route. The route is assembled move by move, from different people’s walks.**

One rule for learning from a fixed log: the max ranges only over moves that appear in the log for cell $s'$. The robot assumes nothing about a move nobody tried.

<div class="note">

**Sidebar: how the maps are scored.** Points are charged for entering a cell, not for standing in it: −0.5 for an ordinary cell, −1.5 for the mud, +9.5 for the treasure. So $r$ is the price of the move about to be made, and $Q(s,a)$ is everything collected from that move onward, its own price included. The maps show, for each cell, the value of the best move out of it. That is why the mud cell will read 6.5, higher than the start’s 5.0: whoever is standing on the mud has already paid, and the treasure is seven moves away. The mud’s penalty lives in the move that enters it. In the cell before the mud, going right is worth −1.5 + 6.5 = 5.0 and going up is worth −0.5 + 6.5 = 6.0, so the route goes up.

</div>

### Watch the value travel

Here is what the table knows after 0, 1, 2, 3, 5 and 10 passes. The number in a cell is the value of the best logged move out of that cell, the one the max picked, not an average and not the value of the cell itself. A cell with one excellent move and three terrible ones shows the excellent one.

<figure class="wide">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/rung2-passes-output-1.svg" alt="The value table after 0, 1, 2, 3, 5 and 10 passes over the log. Each visited cell shows the value of its best logged move, the largest of its four table entries. Value enters at the treasure on pass 1 and travels one cell per pass; cells that have not yet heard from anything good just accumulate step costs.">
<figcaption>The value table after 0, 1, 2, 3, 5 and 10 passes over the log. Each visited cell shows the value of its best logged move, the largest of its four table entries. Value enters at the treasure on pass 1 and travels one cell per pass; cells that have not yet heard from anything good just accumulate step costs.</figcaption>
</figure>

Read the panels in order.

**After 0 passes**, everything is zero. The table has not been told anything.

**After 1 pass**, the table knows one kind of thing: what each move paid immediately. Every ordinary move is worth −0.5, so in most cells that is what shows. Three kinds of move are different. The move from the cell beside the treasure into the treasure paid +9.5, and that cell lights up green. The move from the cell above the exit into the exit paid +0.5. And every move into fire paid −10.5; those entries are in the table too, but never show on the map, because a cell’s best move is never the one into the fire. After one pass the table is a map of immediate consequences and nothing more.

**After 2 passes**, the news spreads one cell. Take the top-right corner. One of its logged moves is Left, into the cell beside the treasure. On pass 1 that move was worth −0.5, like every other move out of the corner. Now the rule adds the step’s −0.5 to the best value in the cell it leads to, which as of the last pass is 9.5. So the move is worth 9.0, it is the corner’s best by a mile, and the corner shows 9.0.

Something smaller happened at the start. On pass 1 the cell above the start learned that going up into the exit is worth +0.5. On pass 2 the start learned that going up into that cell is worth −0.5 + 0.5 = 0.0. The start now believes the best thing it can do is head for the exit, and it will believe that for eight more passes.

**After 3 and 5 passes**, the treasure’s value keeps coming, one cell per pass: down the right edge, then around the corner into the middle row. The green region is the set of cells from which the treasure is at most that many logged moves away. Notice the cells that have heard nothing yet: they get worse each pass, −0.5, then −1.0, then −1.5. A cell that has not heard of anything good can only add up step costs. That is the honest value of wandering.

**After 10 passes**, the news reaches the start. The best route from the start to the treasure is ten moves long, so it takes ten passes for the treasure’s value to arrive. When it does, the start’s Right move is worth 5.0 and the start switches from 0.0 to 5.0. (Its Up move reaches 5.0 on the same pass, by a different ten-move route around the mud. When two moves are worth exactly the same, the robot takes the one that appears more often in the log, which is Right.) Passes 11 through 200 leave every number where it is. The table has converged.

### What the max did

**Five point zero.** Better than the humans’ route walked perfectly. Better than the best walk in the log. On a route that no human walked. That is the weak form of the second claim gone: the robot did not find the best human and copy them. It found something no human did.

<figure class="diagram">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/rung2-plot-output-1.svg" alt="Rung 2. Each visited cell shaded and labeled by the best value any logged move from it achieved. Thin blue: the humans’ route (rung 1). Green: the route the values describe, around the mud, walked by no human, worth 5.0.">
<figcaption>Rung 2. Each visited cell shaded and labeled by the best value any logged move from it achieved. Thin blue: the humans’ route (rung 1). Green: the route the values describe, around the mud, walked by no human, worth 5.0.</figcaption>
</figure>

The route skirts the mud by cutting through the middle of the grid. **No human walked this path.** The training data contained some steps in these directions, a handful of errors by people knocked off the loop, but no human walked the complete path. Here is the route move by move, with the number of times each move appears among the 6,764 steps in the log.

| step | from   | move  | times in the log |
|------|--------|-------|------------------|
| 1    | (0, 0) | right | 657              |
| 2    | (1, 0) | right | 665              |
| 3    | (2, 0) | up    | 69               |
| 4    | (2, 1) | up    | 4                |
| 5    | (2, 2) | right | 4                |
| 6    | (3, 2) | right | 40               |
| 7    | (4, 2) | up    | 535              |
| 8    | (4, 3) | up    | 509              |
| 9    | (4, 4) | left  | 481              |
| 10   | (3, 4) | left  | 408              |

The first two moves and the last four are the humans’ own route, made hundreds of times. Steps 3 to 6 are the detour. Steps 3 and 4 are missteps, two in a row, and the second appears only four times. Steps 5 and 6 are habit, heading back toward the taught route. Nobody who took the detour came out ahead: each of them wasted steps somewhere else, or burned. The max kept the detour and dropped the waste.

This is called **stitching** \[4\]: a learner that values moves by their outcomes can assemble, from fragments of many mediocre episodes, a trajectory better than any episode in the data. The information was in the log. It just was not there as an answer. It was there as consequences, scattered across six hundred people who did not notice.

So: rung 1 matched the best of the humans by finding what they agreed on. Rung 2 beat what they agreed on by finding what *worked*, whether or not anyone agreed on it.

### Is that creative?

Now the strong form of the second claim: a model can only rearrange what it has seen. Look at the table again and concede the point. Every move on the new route is in the log. The robot did not invent a move. It rearranged.

But notice what the concession costs. The claim began as “it can’t do anything it hasn’t seen” and has become “it can’t do anything whose smallest pieces it hasn’t seen.” Those are different claims. Every sentence anyone writes is made of words they have seen, and every proof is made of steps that were already legal. What was not in the data is the route: ten moves in an order no person put them in, scoring more than any person scored. Whether to call that creative is a question about the word. That it is new, and better, is on the scoreboard.

### How much of this was arranged?

Two things, and both deserve saying.

The first is the crowd. I regenerated the six hundred people 40 more times with different random seeds. Rung 2 scored 5.0 on all 40. In 19 of them, though, somebody did walk a 5.0 route by accident, and the notebook deleted that recording before the robot saw it. So “no human walked this path” is a condition I enforced, not a discovery. What the experiment shows is that the robot does not need anyone to have walked it.

The second is coverage. The stitched route rests on moves made four times. Shrink the crowd to 100 people and rung 2 finds a 5.0 route in only 16 of 40 crowds. In the other 24 the pieces are not all there, and it scores 4.0, the same as rung 1. Rung 2 can only stitch what somebody, somewhere, did at least once. And it can trust a move made four times only because nothing in this world is left to chance: a move that paid once pays always. In a world with luck in it, “someone did this and it went well” may mean someone was lucky, and a learner that takes the max will chase the luck. Methods built for real data have to discount for that \[4\].

<div class="note">

**In a language model: learning from feedback.** This is the loosest match of the four. People are shown a model’s answers and say which are better, and the model is trained toward the answers they preferred, not just toward the answers people write. What that shares with rung 2 is the kind of signal: a record of how things turned out, on top of a record of what was done. The machinery is different, and part two looks at how far the comparison holds.

</div>

The scoreboard so far.

<img src="2026-11-10-exceed-training-data_files/figure-commonmark/ladder-2-output-1.svg" id="ladder-2" />

We now have a learner that exceeds the best human. Can a learner do even better? Not from the log. Rung 2 found the best route that can be assembled from the humans’ recordings, and it stopped at 5.0. To go further the robot has to learn something the humans never recorded, and for that it needs one addition to its toolkit: a **verifier**.

## Rung 3: learn what no human knew

Rungs 0 to 2 read a frozen log. This rung does not, and that is the point of it.

What is a verifier here? The grid itself. Until now the robot could only read other people’s recordings. Now it is allowed to walk the grid on its own, Garmin on, and keep the recording. It proposes a route, walks it, and reads off what happened, step by step, including when it burns. Nobody tells it the best route, and nobody tells it where the fire is. The world just answers the one question it has always answered: what happens if I step here? That is all a verifier is: a way to check a proposal against reality without anyone knowing the answer in advance. For a coding AI it is running the tests. For a maths AI it is a proof checker. For a chess AI it is playing the game out. For our robot it is a walk. (One simplification: here the world reports every step’s points, not just the route’s final score. A real checker usually returns one verdict at the end, which makes the learning slower. This post does not show that version.)

Now run the simplest loop there is \[5\]:

1.  **Propose.** Start from the best route you know. Mostly follow it; sometimes take a random step.
2.  **Verify.** Run the proposal. Record what happened, step by step, including when it burns.
3.  **Keep.** Add every verified step to the log.
4.  **Retrain.** Re-run rung 2 on the bigger log.
5.  Repeat.

<figure class="diagram">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/rung3-route-output-1.svg" alt="Rung 3: the route it found, through the cell no human visited.">
<figcaption>Rung 3: the route it found, through the cell no human visited.</figcaption>
</figure>

<figure class="diagram">
<img src="2026-11-10-exceed-training-data_files/figure-commonmark/rung3-score-output-1.svg" alt="The score of the learner’s best route after each round of propose, verify, keep, retrain. It starts from rung 2’s route and finds the best possible one in round 3.">
<figcaption>The score of the learner’s best route after each round of propose, verify, keep, retrain. It starts from rung 2’s route and finds the best possible one in round 3.</figcaption>
</figure>

**Six point zero.** By round 3 the robot has found the 8-step route, through the cell no human ever stood on, and it knows the route is good because it has walked it. Along the way, 105 of its 300 proposals walked into fire. Every one of those was a cheap, verified fact about the world, and not one of them cost a human anything. On rung 2, the only way to learn that a cell was fire was for a person to die in it. On rung 3, the robot buys that knowledge with compute.

This is the rung on which “superhuman” stops being a figure of speech. Rung 1 matched the best human, on every walk, by doing what they all meant to do. Rung 2 beat that by assembling what they stumbled into. Rung 3 goes past the humans’ entire knowledge of the world, because nothing it does is limited to what they did: it can propose anything, and it keeps what checks.

Be clear about what changed, though. Rung 3 did not get more out of its training data. It made more training data. The step into the unknown cell is in no human’s recording; it is in the robot’s own. If the question is whether a learner can exceed the *human* data, rung 3 says yes, with no qualification. If the question is whether it can know something that is in no data at all, the answer is still no. The facts have to come from somewhere, and the verifier is where.

### What the human data was for

Did the humans’ log matter in the end? Run the same loop from an empty log and see. The robot starts knowing nothing, wanders, and finds the exit two steps from the start. One point for stopping beats everything else it has seen, so it settles there, scoring 0.0, and it is still there after fifteen rounds: every proposal is a short walk to the exit with the occasional random step, and none of them gets far enough to find out there is a treasure. The humans’ log is what told the robot a treasure existed, and roughly where. The data got it started. The verifier took it the rest of the way.

That is a fact about this robot’s budget, not a law. A learner that explores harder, for longer, can do without the humans altogether. The famous case is Go. AlphaGo first learned from games between human experts and then improved by playing itself, with the rules of the game as its verifier \[6\]. In its second game against Lee Sedol it played a move, the 37th, that by its own estimate a human would have played one time in ten thousand, and it won. Its successor, AlphaGo Zero, never saw a human game and ended up stronger \[6\]. With a verifier and enough compute, human data is a head start, not a requirement.

<div class="note">

**In a language model: training against a checker.** The model proposes an answer, something checks it (a test suite for code, a proof checker for mathematics, a known answer for a puzzle), and the model is trained on what checked. Where a checker exists the match is tight. Most of what people ask a language model has no checker, and that is where this rung stops. Part two picks it up there.

</div>

## The ladder

The full scoreboard.

<img src="2026-11-10-exceed-training-data_files/figure-commonmark/ladder-output-1.svg" id="ladder" />

## What the ladder says

The claims we started with were that a learner computes the average of its training data, and that at best it copies or rearranges what is in it. The first is true, of rung 0. Each rung above it asks a different question and gets a different answer: the mode instead of the mean, the max over outcomes instead of the mode, and a check instead of a guess.

The second claim came in two forms. The weak form, that a learner can at best copy the best person, fell on rung 2: the same frozen log, and a better route than any person walked. The strong form, that a learner only rearranges what it has seen, is true of rungs 0 to 2 and says less than it sounds like, because the rearrangement beat everyone. On rung 3 it is not even true. The robot stood where no human stood, because it had stopped depending on humans for its facts.

So where does superhuman performance come from? Not from the data alone, and not from a cleverer learner alone. Three different things changed on the way up. From rung 0 to rung 1 the data stayed the same and the *question* changed: the likeliest move, not a sampled one. From 1 to 2 the *signal* changed: outcomes, not just actions. From 2 to 3 the *source* changed: the world, not the recordings. Ask which of those a system has and you know where its ceiling is, and on the top rung there is no ceiling made of human data at all.

The limits are real, and each rung has its own. Consensus is bounded by what the humans intended. It worked here because everyone was attempting the same route and each person’s errors were their own; where a crowd is split, or wrong in the same direction, the majority’s move is no better than the crowd. Outcomes are bounded by what the data covers, as the crowds of 100 showed, and by luck, since a max cannot tell a good move from a fortunate one. That is also why rung 2 refused to assume anything about a move nobody tried: a learner that guesses across an unknown cell in its data can walk confidently into fire. Verification is bounded by the existence of a verifier, and by the cost of being wrong while learning: 105 burned robots are cheap only in a simulation. None of those limits says a learner cannot exceed its data. Each says on which rung, and in which kind of task, the ceiling sits.

“The average of its training data” describes one learner, on one rung, decoded one way. A modern language model is not on one rung. It is pre-trained on rung 0, decoded on rung 1, tuned on human feedback in the spirit of rung 2 and, increasingly, trained against checkers on rung 3. How well each of those matches holds, and what the ladder says about where language models stop, is part two.

## Where this came from

This post owes a lot to two Stanford courses I took: [CS221, *Artificial Intelligence: Principles and Techniques*](https://stanford-cs221.github.io/spring2022/), taught by Tatsunori Hashimoto in spring 2022 \[7\], and [CS224R, *Deep Reinforcement Learning*](https://cs224r.stanford.edu/spring_2025/), taught by Chelsea Finn in spring 2025 \[8\], which contained readings and an assignment on implicit Q-learning (IQL), an offline reinforcement learning method, where the idea came from.

## Reproducibility

- **World:** 5×5; start (0, 0); treasure (2, 4) = +10; exit (0, 2) = +1; fire at (1, 4), (2, 3), (3, 1) = −10; mud at (3, 0) = −1 extra; −0.5 per step; treasure, exit and fire end the episode. Cell (3, 3) is the unknown cell: any recording about to enter it stops there.
- **Humans:** 600 attempts, seed 2024. Shared 10-step route through the mud, with a fixed habitual move back toward the route from each off-route cell (no planning, no map); per-human error rate ε ~ Uniform(0.10, 0.35); errors choose uniformly among the directions that stay on the grid. Each attempt is scored on the full walk; its recording, what the log contains, stops if the human is about to enter the unknown cell (78 of 600). Any recording scoring 5.0 or better is removed before logging. For this seed there was none to remove.
- **Rung 0/1:** per-cell action frequencies; sampled (rung 0, scored on 600 walks, like the humans) or arg-max (rung 1).
- **Rung 2:** tabular Q-learning, 200 sweeps, max restricted to logged moves. Moves of exactly equal value are separated by how often each appears in the log.
- **Other crowds:** seeds 0 to 39, the same construction, with 600 people and with 100; rung 2 re-run on each (30 sweeps). The 5.0 filter removed at least one recording in 19 of the 40 crowds of 600.
- **Rung 3:** 15 rounds × 20 proposals, ε-greedy with ε = 0.3 around the current greedy policy; every verified transition kept; Q-learning re-run each round (60 sweeps). Verifier = the real grid. Repeated from an empty log as a control.
- **Runtime:** about a minute on one CPU core.
- **Source:** the notebook that produced every number and figure above is [in the blog’s repository](https://github.com/marketneutral/marketneutral.github.io/blob/main/notebooks/2026-11-10-exceed-training-data.qmd).

## References

1.  Pomerleau, D. A. (1989). *ALVINN: An autonomous land vehicle in a neural network.* NeurIPS 1.
2.  Zhang, E., Zhu, V., Saphra, N., Kleiman, A., Edelman, B. L., Tambe, M., Kakade, S. M., & Malach, E. (2024). *Transcendence: Generative Models Can Outperform The Experts That Train Them.* NeurIPS 2024. <https://arxiv.org/abs/2406.11741>
3.  Watkins, C. J. C. H., & Dayan, P. (1992). *Q-learning.* Machine Learning 8, 279–292.
4.  Levine, S., Kumar, A., Tucker, G., & Fu, J. (2020). *Offline Reinforcement Learning: Tutorial, Review, and Perspectives on Open Problems.* arXiv:2005.01643. Kumar, A., Hong, J., Singh, A., & Levine, S. (2022). *When Should We Prefer Offline RL to Behavioral Cloning?* ICLR 2022.
5.  Anthony, T., Tian, Z., & Barber, D. (2017). *Thinking Fast and Slow with Deep Learning and Tree Search.* NeurIPS 2017. Zelikman, E., Wu, Y., Mu, J., & Goodman, N. (2022). *STaR: Bootstrapping Reasoning With Reasoning.* NeurIPS 2022. <https://arxiv.org/abs/2203.14465>
6.  Silver, D., et al. (2016). *Mastering the game of Go with deep neural networks and tree search.* Nature 529, 484–489. Silver, D., et al. (2017). *Mastering the game of Go without human knowledge.* Nature 550, 354–359.
7.  Hashimoto, T., et al. (2022). *CS221: Artificial Intelligence: Principles and Techniques.* Stanford University, Spring 2022. <https://stanford-cs221.github.io/spring2022/>
8.  Finn, C., et al. (2025). *CS224R: Deep Reinforcement Learning.* Stanford University, Spring 2025. <https://cs224r.stanford.edu/spring_2025/>
