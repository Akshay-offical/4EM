import xml.etree.ElementTree as ET
import json

# ══════════════════════════════════════════════════════════════════════════════
# CORE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

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

def custom_node(title, em_type, style, shape_type, w=180, h=60, bare=False):
    """
    shape_type:
        leftcut
        circle
        square
        chevron
    """

    if shape_type == "leftcut":
        style = (
            "shape=mxgraph.flowchart.card;"
            "whiteSpace=wrap;"
            "html=1;"
            + style
        )

    elif shape_type == "circle":
        style = (
            "shape=ellipse;"
            "aspect=fixed;"
            "whiteSpace=wrap;"
            "html=1;"
            + style
        )
        w = h = max(w, h)

    elif shape_type == "square":
        style = (
            "rounded=0;"
            "whiteSpace=wrap;"
            "html=1;"
            + style
        )
        w = h = max(w, h)

    elif shape_type == "chevron":
        style = (
            "shape=mxgraph.arrows.blockArrow;"
            "direction=east;"
            "whiteSpace=wrap;"
            "html=1;"
            + style
        )

    label = em_type if bare else "<name>"

    return {
        "xml": make_userobj_xml(label, em_type, style, w, h),
        "w": w,
        "h": h,
        "aspect": "fixed",
        "title": title,
    }

LEFTCUT = (
    "fillColor=#FFFFFF;"
    "strokeColor=#000000;"
    "strokeWidth=2;"
)

CIRCLE_WHITE = (
    "fillColor=#FFFFFF;"
    "strokeColor=#000000;"
    "strokeWidth=2;"
)

CIRCLE_BLACK = (
    "fillColor=#000000;"
    "strokeColor=#000000;"
    "fontColor=#FFFFFF;"
    "strokeWidth=2;"
)

SQUARE_WHITE = (
    "fillColor=#FFFFFF;"
    "strokeColor=#666666;"
    "strokeWidth=2;"
)

SQUARE_BLACK = (
    "fillColor=#000000;"
    "strokeColor=#000000;"
    "fontColor=#FFFFFF;"
    "strokeWidth=2;"
)

CHEVRON = (
    "fillColor=#FFF2CC;"
    "strokeColor=#FF0000;"
    "strokeWidth=2;"
)


def make_userobj_xml(label, em_type, style, w, h):
    """
    Builds a <UserObject> wrapped shape with em_type baked in as custom data.
    When the user drags this stencil and renames it, the label changes but
    em_type stays on the shape permanently. The converter reads em_type
    instead of parsing the label prefix.
    """
    gm = ET.Element("mxGraphModel")
    root = ET.SubElement(gm, "root")
    ET.SubElement(root, "mxCell", attrib={"id": "0"})
    ET.SubElement(root, "mxCell", attrib={"id": "1", "parent": "0"})
    obj = ET.SubElement(root, "UserObject", {
        "label": label,
        "em_type": em_type,   # ← baked in — converter reads this, not label prefix
        "id": "2",
    })
    inner = ET.SubElement(obj, "mxCell", {
        "style": style, "vertex": "1", "parent": "1",
    })
    ET.SubElement(inner, "mxGeometry", {
        "x": "0", "y": "0", "width": str(w), "height": str(h), "as": "geometry"
    })
    return ET.tostring(gm, encoding="unicode")


def node(title, em_type, style, w=180, h=60):
    """
    Node shape with em_type baked in as UserObject custom data.
    The user renames the shape in draw.io — the converter ignores the
    label prefix and reads em_type directly.
    Label placeholder is just '<name>' — no 'Type: ' prefix needed.
    """
    return {
        "xml": make_userobj_xml("<name>", em_type, style, w, h),
        "w": w, "h": h, "aspect": "fixed", "title": title,
    }


def bare_node(title, em_type, style, w=80, h=60):
    """
    Bare-label connector node (AND, OR, Split(AND), etc.) — label IS the
    type string itself, no separate name. Still gets em_type for the
    converter to use.
    """
    return {
        "xml": make_userobj_xml(em_type, em_type, style, w, h),
        "w": w, "h": h, "aspect": "fixed", "title": title,
    }


