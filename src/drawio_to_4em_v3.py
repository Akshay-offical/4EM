"""
draw.io -> 4EM ADL converter (generic, all 4EM sub-models)
------------------------------------------------------------
Reads a draw.io .drawio/.xml file where:
  - vertices (boxes) are labeled "TYPE: Name"   e.g. "Goal: Maximize Service Quality"
  - edges (arrows) are labeled with a 4EM relation type e.g. "Supports", "Hinders"

Outputs a .adl file containing one BUSINESS PROCESS MODEL block with
INSTANCE entries for every box and RELATION entries for every arrow.

Supports all 7 4EM sub-models:
    Goal Model
    Business Process Model
    Actors and Resources Model
    Concepts Model
    Product-Service-Model
    Technical Components and Requirements Model
    Business Rule Model

The model type is AUTO-DETECTED from the node TYPE labels found in the
diagram (e.g. seeing "Process:" boxes implies Business Process Model).
You can override the detected type with --model-type on the command line.

USAGE:
    python drawio_to_4em.py input.drawio.xml output.adl
    python drawio_to_4em.py input.drawio.xml output.adl --model-type "Concepts Model"
    python drawio_to_4em.py input.drawio.xml output.adl --model-name "4EM_MyModel"
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from html import unescape

PX_PER_CM = 37.8  # standard 96dpi conversion (96 / 2.54)


# ════════════════════════════════════════════════════════════════════════════
# MODEL TYPE REGISTRY
# ════════════════════════════════════════════════════════════════════════════
# Maps every node TYPE string that can appear in a box label to the 4EM
# sub-model it belongs to. Used for auto-detection: whichever model type
# has the most matching node types in the diagram wins.

NODE_TYPE_TO_MODEL = {
    # Goal Model
    "Goal": "Goal Model",
    "KPI": "Goal Model",          # KPI also appears in Concepts Model; see NODE_TYPE_TIEBREAK
    "Problem": "Goal Model",
    "Cause": "Goal Model",
    "Opportunity": "Goal Model",
    "Constraint": "Goal Model",
    "AND": "Goal Model",
    "OR": "Goal Model",
    "AND/OR": "Goal Model",
    "Development Action": "Goal Model",
    "Comment": "Goal Model",
    "Assumption": "Goal Model",
    # Business Process Model
    "Process": "Business Process Model",
    "External Process": "Business Process Model",
    "Information Set": "Business Process Model",
    "Split (AND)": "Business Process Model",
    "Join (AND)": "Business Process Model",
    "Split (OR)": "Business Process Model",
    "Join (OR)": "Business Process Model",
    # Actors and Resources Model
    "Role": "Actors and Resources Model",
    "Individual": "Actors and Resources Model",
    "Resource": "Actors and Resources Model",
    "Organizational Unit": "Actors and Resources Model",
    "Partial-ISA": "Actors and Resources Model",
    "Total-ISA": "Actors and Resources Model",
    "Partial-PartOF": "Actors and Resources Model",
    "Total-PartOF": "Actors and Resources Model",
    # Concepts Model
    "Concept": "Concepts Model",
    "Attribute": "Concepts Model",
    "KPI": "Concepts Model",   # shared with Goal Model - in AMBIGUOUS_NODE_TYPES
    # Product-Service-Model
    "Unspecific/Product/Service": "Product-Service-Model",
    "Feature": "Product-Service-Model",
    "Component": "Product-Service-Model",
    "PartOF (AND)": "Product-Service-Model",
    "PartOF (OR)": "Product-Service-Model",
    "PartOF (XOR)": "Product-Service-Model",
    # Technical Components and Requirements Model
    "IS Technical Component": "Technical Components and Requirements Model",
    "IS Requirement": "Technical Components and Requirements Model",
    # Business Rule Model
    "Rule": "Business Rule Model",
}

# Some node type names are ambiguous (appear in more than one model in the
# 4EM metamodel). When auto-detection counts votes, these don't get counted
# towards a single model on their own; they just go along with whichever
# model wins from the unambiguous types.
AMBIGUOUS_NODE_TYPES = {
    "KPI", "Goal", "Process", "Constraint",
    # These appear in Actors, Concepts, Product-Service, and Technical models:
    "Partial-ISA", "Total-ISA", "Partial-PartOF", "Total-PartOF",
    # PartOF variants appear in Product-Service only but keep here for safety:
    "PartOF (OR)", "PartOF (XOR)",
}


# ════════════════════════════════════════════════════════════════════════════
# PER-TYPE ATTRIBUTE TEMPLATES
# ════════════════════════════════════════════════════════════════════════════
# Each entry is a list of (attribute_name, default_value) pairs in the order
# 4EM normally emits them. default_value of None means "blank VALUE" (no
# quotes); "" means an empty quoted string; anything else is used literally
# unless overridden by data found in the diagram (description, etc.)
#
# Special placeholder keys recognized by emit_instance():
#   __POSITION__   -> filled from node geometry
#   __DESCRIPTION__-> filled from node tooltip

COMMON_ATTRS = [
    ("Position", "__POSITION__"),
    ("External tool coupling", ""),
    ("Description", "__DESCRIPTION__"),
    ("Intermodel-Relations", None),
    ("Decomposition", ""),
    ("Defined by", ""),
    ("Attributes", None),
]

# Split/Join/PartOF connectors - CONFIRMED from real 4EM ADL sample:
# they only have Position + External tool coupling, and Position has NO
# width/height (just x/y/index), unlike every other node type.
FLOW_CONNECTOR_ATTRS = [
    ("Position", "__POSITION_NO_WH__"),
    ("External tool coupling", ""),
]

TYPE_ATTRS = {
    # ── Goal Model ──────────────────────────────────────────────────────
    "Goal": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Criticality", "Low"),     # enum: Low|Medium|High - empty rejected by 4EM
        ("Priority", "Medium"),     # enum: Low|Medium|High - empty rejected by 4EM
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Defined by", ""),
        ("Attributes", None),
    ],
    "KPI": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Defined by", ""),
        ("Attributes", None),
        ("Target Value", ""),
        ("KPI Log", ""),
        ("Designation", ""),
    ],
    "Problem": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
        ("Defined by", ""),
        ("Priority", "Low"),       # enum: Low|Medium|High - empty rejected by 4EM
        ("Criticality", "Low"),    # enum: Low|Medium|High - empty rejected by 4EM
        ("Description", "__DESCRIPTION__"),
    ],
    "Threat": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
        ("Defined by", ""),
        ("Priority", "Medium"),       # enum: Low|Medium|High - empty rejected by 4EM
        ("Criticality", "Medium"),    # enum: Low|Medium|High - empty rejected by 4EM
        ("Description", "__DESCRIPTION__"),
    ],
    "Weakness": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
        ("Defined by", ""),
        ("Priority", "High"),       # enum: Low|Medium|High - empty rejected by 4EM
        ("Criticality", "High"),    # enum: Low|Medium|High - empty rejected by 4EM
        ("Description", "__DESCRIPTION__"),
    ],
    "Cause": list(COMMON_ATTRS),
    "Opportunity": list(COMMON_ATTRS),
    "Constraint": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
        ("Defined by", ""),
    ],
    "AND": list(FLOW_CONNECTOR_ATTRS),
    "OR": list(FLOW_CONNECTOR_ATTRS),
    "AND/OR": list(FLOW_CONNECTOR_ATTRS),
    "Development Action": list(COMMON_ATTRS),
    "Comment": [
        ("Position", "__POSITION__"),
        ("Description", "__DESCRIPTION__"),
    ],
    "Assumption": [
        ("Position", "__POSITION__"),
        ("Description", "__DESCRIPTION__"),
    ],

    # ── Business Process Model ──────────────────────────────────────────
    "Process": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Decomposed Process", ""),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Execution Time", "__INTEGER__"),
        ("Complexity", "__INTEGER__"),
        ("Type", ""),
        ("Attributes", None),
    ],
    "External Process": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Execution Time", "__INTEGER__"),
        ("Complexity", "__INTEGER__"),
        ("Type", ""),
        ("Attributes", None),
    ],
    "Information Set": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Type", "Information Set"),  # enum - confirmed always "Information Set", never empty
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
    ],
    "Split (AND)": list(FLOW_CONNECTOR_ATTRS),
    "Join (AND)": list(FLOW_CONNECTOR_ATTRS),
    "Split (OR)": list(FLOW_CONNECTOR_ATTRS),
    "Join (OR)": list(FLOW_CONNECTOR_ATTRS),

    # ── Actors and Resources Model ──────────────────────────────────────
    "Role": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Qualification", ""),
        ("Number of Employees with this Role", "__INTEGER__"),
        ("Attributes", None),
    ],
    "Individual": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
    ],
    "Resource": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Location", ""),
        ("Quantity", "__INTEGER__"),
        ("Attributes", None),
    ],
    "Organizational Unit": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Location", ""),
        ("Attributes", None),
    ],

    # ── Concepts Model ───────────────────────────────────────────────────
    "Concept": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Decomposition", ""),
        ("Complexity", "__INTEGER__"),
        ("Execution Time", "__INTEGER__"),
        ("Intermodel-Relations", None),
        ("Attributes", None),
    ],
    "Attribute": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
        ("Data Type", "String"),
        ("Value Range", ""),
    ],

    # ── Product-Service-Model ───────────────────────────────────────────
    "Unspecific/Product/Service": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Specification", "Service"),  # enum: Unspecific|Product|Service - empty rejected by 4EM
        ("Attribute", None),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
    ],
    "Feature": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Attribute", None),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
    ],
    "Component": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Decomposition", ""),
        ("Quantity", "__INTEGER__"),
        ("Location", ""),
        ("Intermodel-Relations", None),
    ],
    "PartOF (AND)": list(FLOW_CONNECTOR_ATTRS),
    "PartOF (OR)":  list(FLOW_CONNECTOR_ATTRS),
    "PartOF (XOR)": list(FLOW_CONNECTOR_ATTRS),

    # ── Taxonomy/decomposition connectors ─────────────────────────────────
    # CONFIRMED from real 4EM ADL export (Actors_and_Resources_All_possibility.adl):
    # All four types have exactly COMMON_ATTRS (Position with full w/h,
    # External tool coupling, Description, Intermodel-Relations, Decomposition,
    # Defined by, Attributes). They are NOT flow connectors — they have
    # width/height in the Position, unlike Split/Join nodes.
    # They appear in: Actors & Resources, Concepts, Product-Service, Technical.
    "Partial-ISA":   list(FLOW_CONNECTOR_ATTRS),
    "Total-ISA":     list(FLOW_CONNECTOR_ATTRS),
    "Partial-PartOF": list(FLOW_CONNECTOR_ATTRS),
    "Total-PartOF":  list(FLOW_CONNECTOR_ATTRS),

    # ── Technical Components and Requirements Model ────────────────────
    "IS Technical Component": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Location", ""),
        ("Quantity", "__INTEGER__"),
        ("Attributes", None),
    ],
    "IS Requirement": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Description", "__DESCRIPTION__"),
        ("Type", "Functional"),  # enum - confirmed always "Functional" or "Nonfunctional", never empty
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
    ],

    # ── Business Rule Model ─────────────────────────────────────────────
    "Rule": [
        ("Position", "__POSITION__"),
        ("External tool coupling", ""),
        ("Type", "Derivation Rule"),  # enum - confirmed always "Derivation Rule", never empty
        ("Description", "__DESCRIPTION__"),
        ("Intermodel-Relations", None),
        ("Decomposition", ""),
        ("Attributes", None),
        ("Formal description in advanced language", ""),
    ],
}

# Model name used in the BUSINESS PROCESS MODEL <NAME> header, keyed by
# the human-readable model type.
DEFAULT_MODEL_NAME = {
    "Goal Model": "4EM_Goal",
    "Business Process Model": "4EM_Business Process",
    "Actors and Resources Model": "4EM_Actors and Resources",
    "Concepts Model": "4EM_Concepts",
    "Product-Service-Model": "4EM_Product-Service",
    "Technical Components and Requirements Model": "4EM_Technical Components and Requirements",
    "Business Rule Model": "4EM_Business Rule",
}

ALL_MODEL_TYPES = sorted(set(NODE_TYPE_TO_MODEL.values()))


# ════════════════════════════════════════════════════════════════════════════
# RELATION TYPE ENUM (per model) — CONFIRMED from a real 4EM ADL export.
# ════════════════════════════════════════════════════════════════════════════
# 4EM's relation "Type" field is a closed enum, NOT free text, and the exact
# casing matters (it's inconsistent across models - e.g. Goal Model uses
# "Hinders"/"Supports" capitalized, but Technical Components Model uses
# lowercase "hinders"/"supports"). Sending the wrong case causes a real
# validation error inside 4EM when importing/opening the ADL file.
#
# Each list below was extracted directly from real RELATION <4EM_Relation>
# blocks in a working 4EM export - NOT guessed. "" (empty) is always valid
# (an unlabeled/relation). Models not listed here (or relation
# types not seen yet for a listed model) are left unvalidated rather than
# guessed - a missing entry means "not yet confirmed," not "invalid."
RELATION_TYPE_ENUM = {
    "Goal Model": {
        "", "Causes", "Contradicts", "Hinders", "Supports", "measured by",
    },
    "Business Process Model": {
        "", "Input", "Output",
    },
    "Actors and Resources Model": {
        "", "belongs to", "interacts with", "maintains", "plays", "works in", "responsible for",
    },
    "Concepts Model": {
        "", "1:1", "1:n", "n:m", "refers to",
    },
    "Product-Service-Model": {
        "", "requires",
    },
    "Technical Components and Requirements Model": {
        "", "has requirement", "hinders", "supports",
    },
}


def validate_relation_type(model_type, label):
    """Check a relation's Type value against the confirmed enum for the
    given model.

    Returns (type_value, description_value, note):
      - Exact match (or empty label):        (label, "", None)
      - Case-insensitive match to a known
        valid value:                          (canonical_case, "", note)
      - Model not yet covered by the enum:    (label, "", None) - nothing
        to validate against, left as-is (not enough confirmed data to judge)
      - No match at all, model IS covered:    ("", label, note) - 4EM
        rejects unknown enum values outright, so rather than risk another
        rejection we move the original text into Description and leave
        Type blank. The information isn't lost, it just isn't a formal
        Type anymore.
    """
    if not label:
        return label, "", None

    enum = RELATION_TYPE_ENUM.get(model_type)
    if not enum:
        return label, "", None  # model not covered yet - nothing to validate against

    if label in enum:
        return label, "", None  # exact match, nothing to do

    # case-insensitive match -> silently correct to the canonical casing
    for valid in enum:
        if label.lower() == valid.lower():
            return valid, "", (
                f"auto-corrected relation Type '{label}' -> '{valid}' "
                f"(case mismatch with 4EM enum)"
            )

    # no match at all - 4EM would reject this as an invalid enum value,
    # so move it to Description instead of risking another rejection
    return "", label, (
        f"relation Type '{label}' is not a confirmed valid value for "
        f"'{model_type}' (known values: {sorted(enum)}). Moved it into the "
        f"relation's Description field and left Type blank, since 4EM "
        f"rejects unrecognized Type values outright. Please check 4EM's "
        f"relation dropdown for the correct Type if one applies."
    )


# ════════════════════════════════════════════════════════════════════════════
# HTML / TEXT HELPERS
# ════════════════════════════════════════════════════════════════════════════

def strip_html(text):
    """draw.io stencils sometimes inject HTML (<span>, &nbsp;, etc.) into
    labels, especially after a drag-and-drop from a styled stencil shape.
    This strips it back down to plain text."""
    if not text:
        return ""
    text = unescape(text)                  # &nbsp; -> "\xa0", &amp; -> "&", etc.
    text = re.sub(r"<[^>]+>", "", text)    # remove all <span>, <b>, etc.
    text = text.replace("\xa0", " ")       # non-breaking space -> regular space
    return text.strip()


# Node TYPE labels that have NO "Type: Name" structure - the whole label
# IS the type (these are the connective/flow-control shapes: AND/OR
# triangles and Split/Join nodes). When a box's value exactly matches one
# of these (ignoring surrounding whitespace), treat the full label as the
# type with an empty/auto-generated name instead of warning about missing
# "Type: Name" format.
BARE_LABEL_TYPES = {
    "AND", "OR", "AND/OR",
    "Split (AND)", "Join (AND)", "Split (OR)", "Join (OR)",
    "PartOF (AND)", "PartOF (OR)", "PartOF (XOR)",
    "Partial-ISA", "Total-ISA", "Partial-PartOF", "Total-PartOF",
}

# All bare-label types that need auto-numbered unique names to avoid
# collisions when multiple appear on one diagram.
ANONYMOUS_NODE_TYPES = {
    "Split (AND)", "Join (AND)", "Split (OR)", "Join (OR)",
    "PartOF (AND)", "PartOF (OR)", "PartOF (XOR)",
    "Partial-ISA", "Total-ISA", "Partial-PartOF", "Total-PartOF",
}

# Subset of ANONYMOUS_NODE_TYPES that are pure flow-control connectors:
# edges touching these nodes always have empty Type (confirmed from real
# 4EM ADL). Partial/Total ISA/PartOF are NOT in this set — their edges
# also end up empty in practice, but for a different reason (they simply
# have no semantic relation type, not a schema restriction), so they go
# through normal relation validation rather than being force-cleared here.
FLOW_CONNECTOR_NODE_TYPES = {
    "Split (AND)", "Join (AND)", "Split (OR)", "Join (OR)",
    "PartOF (AND)", "PartOF (OR)", "PartOF (XOR)",
}
_anon_counters = {}


def make_anon_name(node_type):
    _anon_counters[node_type] = _anon_counters.get(node_type, 0) + 1
    return f"{node_type}-{_anon_counters[node_type]}"


def px_to_cm(px):
    return round(float(px) / PX_PER_CM, 1)


# ════════════════════════════════════════════════════════════════════════════
# DRAW.IO PARSING
# ════════════════════════════════════════════════════════════════════════════

def normalize_cells(graph_root):
    """
    Walk the <root> element's direct children and normalize both plain
    <mxCell> elements AND <UserObject>/<object> wrapped cells into a single
    list of plain dicts with consistent keys.

    draw.io creates the <UserObject>/<object> wrapper when you use
    "Edit Tooltip..." or "Edit Data..." on a shape. In that case:
      - id, label (NOT "value"!), and tooltip live on the OUTER element
      - style, vertex/edge, geometry live on the INNER <mxCell>
    """
    entries = []
    for child in graph_root:
        if child.tag == "mxCell":
            entries.append({
                "id":      child.get("id"),
                "value":   strip_html(child.get("value")),
                "em_type": None,   # mxCell never has em_type
                "tooltip": child.get("tooltip"),
                "style": child.get("style", ""),
                "vertex": child.get("vertex"),
                "edge": child.get("edge"),
                "parent": child.get("parent"),
                "source": child.get("source"),
                "target": child.get("target"),
                "geometry": child.find("mxGeometry"),
            })
        elif child.tag in ("UserObject", "object"):
            inner = child.find("mxCell")
            if inner is None:
                continue
            entries.append({
                "id":      child.get("id"),
                "value":   strip_html(child.get("label")),
                "em_type": child.get("em_type"),   # NEW — explicit 4EM type attribute
                "tooltip": child.get("tooltip"),
                "style":   inner.get("style", ""),
                "vertex":  inner.get("vertex"),
                "edge":    inner.get("edge"),
                "parent":  inner.get("parent"),
                "source":  inner.get("source"),
                "target":  inner.get("target"),
                "geometry":inner.find("mxGeometry"),
            })
    return entries


def detect_model_type(nodes):
    """Auto-detect the 4EM model type by counting which model each node's
    TYPE label votes for, ignoring ambiguous types where possible. Returns
    (model_type, votes_dict) for transparency/diagnostics."""
    votes = {}
    for n in nodes.values():
        ntype = n["type"]
        if ntype in AMBIGUOUS_NODE_TYPES:
            continue
        model = NODE_TYPE_TO_MODEL.get(ntype)
        if model:
            votes[model] = votes.get(model, 0) + 1

    if not votes:
        # fall back to ambiguous types if nothing unambiguous was found
        for n in nodes.values():
            model = NODE_TYPE_TO_MODEL.get(n["type"])
            if model:
                votes[model] = votes.get(model, 0) + 1

    if not votes:
        return None, votes

    best_model = max(votes, key=votes.get)
    return best_model, votes


def parse_drawio(input_path):
    _anon_counters.clear()
    tree = ET.parse(input_path)
    root = tree.getroot()
    graph_root = root.find(".//root")
    if graph_root is None:
        raise ValueError("Could not find <root> element in draw.io file")

    all_cells = normalize_cells(graph_root)

    # ── Pass 1: find every cell id that is an EDGE ──────────────────────
    # We need this set first because draw.io sometimes stores an edge's label
    # as a SEPARATE child cell (vertex="1", style contains "edgeLabel",
    # parent=<the edge's id>) rather than as the edge's own "value".
    edge_ids = set()
    for cell in all_cells:
        if cell.get("edge") == "1":
            edge_ids.add(cell.get("id"))

    nodes = {}        # cell id -> {type, name, x, y, w, h, index}
    edges = []        # list of {id, source, target, label}
    edge_labels = {}  # edge cell id -> label text (from separate label cells)
    unknown_types = set()

    next_index = 1
    for cell in all_cells:
        if cell.get("edge") == "1":
            edges.append({
                "id": cell.get("id"),
                "source": cell.get("source"),
                "target": cell.get("target"),
                "label": (cell.get("value") or "").strip(),
            })

        elif cell.get("vertex") == "1":
            style = cell.get("style") or ""
            parent = cell.get("parent")
            value = (cell.get("value") or "").strip()

            # ── Detect "edge label" cells ────────────────────────────────
            if "edgeLabel" in style or parent in edge_ids:
                edge_labels[parent] = value
                continue
                
            em_type = (cell.get("em_type") or "").strip()

            # if em_type:
            #     # NEW FORMAT: em_type attribute holds the type,
            #     # label holds just the name
            #     ntype = em_type
            #     name  = value if value else em_type
            #     # Anonymous types still need unique names
            #     if ntype in ANONYMOUS_NODE_TYPES and not value:
            #         name = make_anon_name(ntype)

            if em_type:
                # NEW FORMAT: em_type attribute holds the type,
                # label holds just the name
                ntype = em_type
                
                # Ignore label if it just repeats the type name
                custom_name = value if (value and value != em_type) else None
                
                if custom_name:
                    name = custom_name
                elif ntype in ANONYMOUS_NODE_TYPES:
                    name = make_anon_name(ntype)
                else:
                    name = em_type

            elif value in BARE_LABEL_TYPES:
                # OLD FORMAT fallback: bare labels like "Split (AND)"
                if value in ANONYMOUS_NODE_TYPES:
                    ntype, name = value, make_anon_name(value)
                else:
                    ntype, name = value, value

            elif ":" in value:
                # OLD FORMAT fallback: "Type: Name"
                ntype, name = value.split(":", 1)
                ntype, name = ntype.strip(), name.strip()

            else:
                ntype, name = "Unknown", value
                print(f"WARNING: node '{value}' has no 'Type: Name' format "
                      f"and no em_type attribute "
                      f"(check this box's label - it should be like 'Goal: My Goal')")

            if ntype not in NODE_TYPE_TO_MODEL and ntype != "Unknown":
                unknown_types.add(ntype)

            geom = cell.get("geometry")
            x = geom.get("x", 0) if geom is not None else 0
            y = geom.get("y", 0) if geom is not None else 0
            w = geom.get("width", 0) if geom is not None else 0
            h = geom.get("height", 0) if geom is not None else 0

            description = (cell.get("tooltip") or "").strip()
            description = strip_html(description)
            # ADL VALUE strings are wrapped in double quotes - avoid breaking them
            description = description.replace('"', "'")

            nodes[cell.get("id")] = {
                "type": ntype,
                "name": name,
                "description": description,
                "x": px_to_cm(x),
                "y": px_to_cm(y),
                "w": px_to_cm(w),
                "h": px_to_cm(h),
                "index": next_index,
            }
            next_index += 1

    if unknown_types:
        print(f"WARNING: unrecognized node type(s) {sorted(unknown_types)} - "
              f"these will use generic attributes only. Known types: "
              f"{sorted(NODE_TYPE_TO_MODEL.keys())}")

    # ── Pass 2: fill in any edge labels that came from separate label cells ─
    for e in edges:
        if not e["label"]:
            e["label"] = edge_labels.get(e["id"], "")
            if not e["label"]:
                print(f"WARNING: edge {e['id']} (source={e['source']}, "
                      f"target={e['target']}) has no label/relation type")

    return nodes, edges


# ════════════════════════════════════════════════════════════════════════════
# ADL EMISSION
# ════════════════════════════════════════════════════════════════════════════

def emit_instance(n):
    attrs = TYPE_ATTRS.get(n["type"], COMMON_ATTRS)

    out = []
    out.append(f"INSTANCE <{n['name']}> : <{n['type']}>")
    out.append("")

    for attr_name, default in attrs:
        out.append(f"\tATTRIBUTE <{attr_name}>")
        if default == "__POSITION__":
            out.append(
                f'\tVALUE "NODE x:{n["x"]}cm y:{n["y"]}cm w:{n["w"]}cm '
                f'h:{n["h"]}cm index:{n["index"]}"'
            )
        elif default == "__POSITION_NO_WH__":
            out.append(f'\tVALUE "NODE x:{n["x"]}cm y:{n["y"]}cm index:{n["index"]}"')
        elif default == "__DESCRIPTION__":
            out.append(f'\tVALUE "{n["description"]}"')
        elif default == "__INTEGER__":
            out.append("\tVALUE 0")  # bare integer - NO quotes (4EM rejects quoted numbers here)
        elif default is None:
            out.append("\tVALUE")
        elif default == "":
            out.append('\tVALUE ""')
        else:
            out.append(f'\tVALUE "{default}"')
        out.append("")

    out.append("")
    return "\n".join(out)


def emit_relation(src, tgt, label, idx, description=""):
    out = []
    out.append("RELATION <4EM_Relation>")
    out.append(f"\tFROM <{src['name']}> : <{src['type']}>")
    out.append(f"\tTO <{tgt['name']}> : <{tgt['type']}>")
    out.append("")
    out.append("\tATTRIBUTE <Positions>")
    out.append(f'\tVALUE "EDGE 0 index:{idx}"')
    out.append("")
    out.append("\tATTRIBUTE <Type>")
    out.append(f'\tVALUE "{label}"')
    out.append("")
    out.append("\tATTRIBUTE <Description>")
    out.append(f'\tVALUE "{description}"')
    out.append("")
    out.append("\tATTRIBUTE <IR>")
    out.append('\tVALUE "False"')
    out.append("")
    out.append("")
    return "\n".join(out)


# ════════════════════════════════════════════════════════════════════════════
# MAIN CONVERSION
# ════════════════════════════════════════════════════════════════════════════

def convert(input_path, output_path, model_name=None, model_type=None):

    nodes, edges = parse_drawio(input_path)

    detected_type, votes = detect_model_type(nodes)

    if model_type:
        final_type = model_type
        if detected_type and detected_type != model_type:
            print(f"NOTE: auto-detected '{detected_type}' (votes: {votes}) "
                  f"but using '{model_type}' as requested via --model-type")
    elif detected_type:
        final_type = detected_type
        print(f"Auto-detected model type: '{final_type}' (votes: {votes})")
    else:
        final_type = "Goal Model"
        print("WARNING: could not auto-detect model type from node labels; "
              f"defaulting to '{final_type}'. Use --model-type to override. "
              f"Valid types: {ALL_MODEL_TYPES}")

    final_name = model_name or DEFAULT_MODEL_NAME.get(final_type, "4EM_Model")

    lines = []
    lines.append("VERSION <4.0>")
    lines.append("")
    lines.append("")
    lines.append(f"BUSINESS PROCESS MODEL <{final_name}> : <4EM 2.7>")
    lines.append("VERSION <>")
    lines.append(f"TYPE <{final_type}>")
    lines.append("")
    lines.append("\tATTRIBUTE <Author>")
    lines.append('\tVALUE "Converter"')
    lines.append("")
    lines.append("\tATTRIBUTE <Model type>")
    lines.append('\tVALUE "Current model"')
    lines.append("")
    lines.append("\tATTRIBUTE <Description>")
    lines.append('\tVALUE "Converted from draw.io"')
    lines.append("")
    lines.append("")

    # instances
    for n in nodes.values():
        lines.append(emit_instance(n))

    # relations
    for idx, e in enumerate(edges, start=1):
        src = nodes.get(e["source"])
        tgt = nodes.get(e["target"])
        if not src or not tgt:
            print(f"WARNING: skipping edge with missing endpoint: {e}")
            continue

        # Edges touching a Split/Join/PartOF connector ALWAYS have an empty
        # Type - CONFIRMED from real 4EM ADL sample (every single edge into
        # or out of a Split (AND)/Join (AND) node has Type ""). This
        # overrides whatever label was drawn on the edge (e.g. "Triggers"
        # is not valid here).
        if src["type"] in FLOW_CONNECTOR_NODE_TYPES or tgt["type"] in FLOW_CONNECTOR_NODE_TYPES:
            if e["label"]:
                print(f"NOTE: clearing relation Type '{e['label']}' -> '' "
                      f"(edges to/from Split/Join/PartOF connectors must be "
                      f"unlabeled in 4EM) for {src['name']} -> {tgt['name']}")
            corrected_type, corrected_desc = "", ""
        else:
            corrected_type, corrected_desc, note = validate_relation_type(final_type, e["label"])
            if note:
                print(f"NOTE: {note} (relation: {src['name']} -> {tgt['name']})")
        lines.append(emit_relation(src, tgt, corrected_type, idx, description=corrected_desc))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # summary
    print(f"\nConverted {len(nodes)} nodes and {len(edges)} relations "
          f"as '{final_type}'.")
    for n in nodes.values():
        if n["type"] in FLOW_CONNECTOR_NODE_TYPES:
            print(f"  INSTANCE <{n['name']}> : <{n['type']}>  "
                  f"x:{n['x']}cm y:{n['y']}cm")
        else:
            print(f"  INSTANCE <{n['name']}> : <{n['type']}>  "
                  f"x:{n['x']}cm y:{n['y']}cm w:{n['w']}cm h:{n['h']}cm")
    for e in edges:
        s, t = nodes.get(e["source"]), nodes.get(e["target"])
        if s and t:
            if s["type"] in FLOW_CONNECTOR_NODE_TYPES or t["type"] in FLOW_CONNECTOR_NODE_TYPES:
                shown = "<no type - connector edge>"
            else:
                shown_type, shown_desc, _ = validate_relation_type(final_type, e["label"])
                shown = shown_type if shown_type else f'<no type, description: "{shown_desc}">'
            print(f"  RELATION  {s['name']} --[{shown}]--> {t['name']}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a draw.io diagram into a 4EM ADL model file "
                    "(supports all 7 4EM sub-models, auto-detected by default)."
    )

    parser.add_argument("input", help="Path to input .drawio/.xml file")

    # Optional positional argument
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Path to output .adl file (default: ../adl_outputs/<input_name>.adl)"
    )

    parser.add_argument(
        "--model-type", "-t",
        default=None,
        choices=ALL_MODEL_TYPES,
        help="Override auto-detected 4EM model type."
    )

    parser.add_argument(
        "--model-name", "-n",
        default=None,
        help='Override the model name in the ADL header '
             '(default derived from model type, e.g. "4EM_Goal").'
    )

    args = parser.parse_args()

    # If no output path is provided, use ../adl_outputs/
    if args.output is None:
        os.makedirs("../adl_outputs", exist_ok=True)

        input_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = os.path.join("../adl_outputs", f"{input_name}.adl")

    convert(
        args.input,
        args.output,
        model_name=args.model_name,
        model_type=args.model_type,
    )

if __name__ == "__main__":
    main()