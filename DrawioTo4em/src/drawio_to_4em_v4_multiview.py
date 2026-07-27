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

TYPE_TO_MODELS = {
    "AND": ["Goal Model", "Technical Components and Requirements Model", "Business Rule Model"],
    "AND/OR": ["Goal Model", "Technical Components and Requirements Model", "Business Rule Model"],
    "Assumption": ["Goal Model", "Business Process Model", "Actors and Resources Model", "Concepts Model", "Product-Service-Model", "Technical Components and Requirements Model", "Business Rule Model"],
    "Attribute": ["Concepts Model"],
    "Cause": ["Goal Model"],
    "Comment": ["Goal Model", "Business Process Model", "Actors and Resources Model", "Concepts Model", "Product-Service-Model", "Technical Components and Requirements Model", "Business Rule Model"],
    "Component": ["Product-Service-Model"],
    "Concept": ["Concepts Model"],
    "Constraint": ["Goal Model"],
    "Development Action": ["Goal Model", "Business Process Model", "Actors and Resources Model", "Concepts Model", "Product-Service-Model", "Technical Components and Requirements Model", "Business Rule Model"],
    "External Process": ["Business Process Model"],
    "Feature": ["Product-Service-Model"],
    "Goal": ["Goal Model"],
    "IS Requirement": ["Technical Components and Requirements Model"],
    "IS Technical Component": ["Technical Components and Requirements Model"],
    "Individual": ["Actors and Resources Model"],
    "Information Set": ["Business Process Model"],
    "Join (AND)": ["Business Process Model"],
    "Join (OR)": ["Business Process Model"],
    "KPI": ["Goal Model", "Concepts Model"],
    "OR": ["Goal Model", "Technical Components and Requirements Model", "Business Rule Model"],
    "Opportunity": ["Goal Model"],
    "Organizational Unit": ["Actors and Resources Model"],
    "PartOF (AND)": ["Product-Service-Model"],
    "PartOF (OR)": ["Product-Service-Model"],
    "PartOF (XOR)": ["Product-Service-Model"],
    "Partial-ISA": ["Actors and Resources Model", "Concepts Model", "Product-Service-Model"],
    "Partial-PartOF": ["Actors and Resources Model", "Concepts Model", "Technical Components and Requirements Model"],
    "Problem": ["Goal Model"],
    "Process": ["Business Process Model"],
    "Resource": ["Actors and Resources Model"],
    "Role": ["Actors and Resources Model"],
    "Rule": ["Business Rule Model"],
    "Split (AND)": ["Business Process Model"],
    "Split (OR)": ["Business Process Model"],
    "Total-ISA": ["Actors and Resources Model", "Concepts Model", "Product-Service-Model"],
    "Total-PartOF": ["Actors and Resources Model", "Concepts Model", "Technical Components and Requirements Model"],
    "Unspecific/Product/Service": ["Product-Service-Model"],
}


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
        ("type", "Problem"),       # lowercase "type" - Weakness/Threat are NOT separate
                                    # classes in real 4EM, they're this same "Problem"
                                    # class with this attribute set to "Weakness"/"Threat"
                                    # (confirmed from a real 4EM export)
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
        "supplies", "works at",
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
# The professor's full connection rulebook: every valid (relation, fromType,
# toType) triple across all 7 sub-models plus documented intermodel relations.
# Used to validate intermodel/ambiguous relations during ADL conversion, the
# same table the live draw.io connection validator checks against.
RULEBOOK_RELATIONS = [
    ('Supports', 'Goal', 'Goal'),
    ('Hinders', 'Goal', 'Goal'),
    ('motivates', 'Goal', 'Process'),
    ('requires', 'Goal', 'Process'),
    ('motivates', 'Goal', 'External Process'),
    ('requires', 'Goal', 'External Process'),
    ('Hinders', 'Constraint', 'Goal'),
    ('Hinders', 'Problem', 'Goal'),
    ('Contradicts', 'Goal', 'Goal'),
    ('Causes', 'Cause', 'Problem'),
    ('Causes', 'Cause', 'Opportunity'),
    ('Supports', 'Opportunity', 'Goal'),
    ('motivates', 'Goal', 'Feature'),
    ('measured by', 'Goal', 'KPI'),
    (' ', 'OR', 'Goal'),
    (' ', 'AND/OR', 'Goal'),
    (' ', 'AND', 'Goal'),
    (' ', 'Goal', 'AND'),
    (' ', 'Goal', 'OR'),
    (' ', 'Goal', 'AND/OR'),
    (' ', 'OR', 'Problem'),
    (' ', 'AND/OR', 'Problem'),
    (' ', 'AND', 'Problem'),
    (' ', 'Problem', 'AND'),
    (' ', 'Problem', 'OR'),
    (' ', 'Problem', 'AND/OR'),
    (' ', 'OR', 'Opportunity'),
    (' ', 'AND/OR', 'Opportunity'),
    (' ', 'AND', 'Opportunity'),
    (' ', 'Opportunity', 'AND'),
    (' ', 'Opportunity', 'OR'),
    (' ', 'Opportunity', 'AND/OR'),
    (' ', 'Development Action', 'Goal'),
    (' ', 'Development Action', 'Causes'),
    (' ', 'Development Action', 'Problem'),
    (' ', 'Development Action', 'Constraint'),
    (' ', 'Development Action', 'Opportunity'),
    (' ', 'Development Action', 'Cause'),
    (' ', 'Assumption', 'Goal'),
    (' ', 'Assumption', 'Causes'),
    (' ', 'Assumption', 'Problem'),
    (' ', 'Assumption', 'Constraint'),
    (' ', 'Assumption', 'Opportunity'),
    (' ', 'Assumption', 'Cause'),
    (' ', 'Comment', 'Goal'),
    (' ', 'Comment', 'Causes'),
    (' ', 'Comment', 'Problem'),
    (' ', 'Comment', 'Constraint'),
    (' ', 'Comment', 'Opportunity'),
    (' ', 'Comment', 'Cause'),
    ('motivates', 'Goal', 'Rule'),
    ('requires', 'Goal', 'Rule'),
    ('supports', 'Rule', 'Goal'),
    ('hinders', 'Rule', 'Goal'),
    ('Supports', 'Rule', 'Rule'),
    ('Hinders', 'Rule', 'Rule'),
    ('Contradicts', 'Rule', 'Rule'),
    ('relates to', 'Rule', 'Unspecific/Product/Service'),
    (' ', 'OR', 'Rule'),
    (' ', 'AND/OR', 'Rule'),
    (' ', 'AND', 'Rule'),
    (' ', 'Rule', 'AND'),
    (' ', 'Rule', 'OR'),
    (' ', 'Rule', 'AND/OR'),
    (' ', 'Development Action', 'Rule'),
    (' ', 'Assumption', 'Rule'),
    (' ', 'Comment', 'Rule'),
    ('1:1', 'Concept', 'Concept'),
    ('1:n', 'Concept', 'Concept'),
    ('n:m', 'Concept', 'Concept'),
    ('-', 'Concept', 'Attribute'),
    ('refers to', 'KPI', 'Concept'),
    (' ', 'Total-ISA', 'Concept'),
    (' ', 'Concept', 'Total-ISA'),
    (' ', 'Partial-ISA', 'Concept'),
    (' ', 'Concept', 'Partial-ISA'),
    (' ', 'Total-PartOF', 'Concept'),
    (' ', 'Concept', 'Total-PartOF'),
    (' ', 'Partial-PartOF', 'Concept'),
    (' ', 'Concept', 'Partial-PartOF'),
    (' ', 'Total-ISA', 'Attribute'),
    (' ', 'Attribute', 'Total-ISA'),
    (' ', 'Partial-ISA', 'Attribute'),
    (' ', 'Attribute', 'Partial-ISA'),
    (' ', 'Total-PartOF', 'Attribute'),
    (' ', 'Attribute', 'Total-PartOF'),
    (' ', 'Partial-PartOF', 'Attribute'),
    (' ', 'Attribute', 'Partial-PartOF'),
    (' ', 'Development Action', 'Concept'),
    (' ', 'Assumption', 'Concept'),
    (' ', 'Comment', 'Concept'),
    (' ', 'Development Action', 'Attribute'),
    (' ', 'Assumption', 'Attribute'),
    (' ', 'Comment', 'Attribute'),
    ('Output', 'Process', 'Information Set'),
    ('Output', 'External Process', 'Information Set'),
    ('-', 'Information Set', 'Information Set'),
    ('Input', 'Information Set', 'Process'),
    ('Input', 'Information Set', 'External Process'),
    ('triggers', 'Rule', 'Process'),
    ('-', 'Process', 'External Process'),
    ('-', 'External Process', 'Process'),
    ('supports', 'Process', 'Rule'),
    ('-', 'Split (AND)', 'Information Set'),
    ('-', 'Information Set', 'Split (AND)'),
    ('-', 'Split (OR)', 'Information Set'),
    ('-', 'Information Set', 'Split (OR)'),
    ('-', 'Join (AND)', 'Information Set'),
    ('-', 'Information Set', 'Join (AND)'),
    ('-', 'Join (OR)', 'Information Set'),
    ('-', 'Information Set', 'Join (OR)'),
    ('-', 'Split (AND)', 'Process'),
    ('-', 'Process', 'Split (AND)'),
    ('-', 'Split (OR)', 'Process'),
    ('-', 'Process', 'Split (OR)'),
    ('-', 'Join (AND)', 'Process'),
    ('-', 'Process', 'Join (AND)'),
    ('-', 'Join (OR)', 'Process'),
    ('-', 'Process', 'Join (OR)'),
    ('-', 'Split (AND)', 'External Process'),
    ('-', 'External Process', 'Split (AND)'),
    ('-', 'Split (OR)', 'External Process'),
    ('-', 'External Process', 'Split (OR)'),
    ('-', 'Join (AND)', 'External Process'),
    ('-', 'External Process', 'Join (AND)'),
    ('-', 'Join (OR)', 'External Process'),
    ('-', 'External Process', 'Join (OR)'),
    ('-', 'Development Action', 'Process'),
    ('-', 'Assumption', 'Process'),
    ('-', 'Comment', 'Process'),
    ('-', 'Development Action', 'External Process'),
    ('-', 'Assumption', 'External Process'),
    ('-', 'Comment', 'External Process'),
    ('-', 'Development Action', 'Information Flow'),
    ('-', 'Assumption', 'Information Flow'),
    ('-', 'Comment', 'Information Flow'),
    ('-', 'Development Action', 'Information Set'),
    ('-', 'Assumption', 'Information Set'),
    ('-', 'Comment', 'Information Set'),
    ('-', 'Role', 'Organizational Unit'),
    ('interacts with', 'Resource', 'Resource'),
    ('belongs to', 'Resource', 'Organizational Unit'),
    ('navigates', 'Organizational Unit', 'Resource'),
    ('responsible for', 'Organizational Unit', 'Resource'),
    ('plays', 'Individual', 'Role'),
    ('responsible for', 'Role', 'Resource'),
    ('maintains', 'Role', 'Resource'),
    ('works in', 'Role', 'Organizational Unit'),
    ('works at', 'Role', 'Organizational Unit'),
    ('supplies', 'Role', 'Organizational Unit'),
    ('-', 'Organizational Unit', 'Organizational Unit'),
    ('-', 'Role', 'Role'),
    ('-', 'Resource', 'Role'),
    ('responsible for', 'Role', 'Unspecific/Product/Service'),
    ('responsible for', 'Role', 'Feature'),
    ('-', 'Individual', 'Role'),
    ('-', 'Individual', 'Individual'),
    ('-', 'Individual', 'Organizational Unit'),
    ('-', 'Individual', 'Resource'),
    ('-', 'Role', 'Resource'),
    ('-', 'Role', 'Organizational Unit'),
    ('-', 'Resource', 'Resource'),
    ('-', 'Resource', 'Organizational Unit'),
    ('-', 'Organizational Unit', 'Resource'),
    ('-', 'Total-ISA', 'Role'),
    ('-', 'Role', 'Total-ISA'),
    ('-', 'Partial-ISA', 'Role'),
    ('-', 'Role', 'Partial-ISA'),
    ('-', 'Total-PartOF', 'Role'),
    ('-', 'Role', 'Total-PartOF'),
    ('-', 'Partial-PartOF', 'Role'),
    ('-', 'Role', 'Partial-PartOF'),
    ('-', 'Total-ISA', 'Individual'),
    ('-', 'Individual', 'Total-ISA'),
    ('-', 'Partial-ISA', 'Individual'),
    ('-', 'Individual', 'Partial-ISA'),
    ('-', 'Total-PartOF', 'Individual'),
    ('-', 'Individual', 'Total-PartOF'),
    ('-', 'Partial-PartOF', 'Individual'),
    ('-', 'Individual', 'Partial-PartOF'),
    ('-', 'Total-ISA', 'Resource'),
    ('-', 'Resource', 'Total-ISA'),
    ('-', 'Partial-ISA', 'Resource'),
    ('-', 'Resource', 'Partial-ISA'),
    ('-', 'Total-PartOF', 'Resource'),
    ('-', 'Resource', 'Total-PartOF'),
    ('-', 'Partial-PartOF', 'Resource'),
    ('-', 'Resource', 'Partial-PartOF'),
    ('-', 'Total-ISA', 'Organizational Unit'),
    ('-', 'Organizational Unit', 'Total-ISA'),
    ('-', 'Partial-ISA', 'Organizational Unit'),
    ('-', 'Organizational Unit', 'Partial-ISA'),
    ('-', 'Total-PartOF', 'Organizational Unit'),
    ('-', 'Organizational Unit', 'Total-PartOF'),
    ('-', 'Partial-PartOF', 'Organizational Unit'),
    ('-', 'Organizational Unit', 'Partial-PartOF'),
    ('-', 'Development Action', 'Individual'),
    ('-', 'Assumption', 'Individual'),
    ('-', 'Comment', 'Individual'),
    ('-', 'Development Action', 'Role'),
    ('-', 'Assumption', 'Role'),
    ('-', 'Comment', 'Role'),
    ('-', 'Development Action', 'Resource'),
    ('-', 'Assumption', 'Resource'),
    ('-', 'Comment', 'Resource'),
    ('-', 'Development Action', 'Organizational Unit'),
    ('-', 'Assumption', 'Organizational Unit'),
    ('-', 'Comment', 'Organizational Unit'),
    ('has requirement', 'Goal', 'IS Requirement'),
    ('has requirement', 'Goal', 'IS Technical Component'),
    ('has goal', 'IS Technical Component', 'Goal'),
    ('has requirement', 'IS Technical Component', 'IS Requirement'),
    ('supports', 'IS Technical Component', 'IS Technical Component'),
    ('hinders', 'IS Technical Component', 'IS Technical Component'),
    ('affects', 'IS Problem', 'IS Technical Component'),
    ('applies to', 'IS Requirement', 'IS Techical Component'),
    ('motivates', 'Goal', 'IS Technical Component'),
    ('hinders', 'IS Problem', 'Goal'),
    ('-', 'OR', 'IS Technical Component'),
    ('-', 'AND/OR', 'IS Technical Component'),
    ('-', 'AND', 'IS Technical Component'),
    ('-', 'IS Technical Component', 'AND'),
    ('-', 'IS Technical Component', 'OR'),
    ('-', 'IS Technical Component', 'AND/OR'),
    ('-', 'OR', 'IS Requirement'),
    ('-', 'AND/OR', 'IS Requirement'),
    ('-', 'AND', 'IS Requirement'),
    ('-', 'IS Requirement', 'AND'),
    ('-', 'IS Requirement', 'OR'),
    ('-', 'IS Requirement', 'AND/OR'),
    ('-', 'Total-PartOF', 'IS Technical Component'),
    ('-', 'IS Technical Component', 'Total-PartOF'),
    ('-', 'Partial-PartOF', 'IS Technical Component'),
    ('-', 'IS Technical Component', 'Partial-PartOF'),
    ('-', 'Development Action', 'IS Technical Component'),
    ('-', 'Assumption', 'IS Technical Component'),
    ('-', 'Comment', 'IS Technical Component'),
    ('-', 'Development Action', 'IS Requirement'),
    ('-', 'Assumption', 'IS Requirement'),
    ('-', 'Comment', 'IS Requirement'),
    ('-', 'Development Action', 'IS Goal'),
    ('-', 'Assumption', 'IS Goal'),
    ('-', 'Comment', 'IS Goal'),
    ('-', 'Development Action', 'IS Problem'),
    ('-', 'Assumption', 'IS Problem'),
    ('-', 'Comment', 'IS Problem'),
    ('-', 'Assumption', 'Development Action'),
    ('-', 'Comment', 'Development Action'),
    ('requires', 'Unspecific/Product/Service', 'IS Technical Component'),
    ('requires', 'Feature', 'IS Technical Component'),
    ('requires', 'Feature', 'Unspecific/Product/Service'),
    ('requires', 'Feature', 'Component'),
    (' ', 'Unspecific/Product/Service', 'PartOF (AND)'),
    (' ', 'PartOF (AND)', 'Unspecific/Product/Service'),
    (' ', 'Unspecific/Product/Service', 'PartOF (OR)'),
    (' ', 'PartOF (OR)', 'Unspecific/Product/Service'),
    (' ', 'PartOF (XOR)', 'Unspecific/Product/Service'),
    (' ', 'Unspecific/Product/Service', 'PartOF (XOR)'),
    (' ', 'Unspecific/Product/Service', 'Partial-ISA'),
    (' ', 'Partial-ISA', 'Unspecific/Product/Service'),
    (' ', 'Unspecific/Product/Service', 'Total-ISA'),
    (' ', 'Total-ISA', 'Unspecific/Product/Service'),
    (' ', 'Feature', 'PartOF (AND)'),
    (' ', 'PartOF (AND)', 'Feature'),
    (' ', 'Feature', 'PartOF (OR)'),
    (' ', 'PartOF (OR)', 'Feature'),
    (' ', 'PartOF (XOR)', 'Feature'),
    (' ', 'Feature', 'PartOF (XOR)'),
    (' ', 'Feature', 'Partial-ISA'),
    (' ', 'Partial-ISA', 'Feature'),
    (' ', 'Feature', 'Total-ISA'),
    (' ', 'Total-ISA', 'Feature'),
    (' ', 'Component', 'PartOF (AND)'),
    (' ', 'PartOF (AND)', 'Component'),
    (' ', 'Component', 'PartOF (OR)'),
    (' ', 'PartOF (OR)', 'Component'),
    (' ', 'PartOF (XOR)', 'Component'),
    (' ', 'Component', 'PartOF (XOR)'),
    (' ', 'Component', 'Partial-ISA'),
    (' ', 'Partial-ISA', 'Component'),
    (' ', 'Component', 'Total-ISA'),
    (' ', 'Total-ISA', 'Component'),
    (' ', 'Component', 'Unspecific/Product/Service'),
    (' ', 'Unspecific/Product/Service', 'Unspecific/Product/Service'),
    (' ', 'PartOF (AND)', 'PartOF (OR)'),
    (' ', 'PartOF (OR)', 'PartOF (AND)'),
    (' ', 'PartOF (AND)', 'PartOF (XOR)'),
    (' ', 'PartOF (XOR)', 'PartOF (AND)'),
    (' ', 'PartOF (XOR)', 'PartOF (OR)'),
    (' ', 'PartOF (OR)', 'PartOF (XOR)'),
    ('supports', 'Capability', 'Goal'),
    ('requires', 'Role', 'Capability'),
    ('uses', 'Capability', 'Concept'),
    ('realized by', 'Capability', 'Process'),
    ('supports', 'Resource', 'Capability'),
    ('supports', 'Capability', 'Capability'),
    ('conflicts', 'Capability', 'Capability'),
    (' ', 'Capability', 'AND'),
    (' ', 'Capability', 'OR'),
    (' ', 'Capability', 'AND/OR'),
    (' ', 'AND', 'Capability'),
    (' ', 'OR', 'Capability'),
    (' ', 'AND/OR', 'Capability'),
    ('relates to', 'Unspecific/Product/Service', 'Concept'),
    ('relates to', 'Feature', 'Concept'),
    ('creates', 'Process', 'Unspecific/Product/Service'),
    ('uses', 'Goal', 'Concept'),
    ('relates to', 'Goal', 'Concept'),
    ('uses', 'Process', 'Concept'),
    ('creates', 'Process', 'Concept'),
    ('uses', 'External Process', 'Concept'),
    ('creates', 'External Process', 'Concept'),
    ('defines', 'Role', 'Rule'),
    ('is responsible for', 'Role', 'Rule'),
    ('defines', 'Resource', 'Rule'),
    ('defines', 'Organizational Unit', 'Rule'),
    ('is responsible for', 'Organizational Unit', 'Rule'),
    ('defines', 'Role', 'Goal'),
    ('is responsible for', 'Role', 'Goal'),
    ('defines', 'Resource', 'Goal'),
    ('defines', 'Organizational Unit', 'Goal'),
    ('is responsible for', 'Organizational Unit', 'Goal'),
    ('performs', 'Role', 'External Process'),
    ('is responsible for', 'Role', 'External Process'),
    ('performs', 'Resource', 'External Process'),
    ('performs', 'Organizational Unit', 'External Process'),
    ('is responsible for', 'Organizational Unit', 'External Process'),
    ('performs', 'Role', 'Process'),
    ('is responsible for', 'Role', 'Process'),
    ('performs', 'Resource', 'Process'),
    ('performs', 'Organizational Unit', 'Process'),
    ('is responsible for', 'Organizational Unit', 'Process'),
    ('relates to', 'IS Technical Component', 'Concept'),
    ('relates to', 'IS Requirement', 'Concept'),
    ('defines', 'Role', 'IS Requirement'),
    ('defines', 'Role', 'IS Technical Component'),
    ('defines', 'Role', 'IS Requirement'),
    ('defines', 'Organizational Unit', 'IS Technical Component'),
    ('defines', 'Organizational Unit', 'IS Requirement'),
    ('defines', 'Resource', 'IS Technical Component'),
    ('defines', 'Resource', 'IS Requirement'),
    ('motivates', 'Process', 'IS Requirement'),
    ('motivates', 'External Process', 'IS Requirement'),
    ('motivates', 'Process', 'IS Technical Component'),
    ('motivates', 'External Process', 'IS Technical Component'),
    ('requires', 'Process', 'IS Requirement'),
    ('requires', 'External Process', 'IS Requirement'),
    ('requires', 'Process', 'IS Technical Component'),
    ('requires', 'External Process', 'IS Technical Component'),
]