def edge(title, label, style):
    return {
        "xml": make_cell_xml(label, style, edge=True),
        "w": 160, "h": 60, "aspect": "fixed", "title": title,
    }


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
DIAMOND = "shape=mxgraph.flowchart.decision;whiteSpace=wrap;html=0;fontStyle=1;fontSize=11;"
HEXAGON = "shape=hexagon;whiteSpace=wrap;html=0;fontStyle=1;fontSize=10;perimeter=hexagonPerimeter2;"

def ns(fill, stroke): return BASE_NODE + f"fillColor={fill};strokeColor={stroke};"
def ds(fill, stroke): return DIAMOND   + f"fillColor={fill};strokeColor={stroke};"
def hs(fill, stroke): return HEXAGON   + f"fillColor={fill};strokeColor={stroke};"
def es(color, fc=None):
    fc = fc or color
    return BASE_EDGE + f"strokeColor={color};fontColor={fc};"

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    "Goal": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#B6DFA0;""strokeColor=#000000;""strokeWidth=2;",
    "KPI": "shape=mxgraph.flowchart.terminator;" "whiteSpace=wrap;" "html=1;" "fillColor=#B6E8A2;" "strokeColor=#000000;" "strokeWidth=2;",
    "Problem": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#FFC000;" "strokeColor=#000000;""strokeWidth=2;",
    "Cause": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#8DB4E2;" "strokeColor=#E46C0A;" "strokeWidth=2;",
    "Opportunity": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#38761D;" "strokeColor=#000000;" "strokeWidth=2;",
    "Constraint": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#FFFFFF;" "strokeColor=#F79646;" "strokeWidth=2;",
    "Process": "rounded=1;" "arcSize=40;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "ExtProcess": "rounded=0;" "shadow=1;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "InfoSet": "shape=parallelogram;" "perimeter=parallelogramPerimeter;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "SplitAND": "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "JoinAND": "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "SplitOR": "fillColor=#000000;" "strokeColor=#000000;" "fontColor=#FFFFFF;" "strokeWidth=2;",
    "JoinOR": "fillColor=#000000;" "strokeColor=#000000;" "fontColor=#FFFFFF;" "strokeWidth=2;",
    "Role": "fillColor=#8E7CC3;" "strokeColor=#000000;" "strokeWidth=2;",
    "Individual": "fillColor=#D9C2C2;" "strokeColor=#000000;" "strokeWidth=2;",
    "Resource": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#D9D9D9;" "strokeColor=#000000;" "strokeWidth=2;",
    "OrgUnit": "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#FFFFFF;" "strokeColor=#5B9BD5;" "strokeWidth=2;",
    "PartialISA": "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "TotalISA": "fillColor=#000000;" "strokeColor=#000000;" "fontColor=#FFFFFF;" "strokeWidth=2;",
    "PartialPartOF": "fillColor=#FFFFFF;" "strokeColor=#808080;" "strokeWidth=2;",
    "TotalPartOF": "fillColor=#000000;" "strokeColor=#000000;" "fontColor=#FFFFFF;" "strokeWidth=2;",
    "Concept": "shape=mxgraph.flowchart.terminator;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFF200;" "strokeColor=#000000;" "strokeWidth=2;",
    "Attribute": "shape=mxgraph.flowchart.terminator;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#3366FF;" "strokeWidth=2;",
    "UnspecPS": "shape=cube;" "whiteSpace=wrap;" "html=1;" "fillColor=#CFE8F6;" "strokeColor=#000000;" "strokeWidth=2;",
    "Feature": "shape=parallelogram;" "perimeter=parallelogramPerimeter;" "direction=north;" "whiteSpace=wrap;" "html=1;" "fillColor=#A9CCE3;" "strokeColor=#000000;" "strokeWidth=2;",
    "Component": "shape=mxgraph.flowchart.terminator;" "shadow=1;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "PartOFAND":     ds("#fff2cc", "#d6b656"),
    "PartOFOR":      ds("#e1d5e7", "#9673a6"),
    "PartOFXOR":     ds("#f8cecc", "#b85450"),
    "ISTechComp": "shape=ellipse;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "ISReq": "shape=ellipse;" "dashed=1;" "dashPattern=6 6;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "Rule":  "rounded=0;whiteSpace=wrap;html=1;" "fillColor=#FFFFFF;" "strokeColor=#F79646;" "strokeWidth=2;",
    "AND": "shape=triangle;" "direction=north;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "OR": "shape=triangle;" "direction=south;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "ANDOR": "shape=rhombus;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#000000;" "strokeWidth=2;",
    "DevAction": "fillColor=#FFF2CC;" "strokeColor=#FF0000;" "strokeWidth=2;",
    "Assumption": "shape=document;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#3366FF;" "strokeWidth=2;",
    "Comment": "shape=document;" "whiteSpace=wrap;" "html=1;" "fillColor=#FFFFFF;" "strokeColor=#3366FF;" "strokeWidth=2;",
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

