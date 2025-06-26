# Contrast Experiments

Tattoy is currently using the [WCAG contrast algorithm provided by the palette crate](https://docs.rs/palette/latest/palette/color_difference/trait.Wcag21RelativeContrast.html). But as @c-blake has rightly pointed out, this doesn't take into account the ratio of visible background pixels to foreground pixels. For example the contrast required for a single fullstop character, ".", is goting to be diffrent from a capital, "B".

Here we can experiment with various ways to calculate optimal contrasts.

## contrastDiff.py
![contrastDiff screenshot](./screenshots/contrastDiff.png)

## contrastRat.py
![contrastRat screenshot](./screenshots/contrastRat.png)

## contrast.py w/cb palette
![cbPalette screenshot](./screenshots/cbPalette.png)

Counter-examples of `ScoreA > ScoreB` => A Easier to Read than B (by subjective
perception) is evidence against utility of any score measuring legibility.

I find pretty bad counter-examples to all 4 proposed formulae.  A more thorough
way to rank proposals would be to systematically go through all 1024 cases and
count "inversions".  I didn't have the patience to do that, mostly just thinking
"none are perfect/great".  Basically, I don't see any good way to assign a
threshold that will admit only good color combinations and reject only bad for
any of these 4 metrics.  I do like the "difference" ones better than "ratio"
because there is no fudge term/factor pulled form thin air seemingly in defiance
of the primary research trying to get a linear lightness scales.

Anyway, here are counter examples according to my eyeballs/brain.  My notation
is score@rowColorNum,columnColorNum, e.g. 1.6@0,4 = score1.6, black bg, blue fg
for the first table.

 - First Table:  (./contrast.py 240 RY)

   + 1.6@0,4 harder to read than 1.4@7,9 & marginally harder than inverse (9,7)

   + 1.2@3,9 seems easier than 1.6@0,4

 - Second Table: (./contrast.py 240 RL)

   + 4.8@0,4 seems harder to read than MANY lesser scored cells - literally
     half the table.  Probably this means minL=.05 is a horrible choice for
     L* value ranges.  Given that it was clearly "just some round number near
     but below the lightness score of 4", this *really* begs the question of
     setting minL more systematically or dropping *ratio* of lightness in
     favor of |diff|.

   + To side-step doing all that, but still evaluate the score, just consider
     the 4x4 sub-matrix (6789,6789) where all the L* values are "mid-range"
     0.3615..0.6961, i.e. much > 0.05.  I *still* see the metric fail in that
     1.6@9,8 seems harder to read than 1.3@6,7 *or* 7,6. (Admittedly, this one
     may relate more to the fact that the matrix should not be symmetric since
     pixel area varies across polarity so much in most fonts.)

 - Third Table: DY

   + .03@0,4 harder to read than .01@4,9

   + slew of same-scored 0.11 with wildly different legibility.

   + .13 @14,11 way worse than either 6,5 or 5,6 (cyan purple)

   + .07 @8,2 or 2,8 seem way easier to read than .13@2,9 (or 9,2)

 - Fourth Table: DL

   + .16@5,6 easier than .19@0,4

   + .09@9,6 not so bad either.

   + .10 @8,2 or 2,8 seem way easier to read than .14@2,9 (or 9,2)