_RULEBOOK_BLANK_MARKERS = {"-", " ", ""}


def _is_blank_relation_label(label):
    return label is None or label.strip() in _RULEBOOK_BLANK_MARKERS


def _lookup_rulebook_allowed(from_type, to_type):
    """Same forward/then-swapped lookup the live draw.io validator uses."""
    forward = [r for r, a, b in RULEBOOK_RELATIONS if a == from_type and b == to_type]
    if forward:
        return forward
    backward = [r for r, a, b in RULEBOOK_RELATIONS if a == to_type and b == from_type]
    return backward


def validate_intermodel_relation(from_type, to_type, label):
    """
    Checks an intermodel (or still-ambiguous) relation's label against the
    professor's rulebook, the same table the live connection validator uses
    - closing the gap where intermodel relations previously passed straight
    through to the ADL file unchecked (4EM would then silently substitute
    its own default relation type for anything it didn't recognize).

    Returns (corrected_type, corrected_description, note_or_None).
    """
    allowed = _lookup_rulebook_allowed(from_type, to_type)

    if not allowed:
        # No rule defined for this pair at all - nothing to validate
        # against, so leave the label as-is (matches prior behavior).
        return label or "", "", None

    has_blank_option = any(_is_blank_relation_label(r) for r in allowed)
    named_options = [r for r in allowed if not _is_blank_relation_label(r)]

    if _is_blank_relation_label(label):
        if has_blank_option or not named_options:
            return label or "", "", None
        # A name was expected here but none was given.
        options_str = ", ".join(sorted(set(named_options))) or "(none)"
        note = (f"relation has no label but a Type is expected for "
                f"'{from_type}' -> '{to_type}' (possible values: {options_str}); "
                f"left Type blank")
        return "", "", note

    label_norm = label.strip().lower()
    if any(r.strip().lower() == label_norm for r in named_options):
        return label, "", None

    options_str = ", ".join(sorted(set(named_options))) or "(none)"
    note = (f"relation Type '{label}' is not a valid connection between "
            f"'{from_type}' and '{to_type}' (possible values: {options_str}); "
            f"moved into Description and left Type blank")
    return "", label, note


