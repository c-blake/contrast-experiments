# Contrast Experiments

Tattoy is currently using the [WCAG contrast algorithm provided by the palette crate](https://docs.rs/palette/latest/palette/color_difference/trait.Wcag21RelativeContrast.html). But as @c-blake has rightly pointed out, this doesn't take into account the ratio of visible background pixels to foreground pixels. For example the contrast required for a single fullstop character, ".", is goting to be diffrent from a capital, "B".

Here we can experiment with various ways to calculate optimal contrasts.

## contrastDiff.py
![contrastDiff screenshot](./screenshots/contrastDiff.png)

## contrastRat.py
![contrastRat screenshot](./screenshots/contrastRat.png)
