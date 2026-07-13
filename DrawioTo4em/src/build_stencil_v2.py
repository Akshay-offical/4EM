import xml.etree.ElementTree as ET
import json

def make_cell_xml(value, style, w=160, h=60, edge=False,
                  src_x=0, src_y=30, tgt_x=160, tgt_y=30):
    gm = ET.Element("mxGraphModel")
    root = ET.SubElement(gm, "root")
    ET.SubElement(root, "mxCell", attrib={"id": "0"})
    ET.SubElement(root, "mxCell", attrib={"id": "1", "parent": "0"})
    if edge:
        c = ET.SubElement(root, "mxCell", attrib={
            "id": "2", "value": value, "style": style,
            "edge": "1", "parent": "1",
        })
        geo = ET.SubElement(c, "mxGeometry", attrib={"relative": "1", "as": "geometry"})
        ET.SubElement(geo, "mxPoint", attrib={"x": str(src_x), "y": str(src_y), "as": "sourcePoint"})
        ET.SubElement(geo, "mxPoint", attrib={"x": str(tgt_x), "y": str(tgt_y), "as": "targetPoint"})
    else:
        c = ET.SubElement(root, "mxCell", attrib={
            "id": "2", "value": value, "style": style,
            "vertex": "1", "parent": "1",
        })
        ET.SubElement(c, "mxGeometry", attrib={
            "x": "0", "y": "0", "width": str(w), "height": str(h), "as": "geometry"
        })
    return ET.tostring(gm, encoding="unicode")

def node(title, label, style, w=180, h=60):
    label = label.replace("&lt;", "<").replace("&gt;", ">")
    return {"xml": make_cell_xml(label, style, w=w, h=h),
            "w": w, "h": h, "aspect": "fixed", "title": title}

def edge(title, label, style):
    return {"xml": make_cell_xml(label, style, edge=True),
            "w": 160, "h": 60, "aspect": "fixed", "title": title}

def write_stencil(filename, shapes):
    library = ET.Element("mxlibrary")
    library.text = json.dumps(shapes, ensure_ascii=False)
    xml_str = ET.tostring(library, encoding="unicode")
    out = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    with open(filename, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  Written: {filename}  ({len(shapes)} shapes)")

# ── Base styles ───────────────────────────────────────────────────────────────
BASE_NODE = "rounded=1;whiteSpace=wrap;html=0;fontStyle=1;fontSize=11;"
BASE_EDGE = ("edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;"
             "exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
             "entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
             "strokeWidth=2;fontStyle=1;")

# Diamond shape (for AND/OR splits, joins, logic nodes)
DIAMOND = "shape=mxgraph.flowchart.decision;whiteSpace=wrap;html=0;fontStyle=1;fontSize=11;"

# Hexagon shape (for Development Action / Assumption / Comment helper nodes)
HEXAGON = "shape=hexagon;whiteSpace=wrap;html=0;fontStyle=1;fontSize=10;perimeter=hexagonPerimeter2;"

def ns(fill, stroke):
    return BASE_NODE + f"fillColor={fill};strokeColor={stroke};"

def ds(fill, stroke):           # diamond
    return DIAMOND + f"fillColor={fill};strokeColor={stroke};"

def hs(fill, stroke):           # hexagon (helper nodes)
    return HEXAGON + f"fillColor={fill};strokeColor={stroke};"

def es(color, fc=None):
    fc = fc or color
    return BASE_EDGE + f"strokeColor={color};fontColor={fc};"

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    # Shared
    "Goal":        ns("#dae8fc", "#6c8ebf"),
    "KPI":         ns("#d5e8d4", "#82b366"),
    "Problem":     ns("#f8cecc", "#b85450"),
    "Cause":       ns("#ffe6cc", "#d79b00"),
    "Opportunity": ns("#e1d5e7", "#9673a6"),
    "Constraint":  ns("#fff2cc", "#d6b656"),
    # Business Process
    "Process":     ns("#dae8fc", "#6c8ebf"),
    "ExtProcess":  ns("#f5f5f5", "#666666"),
    "InfoSet":     ns("#d5e8d4", "#82b366"),
    "SplitAND":    ds("#fff2cc", "#d6b656"),
    "JoinAND":     ds("#dae8fc", "#6c8ebf"),
    "SplitOR":     ds("#e1d5e7", "#9673a6"),
    "JoinOR":      ds("#f8cecc", "#b85450"),
    # Actors & Resources
    "Role":        ns("#dae8fc", "#6c8ebf"),
    "Individual":  ns("#d5e8d4", "#82b366"),
    "Resource":    ns("#ffe6cc", "#d79b00"),
    "OrgUnit":     ns("#e1d5e7", "#9673a6"),
    # ISA / PartOF taxonomy nodes — triangle-ish, use distinct color
    "PartialISA":  ds("#f0e6ff", "#7B68EE"),
    "TotalISA":    ds("#d0b3ff", "#7B68EE"),
    "PartialPartOF": ds("#e6f0ff", "#4169E1"),
    "TotalPartOF":   ds("#b3ccff", "#4169E1"),
    # Concepts
    "Concept":     ns("#dae8fc", "#6c8ebf"),
    "Attribute":   ns("#d5e8d4", "#82b366"),
    # Product-Service
    "UnspecPS":    ns("#e1d5e7", "#9673a6"),
    "Feature":     ns("#dae8fc", "#6c8ebf"),
    "Component":   ns("#ffe6cc", "#d79b00"),
    "PartOFAND":   ds("#fff2cc", "#d6b656"),
    "PartOFOR":    ds("#e1d5e7", "#9673a6"),
    "PartOFXOR":   ds("#f8cecc", "#b85450"),
    # Technical
    "ISTechComp":  ns("#dae8fc", "#6c8ebf"),
    "ISReq":       ns("#f8cecc", "#b85450"),
    # Business Rule
    "Rule":        ns("#e1d5e7", "#9673a6"),
    # Logic nodes (AND / OR / AND/OR in Goal, Rule, Technical)
    "AND":         ds("#fff2cc", "#d6b656"),
    "OR":          ds("#d5e8d4", "#82b366"),
    "ANDOR":       ds("#dae8fc", "#6c8ebf"),
    # Helper nodes — used in all models
    "DevAction":   hs("#fff9c4", "#f0a500"),
    "Assumption":  hs("#e8f5e9", "#2e7d32"),
    "Comment":     hs("#fce4ec", "#c2185b"),
}