ANONYMOUS_NODE_TYPES = {
    "AND", "OR", "AND/OR",
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
                # Sub-type overrides baked into specific stencil variants
                # (Problem/Weakness/Threat, Rule's 4 types, IS Requirement's
                # 2 types, Unspecific/Product/Service's 3 types) - None for
                # any shape that doesn't carry that particular attribute.
                "problem_type":  child.get("problem_type"),
                "rule_type":     child.get("rule_type"),
                "req_type":      child.get("req_type"),
                "problem_subtype": child.get("problem_subtype"),
                "specification": child.get("specification"),
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

            # Unspecific/Product/Service nodes carry a "Specification"
            # attribute 4EM needs set to exactly one of Unspecific/Product/
            # Service. Since draw.io only has one shape for all three, you
            # pick which one by appending a tag to the box's name, e.g.
            # "Website [Product]" or "Streaming Service [Service]"
            # (case-insensitive) - stripped back out before it's used as
            # the displayed instance name. Leave it off to keep the
            # default ("Service"). A dedicated stencil variant (baked
            # "specification" attribute) takes priority over the bracket
            # tag if both are somehow present.
            specification = cell.get("specification")
            if ntype == "Unspecific/Product/Service" and not specification:
                spec_match = re.search(
                    r"\[\s*(unspecific|product|service)\s*\]\s*$", name, re.IGNORECASE)
                if spec_match:
                    specification = spec_match.group(1).capitalize()
                    name = name[:spec_match.start()].strip()

            # Sub-type overrides for the other multi-choice node types,
            # baked into their dedicated stencil variants the same way.
            problem_type = cell.get("problem_type") if ntype == "Problem" else None
            rule_type = cell.get("rule_type") if ntype == "Rule" else None
            req_type = cell.get("req_type") if ntype == "IS Requirement" else None

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
                "specification": specification,
                "problem_type": problem_type,
                "rule_type": rule_type,
                "req_type": req_type,
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

def emit_instance(n, pos_override=None):
    attrs = TYPE_ATTRS.get(n["type"], COMMON_ATTRS)
    px = pos_override[0] if pos_override else n["x"]
    py = pos_override[1] if pos_override else n["y"]

    out = []
    out.append(f"INSTANCE <{n['name']}> : <{n['type']}>")
    out.append("")

    for attr_name, default in attrs:
        out.append(f"\tATTRIBUTE <{attr_name}>")
        if attr_name == "Intermodel-Relations":
            out.append("\tVALUE")
            records = n.get("intermodelRecords", [])
            for rec in records:
                out.append("\t\tRECORD")
                out.append("\t\t\tATTRIBUTE <Type>")
                out.append(f'\t\t\tVALUE "{rec["type"]}"')
                out.append("")
                out.append("\t\t\tATTRIBUTE <interref>")
                out.append(
                    f'\t\t\tVALUE "REF mt:\\"{rec["mt"]}\\" m:\\"{rec["m"]}\\" '
                    f'c:\\"{rec["c"]}\\" i:\\"{rec["i"]}\\"'
                )
                out.append('"')
                out.append("\t\tEND")
                out.append("")
            if records:
                out.append("")
        elif attr_name == "Specification" and n.get("specification"):
            out.append(f'\tVALUE "{n["specification"]}"')
            out.append("")
        elif attr_name == "Type" and n["type"] == "Rule" and n.get("rule_type"):
            out.append(f'\tVALUE "{n["rule_type"]}"')
            out.append("")
        elif attr_name == "Type" and n["type"] == "IS Requirement" and n.get("req_type"):
            out.append(f'\tVALUE "{n["req_type"]}"')
            out.append("")
        elif attr_name == "type" and n["type"] == "Problem" and n.get("problem_type"):
            out.append(f'\tVALUE "{n["problem_type"]}"')
            out.append("")
        elif default == "__POSITION__":
            out.append(
                f'\tVALUE "NODE x:{px}cm y:{py}cm w:{n["w"]}cm '
                f'h:{n["h"]}cm index:{n["index"]}"'
            )
            out.append("")
        elif default == "__POSITION_NO_WH__":
            out.append(f'\tVALUE "NODE x:{px}cm y:{py}cm index:{n["index"]}"')
            out.append("")
        elif default == "__DESCRIPTION__":
            out.append(f'\tVALUE "{n["description"]}"')
            out.append("")
        elif default == "__INTEGER__":
            out.append("\tVALUE 0")  # bare integer - NO quotes (4EM rejects quoted numbers here)
            out.append("")
        elif default is None:
            out.append("\tVALUE")
            out.append("")
        elif default == "":
            out.append('\tVALUE ""')
            out.append("")
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


def _model_block_header(block_name, type_str, description):
    lines = []
    lines.append(f"BUSINESS PROCESS MODEL <{block_name}> : <4EM 2.7>")
    lines.append("VERSION <>")
    lines.append(f"TYPE <{type_str}>")
    lines.append("")
    lines.append("\tATTRIBUTE <Author>")
    lines.append('\tVALUE "Converter"')
    lines.append("")
    lines.append("\tATTRIBUTE <Model type>")
    lines.append('\tVALUE "Current model"')
    lines.append("")
    lines.append("\tATTRIBUTE <Description>")
    lines.append(f'\tVALUE "{description}"')
    lines.append("")
    lines.append("")
    return lines


# Canonical order matches the real 4EM export's model ordering.
MODEL_ORDER = list(DEFAULT_MODEL_NAME.keys())


def convert_multiview(input_path, output_path):
    """
    Emits one ADL file containing:
      - one BUSINESS PROCESS MODEL block per populated sub-model, with
        only intra-model relations (both endpoints belong to that model)
      - a final "[view] 4EM_General" block containing every recognized
        node (union across all sub-models) plus every relation, including
        intermodel relations whose endpoints span two different sub-models

    This mirrors the real 4EM export format: 4EM matches the same
    INSTANCE <Name> : <Type> across views by (name, type). A node's
    per-model index/position is computed once and reused identically in
    every view it appears in (confirmed against a real 4EM export file).
    Relation indices are a simple per-block counter - 4EM does not require
    these to match any particular scheme across views.
    """
    nodes, edges = parse_drawio(input_path)

    # 1. Resolve each node's single home model by propagating through its
    #    relations, rather than a fixed type->model lookup. Many node types
    #    (KPI, Goal, Problem, AND/OR/AND-OR, Development Action, Comment,
    #    Assumption, ISA/PartOF connectors, ...) are legitimately used in
    #    more than one of the 7 sub-models - which one a given node "lives
    #    in" depends on what it's actually connected to, confirmed against
    #    a real 4EM export where two KPI nodes of the identical type ended
    #    up in two different views based on their relations (one measuring
    #    a Goal, one referring to a Concept). Every node in that real
    #    export has exactly one true home model - never two - so home[] is
    #    a single value per node, not a set.
    #
    #    candidate[id] = every model that node's type is used in at all
    #    home[id]      = the one model actually pinned down by its edges
    #
    #    IMPORTANT: an edge only ever pins a model down when it narrows
    #    things to EXACTLY one shared candidate. Two nodes that are BOTH
    #    still ambiguous (e.g. a Goal and an AND connector, which both
    #    list Goal Model *and* Technical Components as candidates) must
    #    NOT resolve each other just because their candidate lists
    #    overlap by more than one model - that's not actually a resolved
    #    answer, and committing it anyway causes chains of Goal/Problem/
    #    AND/OR/AND-OR nodes to all incorrectly pick up a second,
    #    unintended home in Technical Components and Requirements Model.
    candidate = {nid: TYPE_TO_MODELS.get(n["type"], []) for nid, n in nodes.items()}
    home = {nid: None for nid in nodes}

    def belief(nid):
        return [home[nid]] if home[nid] else candidate[nid]

    valid_edges = [e for e in edges if e["source"] in nodes and e["target"] in nodes]

    # Fixed-point propagation: repeating this lets a genuine anchor (e.g. a
    # Constraint, unambiguously Goal Model) propagate through a chain of
    # otherwise-ambiguous types (Goal, AND, OR, ...) to pin all of them
    # down correctly, one exactly-one-shared-model edge at a time.
    changed = True
    passes = 0
    while changed and passes < 10:
        changed = False
        passes += 1
        for e in valid_edges:
            overlap = set(belief(e["source"])) & set(belief(e["target"]))
            if len(overlap) == 1:
                m = next(iter(overlap))
                if home[e["source"]] is None:
                    home[e["source"]] = m
                    changed = True
                if home[e["target"]] is None:
                    home[e["target"]] = m
                    changed = True

    # Fallback for nodes that never got pinned down (isolated ambiguous
    # nodes, or connected only to other equally-unresolved ambiguous nodes).
    for nid, n in nodes.items():
        if home[nid] is not None:
            continue
        cands = candidate[nid]
        if not cands:
            print(f"WARNING: node '{n['name']}' has unrecognized type "
                  f"'{n['type']}'; excluded from all views")
        elif len(cands) == 1:
            home[nid] = cands[0]
        else:
            home[nid] = cands[0]
            print(f"NOTE: node '{n['name']}' (type '{n['type']}') is used in "
                  f"more than one 4EM model ({', '.join(cands)}) and isn't "
                  f"connected to anything that pins down which one; "
                  f"defaulting to '{cands[0]}'. Connect it to a node from "
                  f"the intended model if this isn't right.")

    for nid, n in nodes.items():
        n["homeModel"] = home[nid]

    # Assign each node one persistent index, from a counter on its home
    # model - reused identically in every view/block that node appears in
    # (confirmed against a real 4EM export: the same node keeps the same
    # index/position across views).
    per_model_counter = {m: 0 for m in MODEL_ORDER}
    for n in nodes.values():
        if not n["homeModel"]:
            continue
        per_model_counter[n["homeModel"]] += 1
        n["index"] = per_model_counter[n["homeModel"]]

    # 2. Resolve each edge by comparing its two (now-resolved) endpoints'
    #    single home model. Same model -> a normal intra-model relation.
    #    Different models -> a genuine intermodel relation (General view
    #    only), and recorded onto the source node's Intermodel-Relations.
    intra_by_model = {m: [] for m in MODEL_ORDER}
    inter_model = []

    for e in edges:
        src = nodes.get(e["source"])
        tgt = nodes.get(e["target"])
        if not src or not tgt:
            print(f"WARNING: skipping edge with missing endpoint: {e}")
            continue
        if not src["homeModel"] or not tgt["homeModel"]:
            print(f"WARNING: skipping edge (unrecognized endpoint type): "
                  f"{src['name']} -> {tgt['name']}")
            continue

        ctx = f"{src['name']} -> {tgt['name']}"
        same_model = src["homeModel"] == tgt["homeModel"]

        if src["type"] in FLOW_CONNECTOR_NODE_TYPES or tgt["type"] in FLOW_CONNECTOR_NODE_TYPES:
            if e["label"]:
                print(f"NOTE: clearing relation Type '{e['label']}' -> '' "
                      f"(edges to/from Split/Join/PartOF connectors must be "
                      f"unlabeled in 4EM) for {ctx}")
            corrected_type, corrected_desc = "", ""
        elif same_model:
            corrected_type, corrected_desc, note = validate_relation_type(
                src["homeModel"], e["label"])
            if note:
                print(f"NOTE: {note} (relation: {ctx})")
        else:
            # Intermodel relation: no per-model enum applies at this
            # granularity, but the professor's from-to rulebook does -
            # this is the same check the live draw.io validator runs,
            # now applied here too so an invalid label (like a typo)
            # gets caught and moved into Description instead of being
            # written into the ADL as a raw Type value that 4EM would
            # then silently substitute with its own default.
            corrected_type, corrected_desc, note = validate_intermodel_relation(
                src["type"], tgt["type"], e["label"])
            if note:
                print(f"NOTE: {note} (relation: {ctx})")

        entry = {"src": src, "tgt": tgt, "type": corrected_type, "desc": corrected_desc}
        if same_model:
            intra_by_model[src["homeModel"]].append(entry)
        else:
            inter_model.append(entry)
            print(f"NOTE: intermodel relation '{e['label'] or '(unlabeled)'}' "
                  f"({ctx}) only added to [view] 4EM_General, since its "
                  f"endpoints belong to different sub-models")
            src.setdefault("intermodelRecords", []).append({
                "type": corrected_type,
                "mt": tgt["homeModel"],
                "m": DEFAULT_MODEL_NAME.get(tgt["homeModel"], tgt["homeModel"]),
                "c": tgt["type"],
                "i": tgt["name"],
            })

    blocks = []
    view_summaries = []

    # 3. One block per populated sub-model, intra-model relations only.
    #    Each node belongs to exactly one of these (or is skipped entirely
    #    if its type was unrecognized).
    for model_type in MODEL_ORDER:
        model_nodes = [n for n in nodes.values() if n["homeModel"] == model_type]
        if not model_nodes:
            continue  # skip empty views, matches real export behavior

        block_name = DEFAULT_MODEL_NAME[model_type]
        lines = _model_block_header(block_name, model_type, "Converted from draw.io")

        # Individual views get their own self-contained layout: shift this
        # model's cluster so its top-left corner starts near the view's
        # origin, regardless of where you physically drew that cluster on
        # the shared draw.io canvas. (The General view below keeps your
        # original absolute layout, since that's where the clustering/
        # spacing you actually drew is meant to be visible.)
        min_x = min(n["x"] for n in model_nodes)
        min_y = min(n["y"] for n in model_nodes)
        margin_cm = 5

        for n in model_nodes:
            lines.append(emit_instance(n, pos_override=(
                round(n["x"] - min_x + margin_cm, 1),
                round(n["y"] - min_y + margin_cm, 1),
            )))
        for i, rel in enumerate(intra_by_model[model_type], start=1):
            lines.append(emit_relation(rel["src"], rel["tgt"], rel["type"], i, rel["desc"]))

        blocks.append("\n".join(lines))
        view_summaries.append(
            f"{block_name} ({model_type}): {len(model_nodes)} nodes, "
            f"{len(intra_by_model[model_type])} relations"
        )

    # 4. [view] 4EM_General: union of every recognized node + every relation
    #    (intra-model relations in per-model order, then intermodel ones).
    lines = _model_block_header(
        "[view] 4EM_General", "4EM General Model",
        "Union of all models with intermodel relations")
    included_nodes = [n for n in nodes.values() if n["homeModel"]]
    for n in included_nodes:
        lines.append(emit_instance(n))

    all_rels = []
    for m in MODEL_ORDER:
        all_rels.extend(intra_by_model[m])
    all_rels.extend(inter_model)
    for i, rel in enumerate(all_rels, start=1):
        lines.append(emit_relation(rel["src"], rel["tgt"], rel["type"], i, rel["desc"]))

    blocks.append("\n".join(lines))
    view_summaries.append(
        f"[view] 4EM_General: {len(included_nodes)} nodes, {len(all_rels)} "
        f"relations ({len(inter_model)} intermodel)"
    )

    header_comment = (
        "///////////////////////////////////////////////////////////////\n"
        "//\n"
        "// Generated by drawio_to_4em_v4_multiview.py\n"
        "//\n"
        "// The file contains the following models:\n"
        "//\n"
        + "\n".join(f"// {s.split(':')[0]}" for s in view_summaries) + "\n"
        "//\n"
        "///////////////////////////////////////////////////////////////\n\n"
        "VERSION <4.0>\n\n\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header_comment + "\n".join(blocks))

    print(f"\nConverted {len(included_nodes)} nodes across {len(view_summaries) - 1} "
          f"sub-model view(s) + 1 general view:")
    for s in view_summaries:
        print(f"  {s}")


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
             '(default derived from model type, e.g. "4EM_Goal"). '
             'Only used with --single-view.'
    )

    parser.add_argument(
        "--single-view",
        action="store_true",
        help="Emit the old single-model-only output (one auto-detected "
             "model, no [view] 4EM_General, no intermodel relations). "
             "Default is multi-view: one block per populated sub-model "
             "plus a [view] 4EM_General block with all intermodel relations."
    )

    args = parser.parse_args()

    # If no output path is provided, use ../adl_outputs/
    if args.output is None:
        os.makedirs("../adl_outputs", exist_ok=True)

        input_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = os.path.join("../adl_outputs", f"{input_name}.adl")

    if args.single_view:
        convert(
            args.input,
            args.output,
            model_name=args.model_name,
            model_type=args.model_type,
        )
    else:
        convert_multiview(args.input, args.output)

if __name__ == "__main__":
    main()