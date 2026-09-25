# Tool comparison

Supplementary material for the tool comparison chapter of the seminar paper
*Comparison of Collaborative Modeling Tools and Their Export Capabilities*
(University of Rostock, Chair of Business Information Systems).

Everything is in one workbook: **`Comparison_Criteria_-_AEM.xlsx`**.

Four collaborative modeling tools — Miro, Draw.io, Mural and Lucidchart — were assessed
against 27 criteria derived from six publications. The workbook holds the criteria
themselves, the source each one came from, and the full assessment of every tool with a
justification for each score.

## Criteria

The 27 criteria are grouped into six categories:

| Category | Criteria | Max. score |
|---|---|---|
| Collaboration | 6 | 30 |
| Modeling Features | 5 | 25 |
| Export & Conversion | 4 | 20 |
| Access & Versioning | 3 | 15 |
| Practical Aspects | 3 | 15 |
| Participatory Modeling | 6 | 30 |
| **Total** | **27** | **135** |

Criteria are numbered `C1` to `C27`. The numbering reflects the order in which the criteria
were extracted, not the order of the categories, which is why `C2` and `C9` appear under
Participatory Modeling: that category was added after the first five had been filled, and
both criteria fit it better than the category they were first placed in.

## Sheets

### `Comparison_Criteria`

One row per criterion, grouped by category.

| Column | Content |
|---|---|
| A | Criterion ID (`C1` … `C27`) |
| B | Category |
| C | Criterion |
| D | The guiding question used when assessing a tool against this criterion |
| E | Source publication and page |
| F | The wording taken from that publication, quoted |

Column F is what makes the framework traceable: every criterion can be checked against the
sentence in the source paper it was derived from.

### `Miro_results`, `Draw_io_results`, `Mural Results`, `Lucidchart_results`

One sheet per tool, listing all 27 criteria in the same order, each with:

- the score awarded on a scale from 1 (lowest) to 5 (highest),
- a justification explaining why the tool received that score,
- where available, a link to the vendor documentation or community source backing it.

Category subtotals appear beneath each block, and a summary table on the right of each sheet
gives the score per category, the maximum, and the resulting percentage.

The Mural sheet has one additional column, `Answer`, holding a short yes/partial/no verdict
before the score.

What a score means depends on the criterion, and the justification column states the
reasoning in each case. As an example, for *Built-in communication* a 1 means the tool has no
communication features at all, a 3 basic text messaging, and a 5 full video and audio chat.

### `References`

The six publications the criteria were derived from, with the type of study each one
represents:

| | Publication |
|---|---|
| P1 | Barjis, J. (2011). CPI Modeling: Collaborative, Participative, Interactive Modeling. WSC 2011. |
| P2 | Venter, C. & De Vries, M. (2025). A Functional Classification and Feature Repository for Participative Enterprise Modelling Tools. International Journal of Human-Computer Interaction. |
| P3 | Riemer, K., Holler, J. & Indulska, M. (2011). Collaborative Process Modelling — Tool Analysis and Design Implications. ECIS 2011, Paper 39. |
| P4 | Hao, X. (2023). Examining Collaborative Business Process Modeling Techniques. Journal of Enterprise and Business Intelligence 3(2). |
| P5 | Aleem, S., Lazarova-Molnar, S. & Mohamed, N. (2012). Collaborative Business Process Modeling Approaches: A Review. |
| P6 | Gutschmidt, A., Lantow, B., Hellmanzik, B., Ramforth, B., Wiese, M. & Martins, E. (2022). Participatory modeling from a stakeholder perspective. Software and Systems Modeling 22(1). |

## Results

The totals below are the ones reported in the paper.

| Category | Max | Miro | Draw.io | Mural | Lucidchart |
|---|---|---|---|---|---|
| Collaboration | 30 | 25 | 21 | 25 | 25 |
| Modeling Features | 25 | 17 | 18 | 15 | 20 |
| Export & Conversion | 20 | 12 | 17 | 12 | 15 |
| Access & Versioning | 15 | 14 | 11 | 10 | 12 |
| Practical Aspects | 15 | 11 | 13 | 10 | 10 |
| Participatory Modeling | 30 | 21 | 17 | 25 | 19 |
| **Total** | **135** | **100** | **97** | **97** | **101** |

Draw.io and Mural were selected for the conversion pipelines. The aggregate score was not the
deciding factor: Draw.io was chosen for its unrestricted structured XML export, and Mural as a
contrasting, whiteboard-style environment with the strongest support for participatory
modeling. The reasoning is set out in the paper.

## Related folders

- `../DrawioTo4em` — stencil generator, converter and browser validator for the draw.io pipeline
- `../MuralTo4em` — converter, colour palette and example boards for the Mural pipeline
