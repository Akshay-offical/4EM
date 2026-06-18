# 4EM
This repo contains solution for draw.io models to be converted and implemented in 4EM modeling tool.

sample xml flow from draw.io
<mxfile host="app.diagrams.net">
  <diagram name="Goal Model" id="goal-model">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <mxCell id="2"
                value="Goal: Maximize Service Quality"
                style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
                vertex="1"
                parent="1">
          <mxGeometry x="150" y="180" width="160" height="60" as="geometry"/>
        </mxCell>

        <mxCell id="3"
                value="KPI: Customer Satisfaction Score"
                style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;"
                vertex="1"
                parent="1">
          <mxGeometry x="430" y="180" width="160" height="60" as="geometry"/>
        </mxCell>

        <mxCell id="4"
                value="measured by"
                style="edgeStyle=orthogonalEdgeStyle;"
                edge="1"
                source="2"
                target="3"
                parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

Key observation
1. Every element is an <mxCell>
2. Boxes have vertex="1" and a <mxGeometry> with x, y, width, height in pixels
3. Arrows have edge="1" with source="id" and target="id" pointing to their two endpoint boxes
4. id="0" and id="1" are internal draw.io housekeeping cells — always present
5. The label (value) on boxes contains our convention "Type: Name"
6. The label on arrows contains the relation type "measured by"


-----------------------------------------------------
sample 4em plain text
VERSION <4.0>

BUSINESS PROCESS MODEL <4EM_Goal> : <4EM 2.7>
VERSION <>
TYPE <Goal Model>

    ATTRIBUTE <Author>
    VALUE ""

    ATTRIBUTE <Description>
    VALUE ""


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


INSTANCE <Customer Satisfaction Score> : <KPI>

    ATTRIBUTE <Position>
    VALUE "NODE x:11.4cm y:4.8cm w:4.2cm h:1.6cm index:2"

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

key observations
1. ADL uses INSTANCE <name> : <type> — name and type are separate
2. ADL uses centimetres not pixels
3. ADL references nodes by NAME+TYPE in relations, not by numeric ID
4. ADL has specific mandatory ATTRIBUTE blocks even if empty
5. ADL is plain text, not XML

-------------------------------------------------------------------

Challenges.
 
1. Extract type and name from one label
draw.io stores: value="Goal: Maximize Service Quality"
4EM needs: INSTANCE <Maximize Service Quality> : <Goal>
Solution : Split on first colon

value = "Goal: Maximize Service Quality" , 
ntype, name = value.split(":", 1)

# ntype = "Goal"
# name  = "Maximize Service Quality"

2. Convert pixels to centimetres
draw.io stores: <mxGeometry x="150" y="180" width="160" height="60"/>
4EM needs: VALUE "NODE x:4.0cm y:4.8cm w:4.2cm h:1.6cm index:1"
Solution : Conversion to centimeters

PX_PER_CM = 37.8   # 96 DPI ÷ 2.54 cm/inch
px_to_cm(px) function

3. Resolve edge endpoints from IDs to names
draw.io stores: <mxCell id="4" edge="1" source="2" target="3" value="measured by"/>
4EM needs:
    FROM <Maximize Service Quality> : <Goal>
    TO <Customer Satisfaction Score> : <KPI>

Solution: Parsed entire boxes before processing any egde processing

4. Edge labels stored as separate child cells
Normal arrow (label on the edge itself): <mxCell id="9" edge="1" source="2" target="3" value="Contradicts"/>

Arrow where label was added by double-clicking (label as separate child cell):        <mxCell id="9" edge="1" source="2" target="3" value=""/>
<mxCell id="10" vertex="1" parent="9"
        style="edgeLabel;..." value="Contradicts"/>

Solution: 3-pass solution
1. Collect all edges in a set,
2. when we see edgeLabel type of processing
3. other processing. 

5. Description addition(Tooltip)
before Tooltip: 
<mxCell id="8"
        value="Constraint: Annual Budget Limit"
        vertex="1"
        parent="1">
  <mxGeometry x="670" y="180" width="160" height="60"/>
</mxCell>
After tooltip: 
<UserObject id="8"
            label="Constraint: Annual Budget Limit"
            tooltip="A strict financial restriction">
  <mxCell vertex="1" parent="1">
    <mxGeometry x="670" y="180" width="160" height="60"/>
  </mxCell>
</UserObject> 

Solution: normalize_cells() function to handle both the cases . 

---------------------------------------------------

Program workflow
1. ET.parse("input.drawio")
   → loads XML into memory tree

2. root.find(".//root")
   → finds the <root> element containing all cells

3. normalize_cells(graph_root)
   → walks direct children
   → converts both plain <mxCell> and <UserObject> into uniform dicts
   → result: list of dicts, all with id/value/tooltip/vertex/edge/geometry

4. Pass 1 — build edge_ids set
   → loop all cells, collect id of every cell where edge="1"
   → result: edge_ids = {"9","10","11","12","13","14"}

5. Main pass — separate nodes from edges
   → for each cell:

   IF edge="1":
     → store {id, source, target, label} in edges list

   IF vertex="1" AND (edgeLabel in style OR parent in edge_ids):
     → store text in edge_labels[parent_id]
     → skip (not a real node)

   IF vertex="1" AND none of the above:
     → split value on ":" → ntype, name
     → read tooltip → description
     → px_to_cm(x), px_to_cm(y), px_to_cm(w), px_to_cm(h)
     → assign next_index
     → store full dict in nodes[cell_id]

6. Pass 2 — fill empty edge labels
   → for each edge where label is empty:
     → look up edge_labels[edge_id]
     → fill in the label

7. Write ADL header
   → VERSION <4.0>
   → BUSINESS PROCESS MODEL <4EM_Goal> : <4EM 2.7>
   → TYPE <Goal Model>
   → model-level ATTRIBUTE blocks

8. Write INSTANCE blocks
   → for each node in nodes.values():
     → emit_instance(node)
     → writes INSTANCE <name> : <type> with Position, Description, etc.

9. Write RELATION blocks
   → for each edge in edges:
     → src = nodes[edge["source"]]  ← ID lookup → full node dict
     → tgt = nodes[edge["target"]]  ← ID lookup → full node dict
     → emit_relation(src, tgt, edge["label"], idx)
     → writes RELATION block with FROM/TO using names not IDs

10. f.write() → saves the ADL file

11. Print summary to console

-----------------------------------------------------------
Stencil
A stencil file is a JSON array wrapped in XML:
example 
# For a box/node:
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="Goal: <name>" style="rounded=1;fillColor=..." vertex="1">
      <mxGeometry x="0" y="0" width="180" height="60"/>
    </mxCell>
  </root>
</mxGraphModel>

# For an arrow/edge:
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="Supports" style="edgeStyle=...strokeColor=..." edge="1">
      <mxGeometry relative="1">
        <mxPoint x="0" y="30" as="sourcePoint"/>
        <mxPoint x="160" y="30" as="targetPoint"/>
      </mxGeometry>
    </mxCell>
  </root>
</mxGraphModel>

Create stencil using build_stencil_v2.py and running that will create sub models for 4em there edges and nodes. Then add that to draw.io library using File-> Open Library from -> Device and upload the xml files, then drag and drop custom solutions