def helper_nodes():
    return [
        custom_node("Development Action", "Development Action", C["DevAction"], "chevron",w=180, h=60),
        #node("Development Action", "Development Action", C["DevAction"], w=200, h=50),
        node("Assumption",         "Assumption",         C["Assumption"], w=180, h=50),
        node("Comment",            "Comment",            C["Comment"],    w=180, h=50),
    ]

# ══════════════════════════════════════════════════════════════════════════════
# 1. GOAL MODEL
# ══════════════════════════════════════════════════════════════════════════════
goal_shapes = [
    node("Goal",        "Goal",        C["Goal"]),
    node("KPI",         "KPI",         C["KPI"]),
    node("Problem",     "Problem",     C["Problem"]),
    node("Cause",       "Cause",       C["Cause"]),
    node("Opportunity", "Opportunity", C["Opportunity"]),
    node("Constraint",  "Constraint",  C["Constraint"]),
    bare_node("AND",    "AND",    C["AND"],   w=60, h=60),
    bare_node("OR",     "OR",     C["OR"],    w=60, h=60),
    bare_node("AND/OR", "AND/OR", C["ANDOR"], w=60, h=60),
    *helper_nodes(),
    edge("Rel: Supports",    "Supports",    E["green"]),
    edge("Rel: Hinders",     "Hinders",     E["red"]),
    edge("Rel: Contradicts", "Contradicts", E["orange"]),
    edge("Rel: Causes",      "Causes",      E["purple"]),
    edge("Rel: measured by", "measured by", E["blue"]),
]
write_stencil("generated_stencils/4EM_GoalModel_Stencil_v3.xml", goal_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 2. BUSINESS PROCESS MODEL
# ══════════════════════════════════════════════════════════════════════════════
bp_shapes = [
    #node("Process",          "Process",          C["Process"]),
    node("Process", "Process", C["Process"], w=180, h=50),
    node("External Process", "External Process", C["ExtProcess"]),
    node("Information Set",  "Information Set",  C["InfoSet"]),
    #bare_node("Split (AND)", "Split (AND)", C["SplitAND"], w=60, h=60),
    custom_node("Split (AND)", "Split (AND)", C["SplitAND"], "circle", w=60, h=60, bare=True),
    #bare_node("Join (AND)",  "Join (AND)",  C["JoinAND"],  w=60, h=60),
    custom_node("Join (AND)", "Join (AND)", C["JoinAND"], "circle", w=60, h=60, bare=True),
    #bare_node("Split (OR)",  "Split (OR)",  C["SplitOR"],  w=60, h=60),
    custom_node("Split (OR)",  "Split (OR)",  C["SplitOR"], "circle", w=60, h=60, bare=True),
    #bare_node("Join (OR)",   "Join (OR)",   C["JoinOR"],   w=60, h=60),
    custom_node("Join (OR)",  "Join (OR)",  C["JoinOR"], "circle", w=60, h=60, bare=True),
    *helper_nodes(),
    edge("Rel: Input",    "Input",    E["green"]),
    edge("Rel: Output",   "Output",   E["blue"]),
    edge("Rel: creates",  "creates",  E["purple"]),
    edge("Rel: uses",     "uses",     E["teal"]),
    edge("Rel: requires", "requires", E["red"]),
    edge("Rel: motivates","motivates",E["orange"]),
]
write_stencil("generated_stencils/4EM_BusinessProcess_Stencil_v3.xml", bp_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 3. ACTORS AND RESOURCES MODEL
# ══════════════════════════════════════════════════════════════════════════════
ar_shapes = [
    custom_node("Role", "Role", C["Role"], "leftcut", w=180, h=60 ),
    #node("Role",               "Role",               C["Role"]),
    #node("Individual",         "Individual",         C["Individual"]),
    custom_node("Individual", "Individual", C["Individual"], "leftcut", w=180, h=60 ),
    node("Resource",           "Resource",           C["Resource"]),
    node("Organizational Unit","Organizational Unit",C["OrgUnit"], w=210, h=60),
    custom_node("Partial-ISA","Partial-ISA", C["PartialISA"], "circle", w=55, h=55, bare=True),
    #bare_node("Partial-ISA",    "Partial-ISA",    C["PartialISA"],   w=120, h=50),
    custom_node("Total-ISA","Total-ISA", C["TotalISA"], "circle", w=55, h=55,bare=True),
    #bare_node("Total-ISA",      "Total-ISA",      C["TotalISA"],     w=120, h=50),
    custom_node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"], "square", w=55, h=55,bare=True),
    #bare_node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"],w=130, h=50),
    custom_node("Total-PartOF", "Total-PartOF", C["TotalPartOF"], "square", w=55, h=55,bare=True),
    #bare_node("Total-PartOF",   "Total-PartOF",   C["TotalPartOF"],  w=130, h=50),
    *helper_nodes(),
    edge("Rel: plays",           "plays",           E["blue"]),
    edge("Rel: works in",        "works in",        E["green"]),
    edge("Rel: works at",        "works at",        E["teal"]),
    edge("Rel: Supplies",        "Supplies",        E["orange"]),
    edge("Rel: interacts with",  "interacts with",  E["purple"]),
    edge("Rel: responsible for", "responsible for", E["red"]),
    edge("Rel: belongs to",      "belongs to",      E["gray"]),
    edge("Rel: maintains",       "maintains",       E["brown"]),
    edge("Rel: part of",         "part of",         E["navy"]),  # ← NEW
]
write_stencil("generated_stencils/4EM_ActorsResources_Stencil_v3.xml", ar_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 4. CONCEPTS MODEL
# ══════════════════════════════════════════════════════════════════════════════
concepts_shapes = [
    node("Concept",   "Concept",   C["Concept"]),
    node("Attribute", "Attribute", C["Attribute"]),
    node("KPI",       "KPI",       C["KPI"]),
    #bare_node("Partial-ISA",    "Partial-ISA",    C["PartialISA"],   w=120, h=50),
    custom_node("Partial-ISA","Partial-ISA", C["PartialISA"], "circle", w=55, h=55,bare=True),
    #bare_node("Total-ISA",      "Total-ISA",      C["TotalISA"],     w=120, h=50),
    custom_node("Total-ISA","Total-ISA", C["TotalISA"], "circle", w=55, h=55,bare=True),
    #bare_node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"],w=130, h=50),
    custom_node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"], "square", w=55, h=55,bare=True),
    #bare_node("Total-PartOF",   "Total-PartOF",   C["TotalPartOF"],  w=130, h=50),
    custom_node("Total-PartOF", "Total-PartOF", C["TotalPartOF"], "square", w=55, h=55,bare=True),
    *helper_nodes(),
    edge("Rel: 1:1",       "1:1",       E["blue"]),
    edge("Rel: 1:n",       "1:n",       E["green"]),
    edge("Rel: n:m",       "n:m",       E["orange"]),
    edge("Rel: refers to", "refers to", E["purple"]),
    edge("Rel: defines",   "defines",   E["teal"]),
]
write_stencil("generated_stencils/4EM_Concepts_Stencil_v3.xml", concepts_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 5. PRODUCT-SERVICE MODEL
# ══════════════════════════════════════════════════════════════════════════════
ps_shapes = [
    node("Unspecific/Product/Service", "Unspecific/Product/Service", C["UnspecPS"], w=180, h=55),
    node("Feature",   "Feature",   C["Feature"], w=145, h=55),
    node("Component", "Component", C["Component"], w=170, h=42),
    bare_node("PartOF (AND)", "PartOF (AND)", C["PartOFAND"], w=60, h=60),
    bare_node("PartOF (OR)",  "PartOF (OR)",  C["PartOFOR"],  w=60, h=60),
    bare_node("PartOF (XOR)", "PartOF (XOR)", C["PartOFXOR"], w=60, h=60),
    #bare_node("Partial-ISA",  "Partial-ISA",  C["PartialISA"], w=120, h=50),
    custom_node("Partial-ISA","Partial-ISA", C["PartialISA"], "circle", w=55, h=55,bare=True),
    #bare_node("Total-ISA",    "Total-ISA",    C["TotalISA"],   w=120, h=50),
    custom_node("Total-ISA","Total-ISA", C["TotalISA"], "circle", w=55, h=55,bare=True),
    *helper_nodes(),
    edge("Rel: requires",   "requires",   E["red"]),
    edge("Rel: relates to", "relates to", E["blue"]),
]
write_stencil("generated_stencils/4EM_ProductService_Stencil_v3.xml", ps_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 6. TECHNICAL COMPONENTS AND REQUIREMENTS MODEL
# ══════════════════════════════════════════════════════════════════════════════
tech_shapes = [
    node("IS Technical Component", "IS Technical Component", C["ISTechComp"], w=120, h=60),
    node("IS Requirement",         "IS Requirement",         C["ISReq"],      w=120, h=60),
    node("Goal",    "Goal",    C["Goal"]),
    node("Problem", "Problem", C["Problem"]),
    bare_node("AND",    "AND",    C["AND"],   w=60, h=60),
    bare_node("OR",     "OR",     C["OR"],    w=60, h=60),
    bare_node("AND/OR", "AND/OR", C["ANDOR"], w=60, h=60),
    #bare_node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"], w=130, h=50),
    custom_node("Partial-PartOF", "Partial-PartOF", C["PartialPartOF"], "square", w=55, h=55,bare=True),
    #bare_node("Total-PartOF",   "Total-PartOF",   C["TotalPartOF"],   w=130, h=50),
    custom_node("Total-PartOF", "Total-PartOF", C["TotalPartOF"], "square", w=55, h=55,bare=True),
    *helper_nodes(),
    edge("Rel: has requirement", "has requirement", E["blue"]),
    edge("Rel: supports",        "supports",        E["green"]),
    edge("Rel: hinders",         "hinders",         E["red"]),
    edge("Rel: motivates",       "motivates",       E["purple"]),
    edge("Rel: has goal",        "has goal",        E["orange"]),
]
write_stencil("generated_stencils/4EM_Technical_Stencil_v3.xml", tech_shapes)

# ══════════════════════════════════════════════════════════════════════════════
# 7. BUSINESS RULE MODEL — Goal/Process/Constraint REMOVED
# ══════════════════════════════════════════════════════════════════════════════
rule_shapes = [
    node("Rule", "Rule", C["Rule"]),   # only Rule remains — Goal/Process/Constraint removed
    bare_node("AND",    "AND",    C["AND"],   w=60, h=60),
    bare_node("OR",     "OR",     C["OR"],    w=60, h=60),
    bare_node("AND/OR", "AND/OR", C["ANDOR"], w=60, h=60),
    *helper_nodes(),
    edge("Rel: Supports",        "Supports",        E["green"]),
    edge("Rel: Hinders",         "Hinders",         E["red"]),
    edge("Rel: Contradicts",     "Contradicts",     E["orange"]),
    edge("Rel: Derivation Rule", "Derivation Rule", E["purple"]),
    edge("Rel: defines",         "defines",         E["blue"]),
]
write_stencil("generated_stencils/4EM_BusinessRule_Stencil_v3.xml", rule_shapes)

print("\nAll 7 stencils created successfully!")