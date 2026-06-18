"""
draw.io (Goal Model) -> 4EM ADL converter
-------------------------------------------
Reads a draw.io .drawio/.xml file where:
  - vertices (boxes) are labeled "TYPE: Name"   e.g. "Goal: Maximize Service Quality"
  - edges (arrows) are labeled with a 4EM relation type e.g. "Supports", "Hinders"

Outputs a .adl file containing one BUSINESS PROCESS MODEL block (Goal Model)
with INSTANCE entries for every box and RELATION entries for every arrow.
"""

import xml.etree.ElementTree as ET
import sys



PX_PER_CM = 37.8  # standard 96dpi conversion (96 / 2.54)

import re
from html import unescape

def strip_html(text):
    if not text:
        return ""
    text = unescape(text)                      # &nbsp; → " ", &amp; → "&", etc.
    text = re.sub(r"<[^>]+>", "", text)        # remove all <span>, <b>, etc.
    return text.strip()


def px_to_cm(px):
    return round(float(px) / PX_PER_CM, 1)


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
                "id": child.get("id"),
                "value": strip_html(child.get("value")),
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
                "id": child.get("id"),
                "value": strip_html(child.get("label")),   # note: "label", not "value"
                "tooltip": child.get("tooltip"),
                "style": inner.get("style", ""),
                "vertex": inner.get("vertex"),
                "edge": inner.get("edge"),
                "parent": inner.get("parent"),
                "source": inner.get("source"),
                "target": inner.get("target"),
                "geometry": inner.find("mxGeometry"),
            })
    return entries


def parse_drawio(input_path):
    tree = ET.parse(input_path)
    root = tree.getroot()
    graph_root = root.find(".//root")
    if graph_root is None:
        raise ValueError("Could not find <root> element in draw.io file")

    all_cells = normalize_cells(graph_root)

    # ── Pass 1: find every cell id that is an EDGE ──────────────────────────
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

            # ── Detect "edge label" cells ───────────────────────────────────
            if "edgeLabel" in style or parent in edge_ids:
                edge_labels[parent] = value
                continue

            if ":" in value:
                ntype, name = value.split(":", 1)
                ntype, name = ntype.strip(), name.strip()
            else:
                ntype, name = "Unknown", value
                print(f"WARNING: node '{value}' has no 'Type: Name' format "
                      f"(check this box's label - it should be like 'Goal: My Goal')")

            geom = cell.get("geometry")
            x = geom.get("x", 0) if geom is not None else 0
            y = geom.get("y", 0) if geom is not None else 0
            w = geom.get("width", 0) if geom is not None else 0
            h = geom.get("height", 0) if geom is not None else 0

            description = (cell.get("tooltip") or "").strip()
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

    # ── Pass 2: fill in any edge labels that came from separate label cells ─
    for e in edges:
        if not e["label"]:
            e["label"] = edge_labels.get(e["id"], "")
            if not e["label"]:
                print(f"WARNING: edge {e['id']} (source={e['source']}, "
                      f"target={e['target']}) has no label/relation type")

    return nodes, edges


def emit_instance(n):
    out = []
    out.append(f"INSTANCE <{n['name']}> : <{n['type']}>")
    out.append("")
    out.append("\tATTRIBUTE <Position>")
    out.append(f'\tVALUE "NODE x:{n["x"]}cm y:{n["y"]}cm w:{n["w"]}cm h:{n["h"]}cm index:{n["index"]}"')
    out.append("")
    out.append("\tATTRIBUTE <External tool coupling>")
    out.append('\tVALUE ""')
    out.append("")
    out.append("\tATTRIBUTE <Description>")
    out.append(f'\tVALUE "{n["description"]}"')
    out.append("")
    out.append("\tATTRIBUTE <Intermodel-Relations>")
    out.append("\tVALUE")
    out.append("")
    out.append("\tATTRIBUTE <Decomposition>")
    out.append('\tVALUE ""')
    out.append("")
    out.append("\tATTRIBUTE <Defined by>")
    out.append('\tVALUE ""')
    out.append("")
    out.append("\tATTRIBUTE <Attributes>")
    out.append("\tVALUE")
    out.append("")
    out.append("")
    return "\n".join(out)


def emit_relation(src, tgt, label, idx):
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
    out.append('\tVALUE ""')
    out.append("")
    out.append("\tATTRIBUTE <IR>")
    out.append('\tVALUE "False"')
    out.append("")
    out.append("")
    return "\n".join(out)


def convert(input_path, output_path,
            model_name="4EM_Goal", model_type="Goal Model"):

    nodes, edges = parse_drawio(input_path)

    lines = []
    lines.append("VERSION <4.0>")
    lines.append("")
    lines.append("")
    lines.append(f"BUSINESS PROCESS MODEL <{model_name}> : <4EM 2.7>")
    lines.append("VERSION <>")
    lines.append(f"TYPE <{model_type}>")
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
        lines.append(emit_relation(src, tgt, e["label"], idx))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # summary
    print(f"Converted {len(nodes)} nodes and {len(edges)} relations.")
    for n in nodes.values():
        print(f"  INSTANCE <{n['name']}> : <{n['type']}>  "
              f"x:{n['x']}cm y:{n['y']}cm w:{n['w']}cm h:{n['h']}cm")
    for e in edges:
        s, t = nodes.get(e["source"]), nodes.get(e["target"])
        if s and t:
            print(f"  RELATION  {s['name']} --[{e['label']}]--> {t['name']}")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])