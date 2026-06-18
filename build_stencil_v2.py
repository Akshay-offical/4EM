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
    return {"xml": make_cell_xml(label, style, w=w, h=h), "w": w, "h": h, "aspect": "fixed", "title": title}

def edge(title, label, style):
    return {"xml": make_cell_xml(label, style, edge=True), "w": 160, "h": 60, "aspect": "fixed", "title": title}

# ── Base styles ──────────────────────────────────────────────────────────────
BASE_NODE  = "rounded=1;whiteSpace=wrap;html=0;fontStyle=1;fontSize=11;"
BASE_EDGE  = "edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeWidth=2;fontStyle=1;"

def ns(fill, stroke):
    return BASE_NODE + f"fillColor={fill};strokeColor={stroke};"

def es(color, fc=None):
    fc = fc or color
    return BASE_EDGE + f"strokeColor={color};fontColor={fc};"

# ── Shared node colors ────────────────────────────────────────────────────────
C = {
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
    "SplitAND":    "shape=mxgraph.flowchart.decision;whiteSpace=wrap;html=0;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=11;",
    "JoinAND":     "shape=mxgraph.flowchart.decision;whiteSpace=wrap;html=0;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=11;",
    # Actors & Resources
    "Role":        ns("#dae8fc", "#6c8ebf"),
    "Individual":  ns("#d5e8d4", "#82b366"),
    "Resource":    ns("#ffe6cc", "#d79b00"),
    "OrgUnit":     ns("#e1d5e7", "#9673a6"),
    # Concepts
    "Concept":     ns("#dae8fc", "#6c8ebf"),
    "Attribute":   ns("#d5e8d4", "#82b366"),
    # Product-Service
    "UnspecPS":    ns("#e1d5e7", "#9673a6"),
    "Feature":     ns("#dae8fc", "#6c8ebf"),
    "Component":   ns("#ffe6cc", "#d79b00"),
    "PartOFAND":   "shape=mxgraph.flowchart.decision;whiteSpace=wrap;html=0;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=11;",
    # Technical
    "ISTechComp":  ns("#dae8fc", "#6c8ebf"),
    "ISReq":       ns("#f8cecc", "#b85450"),
    # Business Rule
    "Rule":        ns("#e1d5e7", "#9673a6"),
}

# ── Edge colors ───────────────────────────────────────────────────────────────
E = {
    "red":    es("#b85450"),
    "green":  es("#82b366", "#006600"),
    "orange": es("#d79b00"),
    "blue":   es("#6c8ebf", "#0050ef"),
    "purple": es("#9673a6"),
    "gray":   es("#666666"),
    "teal":   es("#006EAF"),
    "brown":  es("#7A4100"),
}

