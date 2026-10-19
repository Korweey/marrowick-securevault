import xml.etree.ElementTree as ET
root = ET.Element("mxfile", host="app.diagrams.net")
d = ET.SubElement(root, "diagram", name="Marrowick Architecture", id="arch")
m = ET.SubElement(d, "mxGraphModel", dx="1800", dy="1000", grid="1", gridSize="10",
                  page="1", pageWidth="1980", pageHeight="1000", math="0", shadow="0")
r = ET.SubElement(m, "root")
ET.SubElement(r, "mxCell", id="0"); ET.SubElement(r, "mxCell", id="1", parent="0")

COL = {"storage":"#7AA116","security":"#DD344C","analytics":"#8C4FFF",
       "compute":"#ED7100","integration":"#E7157B","mgmt":"#E7157B"}
def cell(id, value, style, x, y, w, h):
    c = ET.SubElement(r, "mxCell", id=id, value=value, style=style, vertex="1", parent="1")
    ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as":"geometry"})
def icon(id, label, res, cat, x, y, size=78, pos="bottom"):
    lab = ("verticalLabelPosition=bottom;verticalAlign=top;align=center;" if pos=="bottom"
           else "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=6;")
    style = ("sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;strokeColor=#ffffff;dashed=0;"
             f"html=1;fontSize=11;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;"
             f"resIcon=mxgraph.aws4.{res};fillColor={COL[cat]};" + lab)
    cell(id, label, style, x, y, size, size)
def user(id, label, x, y):
    cell(id, label, "sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#232F3D;strokeColor=none;dashed=0;"
         "verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;aspect=fixed;"
         "shape=mxgraph.aws4.user;", x, y, 60, 60)
def box(id, label, x, y, w, h, fill="#ffffff", stroke="#232F3E", extra=""):
    cell(id, label, f"rounded=1;whiteSpace=wrap;html=1;fontSize=11;fillColor={fill};strokeColor={stroke};{extra}", x, y, w, h)
def edge(id, s, t, label="", dashed=False, extra=""):
    st = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;fontSize=10;"
          "labelBackgroundColor=#ffffff;" + ("dashed=1;strokeColor=#888888;strokeWidth=1;" if dashed
          else "strokeColor=#232F3E;strokeWidth=2;") + extra)
    c = ET.SubElement(r, "mxCell", id=id, value=label, style=st, edge="1", parent="1", source=s, target=t)
    ET.SubElement(c, "mxGeometry", relative="1", **{"as":"geometry"})

# ---- Title
cell("title", "<b>Marrowick Health Analytics – SecureVault Governance Platform</b><br>"
     "<font style='font-size:12px'>CCGC 5506 Mid-Term Project 4 · Group H: Saheedat O. Abbas (N10038753) &amp; Qawiyy A. Rabiu (N10038749)</font>",
     "text;html=1;align=left;verticalAlign=middle;fontSize=18;", 40, 20, 1100, 60)

# ---- Groups (drawn first so they sit behind)
cell("cloud", "AWS Cloud (AWS Academy Learner Lab)", "points=[];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
     "fontSize=12;fontStyle=1;container=0;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;"
     "grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;"
     "spacingLeft=30;fontColor=#232F3E;dashed=0;", 250, 100, 1440, 870)
cell("region", "Region: us-east-1", "points=[];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;"
     "container=0;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;"
     "strokeColor=#00A4A6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=1;",
     270, 135, 1400, 815)
box("gate", "", 640, 300, 520, 420, fill="#FDF0F6", stroke="#E7157B", extra="dashed=1;arcSize=3;")
box("audit", "<b>Audit &amp; Monitoring</b> (runs continuously in the background)", 290, 750, 1360, 180,
    fill="#F4F4F4", stroke="#888888", extra="dashed=1;arcSize=4;verticalAlign=top;align=left;spacingLeft=10;")

# ---- Data sources
box("clinics", "<b>Clinic Partners</b><br>(synthetic data sources)", 40, 120, 190, 340,
    fill="#F4F4F4", stroke="#888888", extra="verticalAlign=top;dashed=1;")
box("ca", "<b>Clinic A</b><br>Brambleton Family Clinic", 60, 175, 150, 65)
box("cb", "<b>Clinic B</b><br>Fenwick Ridge Medical Centre", 60, 275, 150, 65)
box("cc", "<b>Clinic C</b><br>Aldermoor Community Health", 60, 375, 150, 65)

# ---- Top row: security services
icon("kms", "<b>AWS KMS</b><br>Customer-managed key<br>(encrypts raw, quarantine<br>&amp; curated buckets)",
     "key_management_service", "security", 640, 165, 70)
icon("macie", "<b>Amazon Macie</b> (optional)<br>scheduled discovery<br>on tenant buckets", "macie", "security", 1300, 165, 70)
icon("iam", "<b>IAM – LabRole</b> (fixed)<br>least-privilege policies<br>documented as JSON", "identity_and_access_management",
     "security", 1500, 165, 70)

# ---- Main flow
icon("raw", "<b>S3 Raw / Landing bucket</b><br>raw/clinic-a/<br>raw/clinic-b/<br>raw/clinic-c/<br>(SSE-KMS + per-tenant<br>bucket policies)",
     "s3", "storage", 320, 400)
