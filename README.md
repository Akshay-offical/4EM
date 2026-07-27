# 4EM Draw.io Integration Toolkit

Convert draw.io diagrams into **4EM (For Enterprise Modelling)** ADL files and use custom draw.io stencils for all 7 4EM sub-models. This toolkit enables enterprise architects and business analysts to create 4EM models visually in draw.io, then import them directly into the 4EM modeling tool — either through a CLI converter, or through a browser tool that validates connections live while you draw and exports a full multi-view ADL file.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Supported 4EM Models](#supported-4em-models)
- [Installation](#installation)
- [Quick Start](#quick-start)
  * [Option A — Browser Tool (v4, recommended for new diagrams)](#quick-start-browser)
  * [Option B — CLI Converter](#quick-start-cli)
- [Version Evolution](#version-evolution)
  * [v1 — Foundation](#v1--foundation-goal-model-only)
  * [v2 — Multi-Model Support](#v2--multi-model-support)
  * [v3 — Production-Ready](#v3--production-ready-recommended)
  * [v4 — Multi-View & Live Validation (Browser-Based)](#v4--multi-view--live-validation-browser-based--latest)
- [File Structure](#file-structure)
- [How It Works](#how-it-works)
  * [Draw.io XML Format](#drawio-xml-format)
  * [4EM ADL Format](#4em-adl-format)
  * [Key Technical Challenges](#key-technical-challenges)
- [Detailed Usage Guide](#detailed-usage-guide)
  * [Step 1 — Generate Stencils](#step-1--generate-stencils)
  * [Step 2 — Load Stencils into Draw.io](#step-2--load-stencils-into-drawio)
  * [Step 3 — Create Your Diagram](#step-3--create-your-diagram)
  * [Step 4 — Convert to ADL](#step-4--convert-to-adl)
  * [Step 5 — Import into 4EM](#step-5--import-into-4em)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)

---

## Overview

The **4EM toolkit** bridges the gap between draw.io's intuitive visual editor and the 4EM enterprise modeling tool. It provides:

1. **Custom draw.io stencils** for all 7 4EM sub-models with proper shapes, colors, and semantics
2. **Automated converters** that transform draw.io diagrams into 4EM ADL (plain text) format — as a CLI script, or as a self-contained browser tool
3. **Validation & auto-detection** of model types and relation types — checked live while drawing (v4) as well as during conversion
4. **Multi-view ADL output** (v4) — one block per populated sub-model plus a general view containing every intermodel relation, matching how 4EM's own exports are actually structured
5. **Production-ready workflow** with `em_type` metadata for robust, user-friendly conversion

### Why This Toolkit?

| Benefit | Description |
| --- | --- |
| 🎨 **Visual modeling** | Use draw.io's powerful diagram editor instead of 4EM's limited UI |
| 🎯 **Consistency** | Pre-built stencils ensure correct 4EM semantics and styling |
| ✅ **Validation** | Auto-detect model types, validate relation types, catch errors early — live, while drawing, not just after conversion |
| 🧩 **Multi-model in one file** | A single diagram can span several 4EM sub-models and still export correctly, with intermodel relations preserved |

---

## Supported 4EM Models

All 7 4EM sub-models are fully supported:

| Model | Stencil | CLI Converter | Browser Tool (v4) |
| --- | --- | --- | --- |
| Goal Model | ✅ | ✅ | ✅ |
| Business Process Model | ✅ | ✅ | ✅ |
| Actors and Resources Model | ✅ | ✅ | ✅ |
| Concepts Model | ✅ | ✅ | ✅ |
| Product-Service Model | ✅ | ✅ | ✅ |
| Technical Components and Requirements Model | ✅ | ✅ | ✅ |
| Business Rule Model | ✅ | ✅ | ✅ |

---

## Installation

### Prerequisites

- **Python 3.7+** — standard library only, no external dependencies (needed for the CLI converter and stencil generator)
- **A modern web browser with an internet connection** — needed for the v4 browser tool, which embeds the real draw.io editor and auto-loads stencils from this repo
- **draw.io Desktop** or access to [app.diagrams.net](https://app.diagrams.net) — only needed if you're using the CLI workflow's manual "Open Library from Device" step (v1–v3 style), or if you want real-time multi-user collaboration (see [Limitations](#limitations))
- **4EM tool** — for importing the generated ADL files

### Setup

```
# Clone the repository
git clone https://github.com/Akshay-offical/4EM.git
cd 4EM

# No pip install needed — uses Python standard library only
python --version  # Should be 3.7 or higher
```

---

## Quick Start

<a name="quick-start-browser"></a>
### Option A — Browser Tool (v4, recommended for new diagrams)

```
# 1. Just open the file - no build step, no server needed
open 4em_drawio_validator.html   # or double-click it in your file browser

# 2. All 7 stencils load automatically in the sidebar - nothing to do here

# 3. Draw your diagram. Connections get checked live against the
#    relation rulebook as you draw - a popup tells you immediately
#    if a connection isn't valid, and what would be valid instead.

# 4. Click "Convert to ADL & Download" - this produces a multi-view
#    ADL file (one block per sub-model your diagram touches, plus a
#    [view] 4EM_General block with every intermodel relation).

# 5. Import the downloaded .adl file into 4EM as usual.
```

<a name="quick-start-cli"></a>
### Option B — CLI Converter

```
# 1. Generate stencils (v4 recommended)
cd src
python build_stencil_v4.py

# 2. Open draw.io and load a stencil
#    File → Open Library from → Device
#    Select: generated_stencils/4EM_GoalModel_Stencil_v4.xml (repeat for each model you need)

# 3. Create your diagram in draw.io, then export as .drawio.xml

# 4. Convert to ADL (multi-view by default)
python drawio_to_4em_v4_multiview.py ../sample_drawio/Goal_Model.drawio.xml ../adl_outputs/Goal_Model.adl

# 5. Import into 4EM
#    File → Import → Select the .adl file
```

---

## Version Evolution

### v1 — Foundation (Goal Model Only)

**Purpose:** Proof of concept — demonstrates basic draw.io → 4EM conversion for Goal Model only.

#### Key Features

- Manual `"Type: Name"` label format (e.g. `"Goal: Maximize Quality"`)
- Basic stencils for Goal Model elements
- Pixel-to-centimeter coordinate conversion
- Tooltip → Description field mapping
- Edge label extraction (including separate floating label cells)

#### Limitations

- Only supports Goal Model
- Hardcoded model type — no auto-detection
- No relation type validation
- No handling of connector nodes (AND/OR, Split/Join)

#### Files

| File | Purpose |
| --- | --- |
| `src/build_stencil_v1.py` | Basic stencil generator |
| `src/drawio_to_4em_v1.py` | Basic Goal Model converter |

---

### v2 — Multi-Model Support

**Purpose:** Production prototype — adds support for all 7 4EM models with auto-detection and validation.

#### Key Features

- All 7 4EM models supported
- Auto-detection of model type from node labels
- Relation type validation against confirmed 4EM enums
- Anonymous node handling — Split/Join/ISA/PartOF get auto-numbered unique names
- Flow connector detection — edges to/from Split/Join automatically have empty `Type`
- Per-type attribute templates — each node type gets its correct 4EM attributes
- Command-line arguments (`--model-type`, `--model-name`)
- Enhanced stencils with diamonds (AND/OR/Split/Join), hexagons (helper nodes), distinct colors

#### New Node Types Added in v2

| Model | New Types |
| --- | --- |
| Goal Model | AND, OR, AND/OR, Development Action, Assumption, Comment |
| Business Process | Split (OR), Join (OR), helper nodes |
| Actors & Resources | Partial-ISA, Total-ISA, Partial-PartOF, Total-PartOF |
| Concepts | ISA/PartOF taxonomy nodes |
| Product-Service | PartOF (OR), PartOF (XOR), ISA nodes |
| Technical | Goal, Problem, AND/OR logic, PartOF nodes |
| Business Rule | AND, OR, AND/OR logic nodes |

#### Files

| File | Purpose |
| --- | --- |
| `src/build_stencil_v2.py` | Multi-model stencil generator |
| `src/drawio_to_4em_v2.py` | Multi-model converter with auto-detection |

---

### v3 — Production-Ready (Recommended for single-model diagrams)

**Purpose:** Industrial-strength solution with `em_type` metadata for robust, user-friendly conversion.

#### 🎯 Major Breakthrough: `em_type` Attribute

**The Problem (v1/v2) — fragile label parsing:**

```
<!-- User must type the prefix exactly right -->
<mxCell value="Goal: Maximize Service Quality" .../>
```

```
# Converter parses the label prefix — any typo breaks conversion
ntype, name = value.split(":", 1)
```

**The Solution (v3) — type baked into shape metadata:**

```
<!-- Stencil has em_type built in -->
<UserObject label="<name>" em_type="Goal" id="2">
  <mxCell vertex="1" .../>
</UserObject>

<!-- User just renames the label — no prefix needed -->
<UserObject label="Maximize Service Quality" em_type="Goal" id="2">
  ...
</UserObject>
```

```
# Converter reads em_type directly — immune to typos
em_type = cell.get("em_type")  # Always "Goal", no parsing needed
```

#### Key Features (All v2 Features + Enhancements)

- **`em_type` metadata** — node type is baked into the shape, not parsed from the label
- **Simplified labeling** — users just type the name, no `"Type: "` prefix required
- **Typo-proof** — can't accidentally break conversion by misspelling the type
- **Duplicate handling** — fixed bug where multiple nodes of the same type collided
- **Custom shapes** — accurate 4EM visual styling:
  * `leftcut` (`flowchart.card`) for Role/Individual
  * `circle` (`ellipse`) for ISA taxonomy nodes
  * `square` (`rounded=0`) for PartOF taxonomy nodes
  * `chevron` (`blockArrow`) for Development Action
- **Official 4EM colors** — matches the 4EM tool palette exactly
- **Robust anonymous node naming** — handles edge cases where label duplicates type name

#### v1/v2 vs v3 Comparison

| Aspect | v1 / v2 | v3 |
| --- | --- | --- |
| Label format | `"Goal: My Goal"` (must type prefix) | `"My Goal"` (just the name) |
| Typo risk | High — `"Gola: X"` breaks conversion | Zero — type is metadata |
| User experience | Manual, error-prone | Drag-and-drop, rename |
| Duplicate nodes | Bug (all collapse to one instance) | Fixed (unique auto-numbering) |
| Visual accuracy | Generic shapes | Official 4EM colors & shapes |
| Robustness | Fragile string parsing | Metadata-driven |

#### Files

| File | Purpose |
| --- | --- |
| `src/build_stencil_v3.py` | Production stencil generator with `em_type` |
| `src/drawio_to_4em_v3.py` | Production converter with duplicate-handling fix |

---

### v4 — Multi-View & Live Validation (Browser-Based) ⭐ (Latest)

**Purpose:** Move validation *before* conversion instead of after it, and stop treating a 4EM model as belonging to a single sub-model — because real 4EM files don't work that way.

#### 🎯 Major Breakthrough: Live Validation Inside the Editor Itself

**The Problem (v1–v3) — you only find out something's wrong after converting:**

```
$ python drawio_to_4em_v3.py MyModel.drawio.xml MyModel.adl
NOTE: relation Type 'resp' is not a confirmed valid value for 'Actors and Resources Model'
      (known values: , belongs to, interacts with, ...). Moved into Description, Type left blank.
```
By the time you see this, you've already drawn the whole diagram. Fixing a bad connection means going back into draw.io, finding the edge, fixing it, exporting again, re-running the converter, and re-checking the output — every time.

**The Solution (v4) — the check happens the moment you draw the connection:**

A single self-contained HTML file (`4em_drawio_validator.html`) embeds the real draw.io editor via `<iframe src="https://embed.diagrams.net/?embed=1&configure=1&proto=json&libraries=1">` and talks to it over `window.postMessage` (JSON-encoded, since draw.io's embed API supports a couple of different wire formats and `proto=json` picks this one explicitly). draw.io has no "a connection was just made" event, so instead the tool listens for `autosave` — which fires the *entire* current diagram XML on every edit — and re-parses it each time, comparing every edge's `source|target|label` against what it saw last time so it only re-checks what actually changed:

```js
window.addEventListener("message", function(evt) {
  var msg = JSON.parse(evt.data);
  if (msg.event === "autosave") checkDiagram(msg.xml);
});
```

If a connection doesn't match anything in the professor's 349-entry relation rulebook (parsed once out of his 4EM macro script — the same script this whole project is meant to feed data into), a popup appears immediately:

> **Connection not possible**
> Resource → Process (labeled: "resp")
> Possible connections are: `performs`

No conversion round-trip required to find out.

#### Key Features (All v3 Features + Enhancements)

- **Stencils auto-load** — no more manual "File → Open Library from → Device" per model; all 7 (now v4) stencils load automatically via draw.io's `defaultCustomLibraries` config, fetched straight from this repo's raw GitHub URLs
- **Live relation validation** — every connection checked against the professor's rulebook while you draw, not after
- **Multi-view ADL export** — see the breakthrough below; this is the biggest structural change since v3
- **Intermodel-Relations attribute populated** — the per-node panel 4EM shows for cross-model links (previously always blank in v1–v3's output)
- **Per-view position normalization** — each sub-model view gets its own self-contained layout instead of inheriting wherever that cluster happened to sit on the shared draw.io canvas
- **Sub-type attribute support** — Rule (4 types), IS Requirement (2 types), Product-Service's Specification (3 types), and Problem (Problem/Weakness/Threat) can all be set by dragging a dedicated stencil variant, instead of always getting a hardcoded default
- **Cache-busted stencil loading** — every page load appends a fresh timestamp to each stencil URL, so pushing an update to this repo is reflected immediately instead of waiting out GitHub's CDN cache
- **The CLI workflow still exists** — `drawio_to_4em_v4_multiview.py` mirrors the browser tool's logic exactly (verified byte-for-byte identical output on every test diagram used during development); v4 adds a browser option, it doesn't remove the script

#### 🎯 Second Major Breakthrough: Multi-View Output

**The Problem (v1–v3) — one auto-detected model, everything else silently discarded:**

```
Auto-detected model type: 'Actors and Resources Model' (votes: {'Actors and Resources Model': 5})
Converted 9 nodes and 11 relations as 'Actors and Resources Model'.
```
If your diagram had 5 Goal nodes and 4 Actors & Resources nodes, the Goal nodes got forced into an `Actors and Resources Model` block anyway — wrong `TYPE`, wrong relation enum checked against them, and any relation crossing between two different sub-models (e.g. `Role → Goal`, "is responsible for") had nowhere valid to go.

**The Solution (v4) — one block per populated sub-model, plus a general view:**

A real 4EM export was pulled apart to confirm this structurally: 4EM doesn't have a special "view" object at all. It's just multiple `BUSINESS PROCESS MODEL <name>` blocks in one file, and 4EM matches the *same* `INSTANCE <Name> : <Type>` across blocks purely by name + type. Counting instances/relations in a real file proved it: the union of all 7 sub-models' instance counts equals `[view] 4EM_General`'s count exactly (44 = 44), while General's relation count was 13 *more* than the sum of the individual views — exactly the relations whose two ends live in different sub-models.

```
Converted 63 nodes across 3 sub-model view(s) + 1 general view:
  4EM_Goal (Goal Model): 20 nodes, 23 relations
  4EM_Actors and Resources (Actors and Resources Model): 24 nodes, 25 relations
  4EM_Technical Components and Requirements (Technical Components and Requirements Model): 19 nodes, 18 relations
  [view] 4EM_General: 63 nodes, 66 relations (0 intermodel)
```

A node like `Improve Service : Goal` now appears in **both** `4EM_Goal` and `[view] 4EM_General` — same name, same type, matched by 4EM as the same object, but with independent `Position` values in each (confirmed from the real export: the same node genuinely sits at different coordinates in different views).

#### v3 vs v4 Comparison

| Aspect | v1 / v2 / v3 | v4 |
| --- | --- | --- |
| Validation timing | After conversion (console warnings) | While drawing (live popup) + after conversion |
| Model scope | One auto-detected model, rest discarded | Every populated sub-model, plus a general view with intermodel relations |
| Stencil loading | Manual, per file, per session | Automatic, all 7, every time the tool opens |
| Intermodel relations | Not representable at all | Included in general view + written into each node's own Intermodel-Relations attribute |
| Node layout per view | N/A (only one view existed) | Each view self-contained; general view keeps your real layout |
| Sub-type fields (Rule/IS Requirement/Specification/Problem) | Always the hardcoded default | Selectable via dedicated stencil shapes |
| Interface | Python CLI only | Browser tool (primary) + Python CLI (kept in sync, same output) |
| Where the logic runs | Your machine, on demand | Your browser, live, or your machine via the CLI |

#### New/Changed Node Handling in v4

| Model | Change |
| --- | --- |
| All 7 models | `Development Action` removed |
| Technical Components and Requirements | `Goal` and `Problem` removed (they don't belong there — this also surfaced a stale entry in the model-membership table that had wrongly let them "leak" into that model) |
| Product-Service | `Feature`'s shape changed from a slanted parallelogram to a proper trapezoid (`shape=trapezoid;perimeter=trapezoidPerimeter`) |
| Business Rule | `Rule` now has 4 draggable variants (Derivation / Event-action / Static Constraint / Transition Constraint Rule), each pre-setting the ADL `Type` attribute |
| Technical Components and Requirements | `IS Requirement` now has 2 draggable variants (Functional / Nonfunctional) |
| Product-Service | `Unspecific/Product/Service` now has 3 draggable variants (Unspecific / Product / Service), each pre-setting the `Specification` attribute |
| Goal Model | `Problem` now has 3 draggable variants (Problem / Weakness / Threat) |

```
$ python build_stencil_v4.py
  Written: generated_stencils/4EM_GoalModel_Stencil_v4.xml        (18 shapes)
  Written: generated_stencils/4EM_BusinessProcess_Stencil_v4.xml  (15 shapes)
  Written: generated_stencils/4EM_ActorsResources_Stencil_v4.xml  (19 shapes)
  Written: generated_stencils/4EM_Concepts_Stencil_v4.xml         (14 shapes)
  Written: generated_stencils/4EM_ProductService_Stencil_v4.xml   (14 shapes)
  Written: generated_stencils/4EM_Technical_Stencil_v4.xml        (15 shapes)
  Written: generated_stencils/4EM_BusinessRule_Stencil_v4.xml     (14 shapes)

  All 7 stencils created successfully!
```

#### Files

| File | Purpose |
| --- | --- |
| `4em_drawio_validator.html` | Browser tool: embeds draw.io, auto-loads stencils, live-validates connections, converts to multi-view ADL — no install, open the file directly ⭐ |
| `src/build_stencil_v4.py` | Stencil generator with sub-type variants and the 3 explicit shape/removal changes above |
| `src/drawio_to_4em_v4_multiview.py` | CLI multi-view converter — logic verified identical to the browser tool on every test diagram |

---

## File Structure

```
4EM/
├── README.md
├── 4em_drawio_validator.html          # v4: self-contained browser tool ⭐
├── DrawioTo4em/
│   ├── src/
│   │   ├── build_stencil_v1.py            # v1: Basic stencil generator (Goal Model only)
│   │   ├── build_stencil_v2.py            # v2: Multi-model stencils
│   │   ├── build_stencil_v3.py            # v3: Production stencils with em_type
│   │   ├── build_stencil_v4.py            # v4: + sub-type variants, node/shape changes ⭐
│   │   ├── drawio_to_4em_v1.py            # v1: Basic converter (Goal Model only)
│   │   ├── drawio_to_4em_v2.py            # v2: Multi-model converter with auto-detection
│   │   ├── drawio_to_4em_v3.py            # v3: Production converter with duplicate fix
│   │   └── drawio_to_4em_v4_multiview.py  # v4: Multi-view converter (mirrors the browser tool) ⭐
│   ├── generated_stencils/
│   │   ├── 4EM_GoalModel_Stencil_v2.xml
│   │   ├── 4EM_GoalModel_Stencil_v3.xml
│   │   ├── 4EM_GoalModel_Stencil_v4.xml
│   │   ├── 4EM_BusinessProcess_Stencil_v4.xml
│   │   ├── 4EM_ActorsResources_Stencil_v4.xml
│   │   ├── 4EM_Concepts_Stencil_v4.xml
│   │   ├── 4EM_ProductService_Stencil_v4.xml
│   │   ├── 4EM_Technical_Stencil_v4.xml
│   │   ├── 4EM_BusinessRule_Stencil_v4.xml
│   │   └── ... (earlier v2/v3 files kept for reference)
│   ├── sample_drawio/
│   │   ├── Goal_Model_V3.drawio.xml
│   │   ├── Actors_Resources_V3.drawio.xml
│   │   └── ...
│   └── adl_outputs/
│       ├── Goal_Model_V3.adl
│       └── ...
└── MuralTo4em/
    └── ... (separate Mural-based converter, not covered by this README)
```

---

## How It Works

### Draw.io XML Format

Draw.io stores diagrams as XML. Here is a simplified example showing the v3/v4 format:

```
<mxfile host="app.diagrams.net">
  <diagram name="Goal Model" id="goal-model">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- v3/v4: UserObject carries em_type metadata -->
        <UserObject label="Maximize Service Quality" em_type="Goal" id="2">
          <mxCell style="rounded=0;fillColor=#B6DFA0;strokeColor=#000000;"
                  vertex="1" parent="1">
            <mxGeometry x="150" y="180" width="160" height="60" as="geometry"/>
          </mxCell>
        </UserObject>

        <UserObject label="Customer Satisfaction Score" em_type="KPI" id="3">
          <mxCell style="shape=mxgraph.flowchart.terminator;fillColor=#B6E8A2;"
                  vertex="1" parent="1">
            <mxGeometry x="430" y="180" width="160" height="60" as="geometry"/>
          </mxCell>
        </UserObject>

        <!-- Edge connecting the two nodes -->
        <mxCell id="4" value="measured by"
                style="edgeStyle=orthogonalEdgeStyle;"
                edge="1" source="2" target="3" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

**Key observations:**

- Every element is an `<mxCell>` (or `<UserObject>` wrapping `<mxCell>` in v3/v4)
- Boxes have `vertex="1"` with `<mxGeometry>` storing `x`, `y`, `width`, `height` in **pixels**
- Arrows have `edge="1"` with `source` and `target` pointing to endpoint box IDs
- `id="0"` and `id="1"` are internal draw.io housekeeping cells — always ignored
- In v3/v4, `em_type` stores the 4EM node type; the `label` holds only the user's name
- In v4, some shapes also carry an extra custom attribute (`rule_type`, `req_type`, `specification`, `problem_type`) for sub-type selection — see Key Technical Challenge #11 below

---

### 4EM ADL Format

4EM's ADL (Abstract Data Language) is a structured plain-text format:

```
VERSION <4.0>

BUSINESS PROCESS MODEL <4EM_Goal> : <4EM 2.7>
VERSION <>
TYPE <Goal Model>

    ATTRIBUTE <Author>
    VALUE "Converter"

    ATTRIBUTE <Description>
    VALUE "Converted from draw.io"

INSTANCE <Maximize Service Quality> : <Goal>

    ATTRIBUTE <Position>
    VALUE "NODE x:4.0cm y:4.8cm w:4.2cm h:1.6cm index:1"

    ATTRIBUTE <Description>
    VALUE ""

    ATTRIBUTE <Intermodel-Relations>
    VALUE

    ATTRIBUTE <Decomposition>
    VALUE ""

    ATTRIBUTE <Defined by>
    VALUE ""

    ATTRIBUTE <Attributes>
    VALUE

RELATION <4EM_Relation>
    FROM <Maximize Service Quality> : <Goal>
    TO <Customer Satisfaction Score> : <KPI>

    ATTRIBUTE <Positions>
    VALUE "EDGE 0 index:1"

    ATTRIBUTE <Type>
    VALUE "measured by"

    ATTRIBUTE <Description>
    VALUE ""

    ATTRIBUTE <IR>
    VALUE "False"
```

**Key observations:**

- `INSTANCE <name> : <type>` — name and type are separate (not `"Type: Name"`)
- Positions use **centimetres**, not pixels (96 DPI conversion: `px ÷ 37.8`)
- Relations reference nodes by `name + type`, not by numeric ID
- Specific mandatory `ATTRIBUTE` blocks are required even when empty
- ADL is plain text — easy to diff, version-control, and grep
- (v4) A single `.adl` file can contain **multiple** `BUSINESS PROCESS MODEL` blocks — one per sub-model, plus a `[view] 4EM_General` block — and 4EM matches the same instance across blocks by `name + type` alone; see Key Technical Challenge #8

---

### Key Technical Challenges

#### 1 — Extract Type and Name from Label (v1/v2) or Metadata (v3/v4)

**v1/v2 — fragile string parsing:**

```
value = "Goal: Maximize Service Quality"
ntype, name = value.split(":", 1)
# ntype = "Goal"
# name  = "Maximize Service Quality"
```

**v3/v4 — robust metadata read:**

```
em_type = cell.get("em_type")   # "Goal" — baked into the shape
label   = cell.get("label")     # "Maximize Service Quality" — user's text
ntype   = em_type
name    = label if label else em_type
```

---

#### 2 — Convert Pixels to Centimetres

Draw.io stores: `<mxGeometry x="150" y="180" width="160" height="60"/>`
4EM needs: `VALUE "NODE x:4.0cm y:4.8cm w:4.2cm h:1.6cm index:1"`

```
PX_PER_CM = 37.8  # 96 DPI ÷ 2.54 cm/inch

def px_to_cm(px):
    return round(float(px) / PX_PER_CM, 1)
```

---

#### 3 — Resolve Edge Endpoints from IDs to Names

Draw.io stores: `<mxCell id="4" edge="1" source="2" target="3" value="measured by"/>`

4EM needs:

```
FROM <Maximize Service Quality> : <Goal>
TO   <Customer Satisfaction Score> : <KPI>
```

**Solution:** Parse all nodes first (building `id → {type, name}` dict), then process edges using that lookup.

---

#### 4 — Edge Labels Stored as Separate Child Cells

Sometimes draw.io stores an arrow's label as a separate floating `<mxCell>` (with `style` containing `edgeLabel`, parented to the edge's ID) rather than directly on the edge's `value` attribute.

**Solution — 3-pass parsing:**

1. Collect all `edge="1"` cell IDs into a set
2. When encountering `vertex="1"` with `parent` in that set, or `style` containing `edgeLabel` — store text in `edge_labels[parent_id]`
3. Fill any empty edge labels from `edge_labels` after the main pass

---

#### 5 — Two Draw.io Storage Formats for Shapes

When a shape has had its tooltip or custom data edited, draw.io wraps the `<mxCell>` in a `<UserObject>` tag, moving the label from `value=` to `label=` on the outer tag. The `normalize_cells()` function handles both storage formats uniformly before any other logic runs.

---

#### 6 — Anonymous Node Unique Naming (v2/v3, extended in v4)

Connector nodes like Split/Join and ISA/PartOF appear multiple times in a diagram. Using the bare type string as the instance name causes collisions in 4EM (duplicate names). The solution auto-numbers them:

```
ANONYMOUS_NODE_TYPES = {
    "AND", "OR", "AND/OR",                                          # added in v4
    "Split (AND)", "Join (AND)", "Split (OR)", "Join (OR)",
    "PartOF (AND)", "PartOF (OR)", "PartOF (XOR)",
    "Partial-ISA", "Total-ISA", "Partial-PartOF", "Total-PartOF",
}

_anon_counters = {}

def make_anon_name(node_type):
    _anon_counters[node_type] = _anon_counters.get(node_type, 0) + 1
    return f"{node_type}-{_anon_counters[node_type]}"

# Results: "Split (AND)-1", "Split (AND)-2", "Total-PartOF-1", "AND-1", "AND-2", etc.
```

`AND`/`OR`/`AND/OR` were missing from this set in v1–v3. It went unnoticed there because a single-model export never combined separate parts of a diagram into one shared namespace — but v4's `[view] 4EM_General` does exactly that, and multiple un-numbered `AND` nodes with the literal name `"AND"` would get merged by 4EM into a single object, mixing up unrelated relations from different clusters. Fixed by adding these three types to the same auto-numbering set.

---

#### 7 — Cross-Origin Communication with an Embedded Editor (v4)

The browser tool doesn't contain any drawing-canvas code — it embeds the real `embed.diagrams.net` in an iframe and talks to it. Browsers block two different origins in one tab from reading each other's content directly (same-origin policy), so the only channel available is `window.postMessage`, and both sides have to agree on an encoding for it:

```js
// SEND: object -> JSON string -> across the origin boundary
frame.contentWindow.postMessage(JSON.stringify({action: "configure", config: {...}}), "*");

// RECEIVE: string -> JSON.parse -> back to a usable object
window.addEventListener("message", function(evt) {
  var msg = JSON.parse(evt.data);
});
```

`proto=json` in the iframe URL is what tells draw.io to use this JSON encoding rather than an older XML-based one it also supports.

---

#### 8 — Resolving a Node's Home Sub-Model from Its Relations, Not Its Type Alone (v4)

A first attempt used a fixed lookup (`"KPI"` → always Concepts Model). A real 4EM export disproved this directly: two KPI nodes, identical type, one correctly living in Goal Model (via a `measured by` link to a Goal) and one in Concepts Model (via `refers to` a Concept). Fixed by giving each node a *candidate* list of models its type is valid in, then letting every edge narrow that down by intersecting the two endpoints' candidate sets — if exactly one model is shared, both nodes get pinned there:

```
Goal candidates:  {Goal Model, Technical Components}
KPI candidates:   {Goal Model, Concepts Model}
intersection:     {Goal Model}   -> both nodes resolved to Goal Model
```

A subtler version of the same bug showed up with `AND`/`OR`/`AND/OR` connectors, which are valid in *three* models simultaneously (Goal Model, Technical Components, Business Rule) — an edge between two such ambiguous nodes can produce a 2-model overlap, which must be treated as **uninformative** and discarded, not applied. Getting this wrong caused the same node to be emitted into two different `BUSINESS PROCESS MODEL` blocks at once.

---

#### 9 — The Intermodel-Relations Attribute's Exact Format (v4)

4EM shows a per-node "Intermodel-Relations" panel for any node with an outgoing relation into a different sub-model. Pulling the raw bytes of a real export showed this needs a nested structure, not a simple value:

```
ATTRIBUTE <Intermodel-Relations>
VALUE
    RECORD
        ATTRIBUTE <Type>
        VALUE "is responsible for"

        ATTRIBUTE <interref>
        VALUE "REF mt:\"Goal Model\" m:\"4EM_Goal\" c:\"Goal\" i:\"Maximize Service Quality\"
"
    END
```
Confirmed to be populated only on the source side of the relation, never the target, by checking both ends of a real cross-model link in an actual exported file.

---

#### 10 — Per-View Position Normalization (v4)

Since draw.io only has one canvas, a cluster drawn low on the shared canvas was staying low even inside its own supposedly self-contained sub-model view. Fixed by computing each view's own bounding box — using *only that view's own nodes* — and shifting them to start near a small margin from that view's own origin, while `[view] 4EM_General` keeps every node's real, unshifted coordinates, since that's the one place your actual intentional layout is meant to be visible.

---

#### 11 — Sub-Type Attributes Aren't All the Same Mechanism (v4)

Rule and IS Requirement turned out to be single ADL classes with an internal `Type` attribute — a dedicated stencil variant per option, baking a custom attribute (`rule_type`, `req_type`) onto the shape, read by the converter and written straight into `Type`. This worked correctly the first time.

Problem/Weakness/Threat did **not** follow the same pattern, and getting this wrong was a real mistake worth documenting: stale, never-verified data already sitting in the v3 converter's tables suggested `Weakness`/`Threat` were separate ADL classes, so the first implementation built three distinct `em_type`s. Testing against a real 4EM export (drawn directly in 4EM, not converted) proved this wrong:

```
INSTANCE <sample Problem> : <Problem>
INSTANCE <Sample Weakness> : <Problem>
INSTANCE <Sample threat> : <Problem>
```
All three are the same class. The distinction lives in a **lowercase** `type` attribute at the end of the attribute list, not the class name at all — reverted to one shared `em_type="Problem"` with a `problem_type` sub-attribute across three stencil variants, matching Rule/IS Requirement's actual mechanism after all, just with a different (and differently-cased) attribute name.

---

#### 12 — Extending Rulebook Validation to Cross-Model Relations (v4)

The live validator and the per-model relation enum only ever covered relations *within* one sub-model. A relation crossing two sub-models was passing straight into the ADL file with no check at all — typing `"resp"` instead of `"performs"` wrote `Type "resp"` into the file untouched, and 4EM would then silently substitute its own default relation type on import rather than reject or preserve it. Fixed by running the same 349-entry rulebook check against intermodel relations too, moving an invalid label into `Description` with `Type` left blank instead of writing something 4EM would reinterpret unpredictably.

---

#### 13 — Two Layers of Caching Fighting Stencil Updates (v4)

Pushing an update to a stencil file on GitHub didn't always show up immediately in the tool — confirmed directly by inspecting GitHub's raw-content response headers (`cache-control: max-age=300`, `x-cache: HIT`), proving their CDN caches each raw file URL for 5 minutes regardless of what's actually in the repo now. Fixed by appending a fresh `Date.now()` query parameter to every stencil URL on each page load, forcing both GitHub's CDN and the browser to treat it as a new resource. (A more aggressive fix — fetching the content ourselves and handing draw.io a `blob:` URL, immune to any URL-based caching — was considered and deliberately not used: blob URLs are restricted to the exact origin that created them, and the draw.io iframe runs on a different origin, so it would never have been able to fetch it.)

---

## Detailed Usage Guide

### Step 1 — Generate Stencils

```
cd src

python build_stencil_v4.py
#   Written: generated_stencils/4EM_GoalModel_Stencil_v4.xml        (18 shapes)
#   Written: generated_stencils/4EM_BusinessProcess_Stencil_v4.xml  (15 shapes)
#   Written: generated_stencils/4EM_ActorsResources_Stencil_v4.xml  (19 shapes)
#   Written: generated_stencils/4EM_Concepts_Stencil_v4.xml         (14 shapes)
#   Written: generated_stencils/4EM_ProductService_Stencil_v4.xml   (14 shapes)
#   Written: generated_stencils/4EM_Technical_Stencil_v4.xml        (15 shapes)
#   Written: generated_stencils/4EM_BusinessRule_Stencil_v4.xml     (14 shapes)
#
#   All 7 stencils created successfully!
```

*(If you're using the browser tool instead, skip this step — the 7 v4 stencils are already hosted in this repo and load automatically.)*

---

### Step 2 — Load Stencils into Draw.io

**If using the browser tool (v4):** nothing to do — `4em_drawio_validator.html` loads all 7 automatically on open.

**draw.io Desktop (CLI workflow):**

1. Open draw.io Desktop
2. Go to **File → Open Library from → Device**
3. Navigate to `4EM/generated_stencils/`
4. Select one or more `.xml` files (e.g. `4EM_GoalModel_Stencil_v4.xml`)
5. Click **Open** — the stencil appears in the left sidebar

**app.diagrams.net (Web, CLI workflow):**

1. Go to [app.diagrams.net](https://app.diagrams.net)
2. Go to **File → Open Library from → Device**
3. Upload the stencil `.xml` file
4. The stencil loads into the sidebar

---

### Step 3 — Create Your Diagram

1. **Drag shapes** from the loaded stencil onto the canvas
2. **Rename each shape:**
  - **v3/v4 (recommended):** just type the name — e.g. `"Maximize Service Quality"`
  - **v1/v2:** type `"Type: Name"` — e.g. `"Goal: Maximize Service Quality"`
3. **Connect shapes** with arrows using the blue connection points
   - **v4 browser tool:** you'll get an immediate popup if the connection isn't valid, along with what would be valid instead
4. **Label arrows:** double-click an arrow and type the relation type — e.g. `"Supports"`, `"measured by"`
5. **Add descriptions (optional):** right-click a shape → **Edit Tooltip** → type the description
6. **Sub-type shapes (v4 only):** for Problem, Rule, IS Requirement, or Unspecific/Product/Service, drag the specific variant you want (e.g. "Weakness", "Rule (Event-action)", "IS Requirement (Functional)", "Product") instead of the generic shape

---

### Step 4 — Convert to ADL

**Browser tool (v4):** click "Convert to ADL & Download" — no export/import step needed, it reads the live diagram directly.

**CLI workflow — export from draw.io:**

- Go to **File → Export as → XML**
- Save with `.drawio.xml` extension — e.g. `MyGoalModel.drawio.xml`

**Run the converter:**

```
cd src

# v4 - multi-view output (default)
python drawio_to_4em_v4_multiview.py ../sample_drawio/MyModel.drawio.xml ../adl_outputs/MyModel.adl

# v4 - old single-model-only output, if you specifically want it
python drawio_to_4em_v4_multiview.py ../sample_drawio/MyModel.drawio.xml ../adl_outputs/MyModel.adl --single-view

# v3 - single model, auto-detected
python drawio_to_4em_v3.py input.xml output.adl

# v3 - override model type
python drawio_to_4em_v3.py input.xml output.adl --model-type "Concepts Model"

# v3 - override model name in ADL header
python drawio_to_4em_v3.py input.xml output.adl --model-name "4EM_MyModel"
```

**Example output (v4, multi-view):**

```
Converted 9 nodes across 2 sub-model view(s) + 1 general view:
  4EM_Goal (Goal Model): 5 nodes, 4 relations
  4EM_Actors and Resources (Actors and Resources Model): 4 nodes, 3 relations
  [view] 4EM_General: 9 nodes, 8 relations (1 intermodel)
```

**Example output (v3, single model):**

```
Auto-detected model type: 'Goal Model' (votes: {'Goal Model': 2})

Converted 2 nodes and 1 relations as 'Goal Model'.
  INSTANCE <Maximize Service Quality> : <Goal>  x:4.0cm y:4.8cm w:4.2cm h:1.6cm
  INSTANCE <Customer Satisfaction Score> : <KPI>  x:11.4cm y:4.8cm w:4.2cm h:1.6cm
  RELATION  Maximize Service Quality --[measured by]--> Customer Satisfaction Score
```

---

### Step 5 — Import into 4EM

1. Open the 4EM tool
2. Go to **File → Import**
3. Select the generated `.adl` file (e.g. `MyModel.adl`)
4. Click **Open** — 4EM parses the ADL and reconstructs your diagram
5. (v4) If your file has multiple sub-models, you'll see each one as its own view in 4EM's left-hand view list, plus `[view] 4EM_General` showing everything together

**After import, verify:**

- Node positions, names, and types are correct
- Relation types are correct
- Descriptions (from tooltips) appear on the relevant nodes
- Adjust layout if needed (4EM's auto-layout may differ slightly from draw.io)
- (v4) Check the Intermodel-Relations panel on any node you expected to have cross-model links

---

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| `WARNING: node '...' has no 'Type: Name' format` | Using v1/v2 converter with a shape that has no type prefix | Switch to v3/v4 converter + stencils, or add `"Type: "` prefix to the label |
| `WARNING: unrecognized node type(s) [...]` | A node's `em_type` doesn't match any known type | Check spelling against the type list in the converter; make sure you're using the matching stencil version |
| `NOTE: relation Type '...' moved to Description` | Arrow label is not a confirmed valid relation type for this model, or for the from-type/to-type pair | Check 4EM's relation dropdown for the correct label, or leave the arrow unlabeled; in the v4 browser tool, this is flagged live while you draw |
| `WARNING: skipping edge with missing endpoint` | An arrow in draw.io is not connected to a shape at one end | In draw.io, ensure both ends of every arrow are snapped to a shape (connection point turns green) |
| Wrong model auto-detected (v1–v3) | Diagram has more nodes from a different model | Use `--model-type "Model Name"` to force the correct model, or switch to v4's multi-view converter which doesn't need to pick just one |
| Duplicate node names in output | Multiple anonymous connector nodes (Split, Join, ISA, PartOF, AND/OR) on one diagram | Handled automatically in v2/v3/v4 for their respective supported types — make sure you're using the latest converter and stencils together |
| 4EM shows "wrong enumeration value" on import | An attribute field received an empty string when it expects a specific enum value | Ensure you are using the latest converter, which provides correct enum defaults |
| A node with multiple home models appears in two views unexpectedly (v4) | A node's type is valid in more than one sub-model, and it's not connected to anything that pins down which one | Connect it to a node from the intended model — the converter's log will name which node this affects |
| Stencil sidebar shows old shapes after updating this repo (v4 browser tool) | GitHub's raw-content CDN caches each file for ~5 minutes; browsers cache it too | The tool cache-busts on every load; if it still looks stale, hard-refresh the page once |
| Two people editing the same file don't see each other's changes (v4 browser tool) | The browser tool has no shared backend — see [Limitations](#limitations) | Use `app.diagrams.net` with Google Drive for the collaborative session, then bring the export into this tool just for validation/conversion |

---

## Limitations

### No real-time multi-user collaboration

In real 4EM (and in draw.io's own full app), you can save a diagram to Google Drive and have multiple people edit it together, live. **The browser tool in this repo does not do this**, and hosting it on a server by itself does not add it either — this is worth being explicit about rather than letting it seem like an oversight to be tweaked away.

**Why:** `4em_drawio_validator.html` has no backend and no shared storage of any kind. The `autosave` event this tool listens for only ever exists inside one person's browser tab. If two people open the same hosted page, they get two completely independent, unsynced draw.io sessions — there is no server in the loop to relay changes between them.

**Practical workaround (no extra engineering needed):** do the collaborative drawing session in the real, full draw.io app (`app.diagrams.net`), which already has native Google Drive integration and real-time multi-user editing built in — it's simply not present in the stripped-down `embed.diagrams.net` mode this tool uses. Once the team is done, export the `.drawio` XML from there and bring it into this tool just for the stencil-driven relation validation and ADL conversion step. Collaborate in real draw.io + Drive; validate and convert here.

**If genuine in-tool real-time collaboration is wanted anyway:** it would need an actual backend — something like a WebSocket server or Firebase Realtime Database that the tool pushes the diagram XML to on every `autosave` and periodically re-loads from when other users have made changes — plus handling what happens when two people edit at the same moment, which Drive's own integration already solves for you. This is a genuine multi-hour build, not a configuration change, and would need real server hosting (not just static file hosting) to run.

### Needs an internet connection to start

The tool has no local file dependencies, but it does need to reach two public addresses every time it opens: `embed.diagrams.net` (to load the editor itself) and this repo's raw GitHub URLs (to load the 7 stencils). Both are public, unauthenticated URLs, so this works for anyone with the file — but it is not an offline tool, and if this repo is ever made private or these files are moved, the editor will still load but the stencil sidebar will come up empty.

---

*Built for the 4EM enterprise modelling community. Contributions and issue reports welcome.*