E = {
    "red":    es("#b85450"),
    "green":  es("#82b366", "#006600"),
    "orange": es("#d79b00"),
    "blue":   es("#6c8ebf", "#0050ef"),
    "purple": es("#9673a6"),
    "gray":   es("#666666"),
    "teal":   es("#006EAF"),
    "brown":  es("#7A4100"),
    "violet": es("#7B68EE"),
    "navy":   es("#4169E1"),
}

# ── Helper node shortcut ──────────────────────────────────────────────────────
def helper_nodes():
    """Development Action, Assumption, Comment appear in all models."""
    return [
        node("Development Action", "Development Action: <name>",
             C["DevAction"], w=200, h=50),
        node("Assumption",         "Assumption: <name>",
             C["Assumption"], w=180, h=50),
        node("Comment",            "Comment: <name>",
             C["Comment"],   w=180, h=50),
    ]

# ══════════════════════════════════════════════════════════════════════════════
# 1. GOAL MODEL
# ══════════════════════════════════════════════════════════════════════════════
goal_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("Goal",        "Goal: <name>",        C["Goal"]),
    node("KPI",         "KPI: <name>",         C["KPI"]),
    node("Problem",     "Problem: <name>",     C["Problem"]),
    node("Cause",       "Cause: <name>",       C["Cause"]),
    node("Opportunity", "Opportunity: <name>", C["Opportunity"]),
    node("Constraint",  "Constraint: <name>",  C["Constraint"]),
    # Logic nodes (NEW)
    node("AND",    "AND",    C["AND"],   w=60, h=60),
    node("OR",     "OR",     C["OR"],    w=60, h=60),
    node("AND/OR", "AND/OR", C["ANDOR"], w=60, h=60),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: Supports",    "Supports",    E["green"]),
    edge("Rel: Hinders",     "Hinders",     E["red"]),
    edge("Rel: Contradicts", "Contradicts", E["orange"]),
    edge("Rel: Causes",      "Causes",      E["purple"]),
    edge("Rel: measured by", "measured by", E["blue"]),
]
write_stencil("29_06_2026/4EM_GoalModel_Stencil_v4.xml", goal_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 2. BUSINESS PROCESS MODEL
# ══════════════════════════════════════════════════════════════════════════════
bp_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("Process",           "Process: <name>",           C["Process"]),
    node("External Process",  "External Process: <name>",  C["ExtProcess"]),
    node("Information Set",   "Information Set: <name>",   C["InfoSet"]),
    # Split/Join — AND (existing)
    node("Split (AND)", "Split (AND)", C["SplitAND"], w=60, h=60),
    node("Join (AND)",  "Join (AND)",  C["JoinAND"],  w=60, h=60),
    # Split/Join — OR (NEW)
    node("Split (OR)",  "Split (OR)",  C["SplitOR"],  w=60, h=60),
    node("Join (OR)",   "Join (OR)",   C["JoinOR"],   w=60, h=60),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: Input",    "Input",    E["green"]),
    edge("Rel: Output",   "Output",   E["blue"]),
    edge("Rel: creates",  "creates",  E["purple"]),
    edge("Rel: uses",     "uses",     E["teal"]),
    edge("Rel: requires", "requires", E["red"]),
    edge("Rel: motivates","motivates",E["orange"]),
]
write_stencil("29_06_2026/4EM_BusinessProcess_Stencil_v4.xml", bp_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 3. ACTORS AND RESOURCES MODEL
# ══════════════════════════════════════════════════════════════════════════════
ar_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("Role",               "Role: <name>",               C["Role"]),
    node("Individual",         "Individual: <name>",         C["Individual"]),
    node("Resource",           "Resource: <name>",           C["Resource"]),
    node("Organizational Unit","Organizational Unit: <name>",C["OrgUnit"], w=210, h=60),
    # ISA / PartOF taxonomy nodes (NEW)
    node("Partial-ISA",    "Partial-ISA",    C["PartialISA"],   w=120, h=50),
    node("Total-ISA",      "Total-ISA",      C["TotalISA"],     w=120, h=50),
    node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"],w=130, h=50),
    node("Total-PartOF",   "Total-PartOF",   C["TotalPartOF"],  w=130, h=50),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: plays",            "plays",            E["blue"]),
    edge("Rel: works in",         "works in",         E["green"]),
    edge("Rel: works at",         "works at",         E["teal"]),
    edge("Rel: Supplies",         "Supplies",         E["orange"]),
    edge("Rel: interacts with",   "interacts with",   E["purple"]),
    edge("Rel: responsible for",  "responsible for",  E["red"]),
    edge("Rel: belongs to",       "belongs to",       E["gray"]),
    edge("Rel: maintains",        "maintains",        E["brown"]),
]
write_stencil("29_06_2026/4EM_ActorsResources_Stencil_v4.xml", ar_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 4. CONCEPTS MODEL
# ══════════════════════════════════════════════════════════════════════════════
concepts_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("Concept",   "Concept: <name>",   C["Concept"]),
    node("Attribute", "Attribute: <name>", C["Attribute"]),
    node("KPI",       "KPI: <name>",       C["KPI"]),
    # ISA / PartOF taxonomy nodes (NEW)
    node("Partial-ISA",    "Partial-ISA",    C["PartialISA"],   w=120, h=50),
    node("Total-ISA",      "Total-ISA",      C["TotalISA"],     w=120, h=50),
    node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"],w=130, h=50),
    node("Total-PartOF",   "Total-PartOF",   C["TotalPartOF"],  w=130, h=50),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: 1:1",       "1:1",       E["blue"]),
    edge("Rel: 1:n",       "1:n",       E["green"]),
    edge("Rel: n:m",       "n:m",       E["orange"]),
    edge("Rel: refers to", "refers to", E["purple"]),
    edge("Rel: defines",   "defines",   E["teal"]),
]
write_stencil("29_06_2026/4EM_Concepts_Stencil_v4.xml", concepts_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 5. PRODUCT-SERVICE MODEL
# ══════════════════════════════════════════════════════════════════════════════
ps_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("Unspecific/Product/Service",
         "Unspecific/Product/Service: <name>", C["UnspecPS"], w=230, h=60),
    node("Feature",   "Feature: <name>",   C["Feature"]),
    node("Component", "Component: <name>", C["Component"]),
    # PartOF variants — AND / OR / XOR (NEW)
    node("PartOF (AND)", "PartOF (AND)", C["PartOFAND"], w=60, h=60),
    node("PartOF (OR)",  "PartOF (OR)",  C["PartOFOR"],  w=60, h=60),
    node("PartOF (XOR)", "PartOF (XOR)", C["PartOFXOR"], w=60, h=60),
    # ISA taxonomy nodes (NEW)
    node("Partial-ISA", "Partial-ISA", C["PartialISA"], w=120, h=50),
    node("Total-ISA",   "Total-ISA",   C["TotalISA"],   w=120, h=50),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: requires",  "requires",  E["red"]),
    edge("Rel: relates to","relates to",E["blue"]),
]
write_stencil("29_06_2026/4EM_ProductService_Stencil_v4.xml", ps_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 6. TECHNICAL COMPONENTS AND REQUIREMENTS MODEL
# ══════════════════════════════════════════════════════════════════════════════
tech_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("IS Technical Component",
         "IS Technical Component: <name>", C["ISTechComp"], w=230, h=60),
    node("IS Requirement",
         "IS Requirement: <name>",         C["ISReq"],      w=200, h=60),
    # Goal and Problem shared from Goal Model (appear in Technical model too)
    node("Goal",    "Goal: <name>",    C["Goal"]),
    node("Problem", "Problem: <name>", C["Problem"]),
    # Logic nodes (NEW)
    node("AND",    "AND",    C["AND"],   w=60, h=60),
    node("OR",     "OR",     C["OR"],    w=60, h=60),
    node("AND/OR", "AND/OR", C["ANDOR"], w=60, h=60),
    # PartOF taxonomy nodes (NEW)
    node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"], w=130, h=50),
    node("Total-PartOF",   "Total-PartOF",   C["TotalPartOF"],   w=130, h=50),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: has requirement", "has requirement", E["blue"]),
    edge("Rel: supports",        "supports",        E["green"]),
    edge("Rel: hinders",         "hinders",         E["red"]),
    edge("Rel: motivates",       "motivates",       E["purple"]),
    edge("Rel: has goal",        "has goal",        E["orange"]),
]
write_stencil("29_06_2026/4EM_Technical_Stencil_v4.xml", tech_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 7. BUSINESS RULE MODEL
# ══════════════════════════════════════════════════════════════════════════════
rule_shapes = [
    # ── Nodes ─────────────────────────────────────────────────────────────
    node("Rule",       "Rule: <name>",       C["Rule"]),
    node("Goal",       "Goal: <name>",       C["Goal"]),
    node("Process",    "Process: <name>",    C["Process"]),
    node("Constraint", "Constraint: <name>", C["Constraint"]),
    # Logic nodes (NEW)
    node("AND",    "AND",    C["AND"],   w=60, h=60),
    node("OR",     "OR",     C["OR"],    w=60, h=60),
    node("AND/OR", "AND/OR", C["ANDOR"], w=60, h=60),
    # Helper nodes (NEW)
    *helper_nodes(),
    # ── Relations ─────────────────────────────────────────────────────────
    edge("Rel: Supports",        "Supports",        E["green"]),
    edge("Rel: Hinders",         "Hinders",         E["red"]),
    edge("Rel: Contradicts",     "Contradicts",     E["orange"]),
    edge("Rel: Derivation Rule", "Derivation Rule", E["purple"]),
    edge("Rel: defines",         "defines",         E["blue"]),
]
write_stencil("29_06_2026/4EM_BusinessRule_Stencil_v4.xml", rule_shapes)

print("\nAll 7 stencils (v4) created successfully!")
print("\nNew nodes added vs v3:")
print("  Goal Model:      AND, OR, AND/OR + Dev Action, Assumption, Comment")
print("  Business Process: Split(OR), Join(OR) + Dev Action, Assumption, Comment")
print("  Actors & Resources: Partial-ISA, Total-ISA, Partial-PartOF, Total-PartOF + helpers")
print("  Concepts:        Partial-ISA, Total-ISA, Partial-PartOF, Total-PartOF + helpers")
print("  Product-Service: PartOF(OR), PartOF(XOR), Partial-ISA, Total-ISA + helpers")
print("  Technical:       Goal, Problem, AND, OR, AND/OR, Partial-PartOF, Total-PartOF + helpers")
print("  Business Rule:   AND, OR, AND/OR + Dev Action, Assumption, Comment")