def write_stencil(filename, shapes):
    library = ET.Element("mxlibrary")
    library.text = json.dumps(shapes, ensure_ascii=False)
    xml_str = ET.tostring(library, encoding="unicode")
    out = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    with open(filename, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  Written: {filename}  ({len(shapes)} shapes)")

# ════════════════════════════════════════════════════════════════════════════════
# 1. GOAL MODEL
# ════════════════════════════════════════════════════════════════════════════════
goal_shapes = [
    node("Goal",        "Goal: &lt;name&gt;",        C["Goal"]),
    node("KPI",         "KPI: &lt;name&gt;",         C["KPI"]),
    node("Problem",     "Problem: &lt;name&gt;",     C["Problem"]),
    node("Cause",       "Cause: &lt;name&gt;",       C["Cause"]),
    node("Opportunity", "Opportunity: &lt;name&gt;", C["Opportunity"]),
    node("Constraint",  "Constraint: &lt;name&gt;",  C["Constraint"]),
    edge("Rel: Supports",   "Supports",   E["green"]),
    edge("Rel: Hinders",    "Hinders",    E["red"]),
    edge("Rel: Contradicts","Contradicts",E["orange"]),
    edge("Rel: Causes",     "Causes",     E["purple"]),
    edge("Rel: measured by","measured by",E["blue"]),
]
write_stencil("4EM_GoalModel_Stencil.xml", goal_shapes)

# ════════════════════════════════════════════════════════════════════════════════
# 2. BUSINESS PROCESS MODEL
# ════════════════════════════════════════════════════════════════════════════════
bp_shapes = [
    node("Process",          "Process: &lt;name&gt;",          C["Process"]),
    node("External Process", "External Process: &lt;name&gt;", C["ExtProcess"]),
    node("Information Set",  "Information Set: &lt;name&gt;",  C["InfoSet"]),
    node("Split (AND)",      "Split (AND)",                    C["SplitAND"], w=60, h=60),
    node("Join (AND)",       "Join (AND)",                     C["JoinAND"],  w=60, h=60),
    edge("Rel: Input",   "Input",   E["green"]),
    edge("Rel: Output",  "Output",  E["blue"]),
    edge("Rel: Triggers","Triggers",E["orange"]),
    edge("Rel: creates", "creates", E["purple"]),
    edge("Rel: uses",    "uses",    E["teal"]),
]
write_stencil("4EM_BusinessProcess_Stencil.xml", bp_shapes)

# ════════════════════════════════════════════════════════════════════════════════
# 3. ACTORS AND RESOURCES MODEL
# ════════════════════════════════════════════════════════════════════════════════
ar_shapes = [
    node("Role",              "Role: &lt;name&gt;",              C["Role"]),
    node("Individual",        "Individual: &lt;name&gt;",        C["Individual"]),
    node("Resource",          "Resource: &lt;name&gt;",          C["Resource"]),
    node("Organizational Unit","Organizational Unit: &lt;name&gt;",C["OrgUnit"], w=200, h=60),
    edge("Rel: plays",           "plays",           E["blue"]),
    edge("Rel: works in",        "works in",        E["green"]),
    edge("Rel: works at",        "works at",        E["teal"]),
    edge("Rel: Supplies",        "Supplies",        E["orange"]),
    edge("Rel: interacts with",  "interacts with",  E["purple"]),
    edge("Rel: responsible for", "responsible for", E["red"]),
    edge("Rel: belongs to",      "belongs to",      E["gray"]),
    edge("Rel: maintains",       "maintains",       E["brown"]),
]
write_stencil("4EM_ActorsResources_Stencil.xml", ar_shapes)

# ════════════════════════════════════════════════════════════════════════════════
# 4. CONCEPTS MODEL
# ════════════════════════════════════════════════════════════════════════════════
concepts_shapes = [
    node("Concept",   "Concept: &lt;name&gt;",   C["Concept"]),
    node("Attribute", "Attribute: &lt;name&gt;", C["Attribute"]),
    node("KPI",       "KPI: &lt;name&gt;",       C["KPI"]),
    edge("Rel: 1:1",       "1:1",       E["blue"]),
    edge("Rel: 1:n",       "1:n",       E["green"]),
    edge("Rel: n:m",       "n:m",       E["orange"]),
    edge("Rel: refers to", "refers to", E["purple"]),
    edge("Rel: defines",   "defines",   E["teal"]),
]
write_stencil("4EM_Concepts_Stencil.xml", concepts_shapes)

# ════════════════════════════════════════════════════════════════════════════════
# 5. PRODUCT-SERVICE MODEL
# ════════════════════════════════════════════════════════════════════════════════
ps_shapes = [
    node("Unspecific/Product/Service", "Unspecific/Product/Service: &lt;name&gt;", C["UnspecPS"], w=220, h=60),
    node("Feature",   "Feature: &lt;name&gt;",   C["Feature"]),
    node("Component", "Component: &lt;name&gt;", C["Component"]),
    node("PartOF (AND)", "PartOF (AND)",          C["PartOFAND"], w=60, h=60),
    edge("Rel: requires",  "requires",  E["red"]),
    edge("Rel: relates to","relates to",E["blue"]),
]
write_stencil("4EM_ProductService_Stencil.xml", ps_shapes)

# ════════════════════════════════════════════════════════════════════════════════
# 6. TECHNICAL COMPONENTS AND REQUIREMENTS MODEL
# ════════════════════════════════════════════════════════════════════════════════
tech_shapes = [
    node("IS Technical Component", "IS Technical Component: &lt;name&gt;", C["ISTechComp"], w=220, h=60),
    node("IS Requirement",         "IS Requirement: &lt;name&gt;",         C["ISReq"],      w=200, h=60),
    edge("Rel: has requirement", "has requirement", E["blue"]),
    edge("Rel: supports",        "supports",        E["green"]),
    edge("Rel: hinders",         "hinders",         E["red"]),
    edge("Rel: motivates",       "motivates",       E["purple"]),
    edge("Rel: has goal",        "has goal",        E["orange"]),
]
write_stencil("4EM_Technical_Stencil.xml", tech_shapes)

# ════════════════════════════════════════════════════════════════════════════════
# 7. BUSINESS RULE MODEL
# ════════════════════════════════════════════════════════════════════════════════
rule_shapes = [
    node("Rule",        "Rule: &lt;name&gt;",        C["Rule"]),
    node("Goal",        "Goal: &lt;name&gt;",        C["Goal"]),
    node("Process",     "Process: &lt;name&gt;",     C["Process"]),
    node("Constraint",  "Constraint: &lt;name&gt;",  C["Constraint"]),
    edge("Rel: Supports",       "Supports",        E["green"]),
    edge("Rel: Hinders",        "Hinders",         E["red"]),
    edge("Rel: Contradicts",    "Contradicts",     E["orange"]),
    edge("Rel: Derivation Rule","Derivation Rule", E["purple"]),
    edge("Rel: defines",        "defines",         E["blue"]),
]
write_stencil("4EM_BusinessRule_Stencil.xml", rule_shapes)

print("\nAll 7 stencils created successfully!")