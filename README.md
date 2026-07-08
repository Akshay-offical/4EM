# 4EM Draw.io Integration Toolkit

Convert draw.io diagrams into **4EM (For Enterprise Modelling)** ADL files and use custom draw.io stencils for all 7 4EM sub-models. This toolkit enables enterprise architects and business analysts to create 4EM models visually in draw.io, then import them directly into the 4EM modeling tool.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Supported 4EM Models](#supported-4em-models)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Version Evolution](#version-evolution)
  - [v1 — Foundation](#v1--foundation-goal-model-only)
  - [v2 — Multi-Model Support](#v2--multi-model-support)
  - [v3 — Production-Ready](#v3--production-ready-recommended)
- [File Structure](#file-structure)
- [How It Works](#how-it-works)
  - [Draw.io XML Format](#drawio-xml-format)
  - [4EM ADL Format](#4em-adl-format)
  - [Key Technical Challenges](#key-technical-challenges)
- [Detailed Usage Guide](#detailed-usage-guide)
  - [Step 1 — Generate Stencils](#step-1--generate-stencils)
  - [Step 2 — Load Stencils into Draw.io](#step-2--load-stencils-into-drawio)
  - [Step 3 — Create Your Diagram](#step-3--create-your-diagram)
  - [Step 4 — Convert to ADL](#step-4--convert-to-adl)
  - [Step 5 — Import into 4EM](#step-5--import-into-4em)
- [Troubleshooting](#troubleshooting)

---

## Overview

The **4EM toolkit** bridges the gap between draw.io's intuitive visual editor and the 4EM enterprise modeling tool. It provides:

1. **Custom draw.io stencils** for all 7 4EM sub-models with proper shapes, colors, and semantics
2. **Automated converters** that transform draw.io diagrams into 4EM ADL (plain text) format
3. **Validation & auto-detection** of model types and relation types
4. **Production-ready workflow** with `em_type` metadata for robust, user-friendly conversion

### Why This Toolkit?

| Benefit | Description |
|---------|-------------|
| 🎨 **Visual modeling** | Use draw.io's powerful diagram editor instead of 4EM's limited UI |
| 🤝 **Collaboration** | Share diagrams via draw.io web/desktop, version control with Git |
| 🎯 **Consistency** | Pre-built stencils ensure correct 4EM semantics and styling |
| ✅ **Validation** | Auto-detect model types, validate relation types, catch errors early |

---

## Supported 4EM Models

All 7 4EM sub-models are fully supported:

| Model | Stencil | Converter |
|-------|:-------:|:---------:|
| Goal Model | ✅ | ✅ |
| Business Process Model | ✅ | ✅ |
| Actors and Resources Model | ✅ | ✅ |
| Concepts Model | ✅ | ✅ |
| Product-Service Model | ✅ | ✅ |
| Technical Components and Requirements Model | ✅ | ✅ |
| Business Rule Model | ✅ | ✅ |

---

## Installation

### Prerequisites

- **Python 3.7+** — standard library only, no external dependencies
- **draw.io Desktop** or access to [app.diagrams.net](https://app.diagrams.net)
- **4EM tool** — for importing the generated ADL files

### Setup

```bash
# Clone the repository
git clone https://github.com/Akshay-offical/4EM.git
cd 4EM

# No pip install needed — uses Python standard library only
python --version  # Should be 3.7 or higher
```

---

## Quick Start

```bash
# 1. Generate stencils (v3 recommended)
cd src
python build_stencil_v3.py

# 2. Open draw.io and load a stencil
#    File → Open Library from → Device
#    Select: generated_stencils/4EM_GoalModel_Stencil_v3.xml

# 3. Create your diagram in draw.io, then export as .drawio.xml

# 4. Convert to ADL
python drawio_to_4em_v3.py ../sample_drawio/Goal_Model_V3.drawio.xml ../adl_outputs/Goal_Model_V3.adl

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
|------|---------|
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
|-------|-----------|
| Goal Model | AND, OR, AND/OR, Development Action, Assumption, Comment |
| Business Process | Split (OR), Join (OR), helper nodes |
| Actors & Resources | Partial-ISA, Total-ISA, Partial-PartOF, Total-PartOF |
| Concepts | ISA/PartOF taxonomy nodes |
| Product-Service | PartOF (OR), PartOF (XOR), ISA nodes |
| Technical | Goal, Problem, AND/OR logic, PartOF nodes |
| Business Rule | AND, OR, AND/OR logic nodes |

#### Files

| File | Purpose |
|------|---------|
| `src/build_stencil_v2.py` | Multi-model stencil generator |
| `src/drawio_to_4em_v2.py` | Multi-model converter with auto-detection |

---

### v3 — Production-Ready ⭐ (Recommended)

**Purpose:** Industrial-strength solution with `em_type` metadata for robust, user-friendly conversion.

#### 🎯 Major Breakthrough: `em_type` Attribute

**The Problem (v1/v2) — fragile label parsing:**

```xml
<!-- User must type the prefix exactly right -->
<mxCell value="Goal: Maximize Service Quality" .../>
```

```python
# Converter parses the label prefix — any typo breaks conversion
ntype, name = value.split(":", 1)
```

**The Solution (v3) — type baked into shape metadata:**

```xml
<!-- Stencil has em_type built in -->
<UserObject label="<name>" em_type="Goal" id="2">
  <mxCell vertex="1" .../>
</UserObject>

<!-- User just renames the label — no prefix needed -->
<UserObject label="Maximize Service Quality" em_type="Goal" id="2">
  ...
</UserObject>
```

```python
# Converter reads em_type directly — immune to typos
em_type = cell.get("em_type")  # Always "Goal", no parsing needed
```

#### Key Features (All v2 Features + Enhancements)

- **`em_type` metadata** — node type is baked into the shape, not parsed from the label
- **Simplified labeling** — users just type the name, no `"Type: "` prefix required
- **Typo-proof** — can't accidentally break conversion by misspelling the type
- **Duplicate handling** — fixed bug where multiple nodes of the same type collided
- **Custom shapes** — accurate 4EM visual styling:
  - `leftcut` (`flowchart.card`) for Role/Individual
  - `circle` (`ellipse`) for ISA taxonomy nodes
  - `square` (`rounded=0`) for PartOF taxonomy nodes
  - `chevron` (`blockArrow`) for Development Action
- **Official 4EM colors** — matches the 4EM tool palette exactly
- **Robust anonymous node naming** — handles edge cases where label duplicates type name

#### v1/v2 vs v3 Comparison

| Aspect | v1 / v2 | v3 |
|--------|---------|-----|
| Label format | `"Goal: My Goal"` (must type prefix) | `"My Goal"` (just the name) |
| Typo risk | High — `"Gola: X"` breaks conversion | Zero — type is metadata |
| User experience | Manual, error-prone | Drag-and-drop, rename |
| Duplicate nodes | Bug (all collapse to one instance) | Fixed (unique auto-numbering) |
| Visual accuracy | Generic shapes | Official 4EM colors & shapes |
| Robustness | Fragile string parsing | Metadata-driven |

#### Files

| File | Purpose |
|------|---------|
| `src/build_stencil_v3.py` | Production stencil generator with `em_type` |
| `src/drawio_to_4em_v3.py` | Production converter with duplicate-handling fix |

---

## File Structure

```
4EM/
├── README.md
├── src/
│   ├── build_stencil_v1.py            # v1: Basic stencil generator (Goal Model only)
│   ├── build_stencil_v2.py            # v2: Multi-model stencils
│   ├── build_stencil_v3.py            # v3: Production stencils with em_type ⭐
│   ├── drawio_to_4em_v1.py            # v1: Basic converter (Goal Model only)
│   ├── drawio_to_4em_v2.py            # v2: Multi-model converter with auto-detection
│   └── drawio_to_4em_v3.py            # v3: Production converter with duplicate fix ⭐
├── generated_stencils/
│   ├── 4EM_GoalModel_Stencil_v2.xml
│   ├── 4EM_GoalModel_Stencil_v3.xml
│   ├── 4EM_BusinessProcess_Stencil_v3.xml
│   ├── 4EM_ActorsResources_Stencil_v3.xml
│   ├── 4EM_Concepts_Stencil_v3.xml
│   ├── 4EM_ProductService_Stencil_v3.xml
│   ├── 4EM_Technical_Stencil_v3.xml
│   └── 4EM_BusinessRule_Stencil_v3.xml
├── sample_drawio/
│   ├── Goal_Model_V3.drawio.xml
│   ├── Actors_Resources_V3.drawio.xml
│   └── ...
└── adl_outputs/
    ├── Goal_Model_V3.adl
    └── ...
```

---

## How It Works

### Draw.io XML Format

Draw.io stores diagrams as XML. Here is a simplified example showing the v3 format:

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Goal Model" id="goal-model">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- v3: UserObject carries em_type metadata -->
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
- Every element is an `<mxCell>` (or `<UserObject>` wrapping `<mxCell>` in v3)
- Boxes have `vertex="1"` with `<mxGeometry>` storing `x`, `y`, `width`, `height` in **pixels**
- Arrows have `edge="1"` with `source` and `target` pointing to endpoint box IDs
- `id="0"` and `id="1"` are internal draw.io housekeeping cells — always ignored
- In v3, `em_type` stores the 4EM node type; the `label` holds only the user's name

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

---

### Key Technical Challenges

#### 1 — Extract Type and Name from Label (v1/v2) or Metadata (v3)

**v1/v2 — fragile string parsing:**
```python
value = "Goal: Maximize Service Quality"
ntype, name = value.split(":", 1)
# ntype = "Goal"
# name  = "Maximize Service Quality"
```

**v3 — robust metadata read:**
```python
em_type = cell.get("em_type")   # "Goal" — baked into the shape
label   = cell.get("label")     # "Maximize Service Quality" — user's text
ntype   = em_type
name    = label if label else em_type
```

---

#### 2 — Convert Pixels to Centimetres

Draw.io stores: `<mxGeometry x="150" y="180" width="160" height="60"/>`  
4EM needs: `VALUE "NODE x:4.0cm y:4.8cm w:4.2cm h:1.6cm index:1"`

```python
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

#### 6 — Anonymous Node Unique Naming (v2/v3)

Connector nodes like Split/Join and ISA/PartOF appear multiple times in a diagram. Using the bare type string as the instance name causes collisions in 4EM (duplicate names). The solution auto-numbers them:

```python
ANONYMOUS_NODE_TYPES = {
    "Split (AND)", "Join (AND)", "Split (OR)", "Join (OR)",
    "PartOF (AND)", "PartOF (OR)", "PartOF (XOR)",
    "Partial-ISA", "Total-ISA", "Partial-PartOF", "Total-PartOF",
}

_anon_counters = {}

def make_anon_name(node_type):
    _anon_counters[node_type] = _anon_counters.get(node_type, 0) + 1
    return f"{node_type}-{_anon_counters[node_type]}"

# Results: "Split (AND)-1", "Split (AND)-2", "Total-PartOF-1", etc.
```

---

## Detailed Usage Guide

### Step 1 — Generate Stencils

```bash
cd src

python build_stencil_v3.py
#   Written: generated_stencils/4EM_GoalModel_Stencil_v3.xml        (15 shapes)
#   Written: generated_stencils/4EM_BusinessProcess_Stencil_v3.xml  (14 shapes)
#   Written: generated_stencils/4EM_ActorsResources_Stencil_v3.xml  (16 shapes)
#   Written: generated_stencils/4EM_Concepts_Stencil_v3.xml         (14 shapes)
#   Written: generated_stencils/4EM_ProductService_Stencil_v3.xml   (12 shapes)
#   Written: generated_stencils/4EM_Technical_Stencil_v3.xml        (13 shapes)
#   Written: generated_stencils/4EM_BusinessRule_Stencil_v3.xml     (8 shapes)
#
#   All 7 stencils created successfully!
```

---

### Step 2 — Load Stencils into Draw.io

**draw.io Desktop:**
1. Open draw.io Desktop
2. Go to **File → Open Library from → Device**
3. Navigate to `4EM/generated_stencils/`
4. Select one or more `.xml` files (e.g. `4EM_GoalModel_Stencil_v3.xml`)
5. Click **Open** — the stencil appears in the left sidebar

**app.diagrams.net (Web):**
1. Go to [app.diagrams.net](https://app.diagrams.net)
2. Go to **File → Open Library from → Device**
3. Upload the stencil `.xml` file
4. The stencil loads into the sidebar

---

### Step 3 — Create Your Diagram

1. **Drag shapes** from the loaded stencil onto the canvas
2. **Rename each shape:**
   - **v3 (recommended):** just type the name — e.g. `"Maximize Service Quality"`
   - **v1/v2:** type `"Type: Name"` — e.g. `"Goal: Maximize Service Quality"`
3. **Connect shapes** with arrows using the blue connection points
4. **Label arrows:** double-click an arrow and type the relation type — e.g. `"Supports"`, `"measured by"`
5. **Add descriptions (optional):** right-click a shape → **Edit Tooltip** → type the description

---

### Step 4 — Convert to ADL

**Export from draw.io:**
- Go to **File → Export as → XML**
- Save with `.drawio.xml` extension — e.g. `MyGoalModel.drawio.xml`

**Run the converter:**

```bash
cd src

# Basic usage (model type auto-detected)
python drawio_to_4em_v3.py ../sample_drawio/MyGoalModel.drawio.xml ../adl_outputs/MyGoalModel.adl

# Override model type
python drawio_to_4em_v3.py input.xml output.adl --model-type "Concepts Model"

# Override model name in ADL header
python drawio_to_4em_v3.py input.xml output.adl --model-name "4EM_MyModel"
```

**Example output:**
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
3. Select the generated `.adl` file (e.g. `MyGoalModel.adl`)
4. Click **Open** — 4EM parses the ADL and reconstructs your diagram

**After import, verify:**
- Node positions, names, and types are correct
- Relation types are correct
- Descriptions (from tooltips) appear on the relevant nodes
- Adjust layout if needed (4EM's auto-layout may differ slightly from draw.io)

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `WARNING: node '...' has no 'Type: Name' format` | Using v1/v2 converter with a shape that has no type prefix | Switch to v3 converter + stencils, or add `"Type: "` prefix to the label |
| `WARNING: unrecognized node type(s) [...]` | A node's `em_type` (v3) or label prefix (v1/v2) doesn't match any known type | Check spelling against the type list in the converter |
| `NOTE: relation Type '...' moved to Description` | Arrow label is not a confirmed valid relation type for this model | Check 4EM's relation dropdown for the correct label, or leave the arrow unlabeled |
| `WARNING: skipping edge with missing endpoint` | An arrow in draw.io is not connected to a shape at one end | In draw.io, ensure both ends of every arrow are snapped to a shape (connection point turns green) |
| Wrong model auto-detected | Diagram has more nodes from a different model | Use `--model-type "Model Name"` to force the correct model |
| Duplicate node names in output | Multiple anonymous connector nodes (Split, Join, ISA, PartOF) on one diagram | This is handled automatically in v2/v3 — check that you are using the v3 converter |
| 4EM shows "wrong enumeration value" on import | An attribute field received an empty string when it expects a specific enum value | This is a known validation requirement — ensure you are using the latest converter, which provides correct enum defaults |

---

*Built for the 4EM enterprise modelling community. Contributions and issue reports welcome.*