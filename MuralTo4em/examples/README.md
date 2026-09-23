# Examples

Two boards that were converted and imported into the 4EM Modeling Toolkit, kept here as
reference material and as regression input.

Each example comes in three parts:

| File | What it is |
|---|---|
| `*_board.json` | The Mural board as returned by the *Get widgets for a mural* endpoint of the Mural REST API. This is the converter's input. |
| `*_generated.xml` | The AdoXML file produced from that board by `mural_to_4em.py`, ready to be imported into 4EM. |
| `*_4em_reference.xml` | An export of a model with the same content built by hand inside the 4EM Modeling Toolkit, for comparison. |

## goal_model

A Goal Model with nine elements of six classes (Goal, KPI, Problem, Cause, Constraint,
Opportunity) and nine labelled arrows. All nine elements and all nine relations appear in the
imported model with the direction and type drawn on the board. The arrow label `Measured By`
is written as `measured by`, which is the casing 4EM uses.

The hand-built reference model contains one relation more: a second `Contradicts` between the
same two goals in the opposite direction, which was never drawn on the Mural board. That is a
difference between the two source models, not something the conversion loses.

## business_rule_model

A minimal board with two Rule stickies and no arrows. Useful as the smallest case that still
produces a valid import file, and for comparing the generated instance structure against the
attribute structure 4EM itself writes.

Note that the hand-built reference additionally links each Rule to a Process in a Business
Process Model. The Mural board holds no Process stickies, so the generated file contains no
such relation.

## Reproducing

```bash
python3 mural_to_4em.py examples/goal_model_board.json out.xml
diff out.xml examples/goal_model_generated.xml
```

If that diff is not empty, either the palette or one of the attribute templates has changed
since these files were generated. Run `--validate` on the board first to see whether the board
still classifies cleanly.