icon("glue", "<b>AWS Glue Crawler</b><br>+ Data Catalog", "glue", "analytics", 480, 400)
icon("sfn", "<b>AWS Step Functions</b> – PII gate workflow", "step_functions", "integration", 655, 312, 48, pos="right")
icon("lambda", "<b>AWS Lambda</b><br>regex PII/PHI scan<br>(health card, SIN, email)", "lambda", "compute", 680, 430)
cell("choice", "<b>Choice:</b><br>PII found?", "rhombus;whiteSpace=wrap;html=1;fontSize=11;fillColor=#fff2cc;strokeColor=#d6b656;",
     830, 424, 110, 90)
icon("quar", "<b>S3 Quarantine bucket</b><br>blocked batch (SSE-KMS)", "s3", "storage", 846, 570)
icon("sns", "<b>Amazon SNS</b><br>gate-failure alert", "sns", "integration", 1040, 570)
user("secteam", "Security / Governance<br>team (email)", 1230, 580)
icon("cur", "<b>S3 Curated bucket</b><br>curated/clinic-a|b|c/<br>(SSE-KMS)", "s3", "storage", 1220, 424)
icon("lf", "<b>Access layer</b><br>Athena views (enforced)<br>Lake Formation filters<br>(design-only – blocked in lab)", "lake_formation", "analytics", 1380, 424)
icon("athena", "<b>Amazon Athena</b><br>analyst workgroup", "athena", "analytics", 1530, 424)
user("u1", "<b>Clinic Analyst</b><br>own clinic rows only", 1760, 320)
user("u2", "<b>Corporate Analyst</b><br>all clinics, no PII columns", 1760, 500)
box("lfnote", "<b>Access separation (tested 7/7)</b><br>• Clinic analyst: view_clinic_a_analyst – own rows, no notes_field<br>"
    "• Corporate analyst: view_corporate_analyst – all rows, no notes_field / patient_ref",
    1690, 640, 270, 110, fill="#F3EDFF", stroke="#8C4FFF", extra="align=left;spacingLeft=6;")

# ---- Audit row
icon("trail", "<b>AWS CloudTrail</b><br>records all API calls", "cloudtrail", "mgmt", 330, 790, 70)
icon("trails3", "<b>S3 CloudTrail logs</b><br>bucket (validated)", "s3", "storage", 560, 790, 70)
icon("athena2", "<b>Amazon Athena</b><br>audit queries", "athena", "analytics", 790, 790, 70)
box("auditq", "<b>Audit questions answered</b><br>Q1 Who accessed curated clinic-c data?<br>Q2 Which calls changed bucket security?<br>Q3 Denied / anomalous attempts",
    960, 785, 300, 90, fill="#ffffff", stroke="#888888", extra="align=left;spacingLeft=6;")
icon("cw", "<b>Amazon CloudWatch</b><br>Lambda / Step Functions<br>logs &amp; metrics", "cloudwatch_2", "mgmt", 1340, 790, 70)

# ---- Legend
box("legend", "<b>Legend</b><br>━━▶ data flow (numbered steps)<br>- - ▶ encryption / control / logging<br><br>"
    "<b>Steps</b><br>1 Upload clinic CSVs<br>2 Crawl &amp; catalog<br>3 Regex PII scan<br>4 Clean or flagged?<br>"
    "5a Clean → curated<br>5b Flagged → quarantine + SNS<br>6 Access layer (Athena views)<br>7 Analysts query via Athena",
    40, 520, 190, 200, fill="#ffffff", stroke="#888888", extra="align=left;verticalAlign=top;spacingLeft=6;spacingTop=4;")

# ---- Edges
edge("e1", "ca", "raw", "1. Upload CSV", extra="entryX=0;entryY=0.5;")
edge("e2", "cb", "raw", extra="entryX=0;entryY=0.5;"); edge("e3", "cc", "raw", extra="entryX=0;entryY=0.5;")
edge("e4", "raw", "glue", "2. Crawl")
edge("e5", "glue", "lambda", "start gate")
edge("e6", "lambda", "choice", "3. Scan")
edge("e7", "choice", "cur", "5a. NO – clean → promote")
edge("e8", "choice", "quar", "5b. YES – quarantine")
edge("e9", "quar", "sns", "notify")
edge("e10", "sns", "secteam", "email")
edge("e11", "cur", "lf", "6. Catalog")
edge("e12", "lf", "athena", "filtered")
edge("e13", "athena", "u1", "7. Results", extra="entryX=0;entryY=0.5;"); edge("e14", "athena", "u2", extra="entryX=0;entryY=0.5;")
edge("k1", "kms", "raw", "encrypts", dashed=True, extra="exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
edge("k2", "kms", "cur", "encrypts", dashed=True, extra="exitX=1;exitY=0.5;entryX=0.5;entryY=0;")
edge("a1", "trail", "trails3", "log files")
edge("a2", "trails3", "athena2", "query")
edge("a3", "athena2", "auditq", "answers")

ET.indent(root)
ET.ElementTree(root).write("/home/claude/marrowick/repo/architecture/Marrowick_Architecture.drawio", encoding="utf-8", xml_declaration=False)
print("ok")
