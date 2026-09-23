# Sticky note palette

Each 4EM class is identified by one `(background colour, shape)` pair. This table is the
human-readable form of `COLOR_SHAPE_TO_CLASS` in `mural_to_4em.py`, which remains the
single source of truth. Colours are given as Mural writes them in its API export, i.e.
eight hex digits with the alpha channel at the end; matching is exact.

`KPI` appears twice because it can belong to either the Goal Model or the Concepts Model.
The two entries are kept apart internally and are written to the generated file under the
same class name.

Open `legend.html` in a browser for the same table with visible colours; use it to build
the legend board in Mural.

## Goal Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#AAED92FF` | rectangle | Goal |
| `#AAED92FF` | circle | KPI |
| `#F6A324FF` | rectangle | Problem |
| `#9EDCFAFF` | rectangle | Cause |
| `#FFFFFFFF` | rectangle | Constraint |
| `#459C5BFF` | rectangle | Opportunity |

## Business Process Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#FFFFFFFF` | circle | Process |
| `#EDEDEDFF` | rectangle | External Process |
| `#FBF9E5FF` | rectangle | Information Set |
| `#EDEDEDFF` | circle | Split (AND) |
| `#F7F7F7FF` | circle | Join (AND) |

## Actors and Resources Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#FEBBBEFF` | rectangle | Individual |
| `#9E7EE6FF` | rectangle | Role |
| `#D4D4D4FF` | rectangle | Resource |
| `#F7F7F7FF` | rectangle | Organizational Unit |

## Concepts Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#E6C003FF` | circle | Concept |
| `#D4D4D4FF` | circle | Attribute |
| `#459C5BFF` | circle | KPI |

## Technical Components and Requirements Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#D8C7FFFF` | circle | IS Technical Component |
| `#9EDCFAFF` | circle | IS Requirement |

## Product-Service-Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#0561A6FF` | rectangle | Unspecific/Product/Service |
| `#2897DCFF` | rectangle | Feature |
| `#F8F7FDFF` | circle | Component |
| `#FCB6D4FF` | rectangle | PartOF (AND) |

## Business Rule Model

| Colour | Shape | 4EM class |
|---|---|---|
| `#B3B3B3FF` | rectangle | Rule |
