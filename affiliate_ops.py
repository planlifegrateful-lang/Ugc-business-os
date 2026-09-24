#!/usr/bin/env python3
"""Local, human-reviewed affiliate content operations system.

No external publishing occurs. The system creates reviewable content packages,
records evidence and disclosures, and exports only approved assets.
"""
from __future__ import annotations
import argparse, json, os, sqlite3, textwrap, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "affiliate_ops.sqlite3"
CONFIG = ROOT / "config.json"

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def load_config():
    with CONFIG.open() as f:
        return json.load(f)

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS products (
      id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT, url TEXT,
      affiliate_url TEXT, price TEXT, verified_facts TEXT NOT NULL DEFAULT '[]',
      restrictions TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS evidence (
      id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES products(id),
      source_url TEXT NOT NULL, claim TEXT NOT NULL, source_type TEXT NOT NULL,
      verified INTEGER NOT NULL DEFAULT 0, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS content (
      id TEXT PRIMARY KEY, product_id TEXT REFERENCES products(id), channel TEXT NOT NULL,
      angle TEXT NOT NULL, title TEXT NOT NULL, hook TEXT NOT NULL, script TEXT NOT NULL,
      caption TEXT NOT NULL, cta TEXT NOT NULL, disclosure TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'draft', risk_flags TEXT NOT NULL DEFAULT '[]',
      evidence_ids TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS approvals (
      id TEXT PRIMARY KEY, content_id TEXT NOT NULL REFERENCES content(id),
      reviewer TEXT NOT NULL, decision TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS runs (
      id TEXT PRIMARY KEY, command TEXT NOT NULL, status TEXT NOT NULL,
      summary TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
    );
    """)
    conn.commit(); conn.close()

def rid(prefix): return f"{prefix}_{uuid.uuid4().hex[:10]}"
def json_text(v): return json.dumps(v, ensure_ascii=False)

def log_run(command, status, summary):
    conn=db(); conn.execute("INSERT INTO runs VALUES (?,?,?,?,?)", (rid("run"),command,status,summary,now())); conn.commit(); conn.close()

def add_product(args):
    conn=db(); pid=rid("prod")
    conn.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)", (pid,args.name,args.category,args.url,args.affiliate_url,args.price,"[]",args.restrictions,args.notes,"active",now()))
    conn.commit(); conn.close(); print(f"Created product {pid}: {args.name}")

def add_evidence(args):
    conn=db(); row=conn.execute("SELECT id FROM products WHERE id=?",(args.product_id,)).fetchone()
    if not row: raise SystemExit("Product not found")
    eid=rid("ev"); conn.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)", (eid,args.product_id,args.source_url,args.claim,args.source_type,1 if args.verified else 0,args.notes,now()))
    if args.verified:
        prod=conn.execute("SELECT verified_facts FROM products WHERE id=?",(args.product_id,)).fetchone()
        facts=json.loads(prod[0]); facts.append(args.claim)
        conn.execute("UPDATE products SET verified_facts=? WHERE id=?",(json_text(facts),args.product_id))
    conn.commit(); conn.close(); print(f"Created evidence {eid}")

def risk_scan(text, product=None):
    lower=text.lower(); flags=[]
    sensitive={"health": ["cure","treat","diagnose","guaranteed weight loss","prevent disease"], "finance":["guaranteed return","risk-free","beat the market","make money fast"], "legal":["legal advice","guaranteed approval"], "religion":["scripture says","the bible guarantees"]}
    for domain, terms in sensitive.items():
        hits=[t for t in terms if t in lower]
        if hits: flags.append({"type":domain,"matches":hits,"action":"manual verification required"})
    if "affiliate" not in lower and "commission" not in lower and "disclosure" not in lower:
        flags.append({"type":"disclosure","matches":[],"action":"add affiliate disclosure"})
    if product and product["restrictions"]: flags.append({"type":"product_restriction","matches":[],"action":product["restrictions"]})
    return flags

def make_script(product, args, cfg):
    facts=json.loads(product["verified_facts"])
    facts_text="; ".join(facts) if facts else "No verified product facts supplied yet."
    disclosure=cfg["default_disclosure"]
    hook=args.hook or f"Before you buy {product['name']}, check this first."
    title=args.title or f"A practical look at {product['name']}"
    cta=args.cta or cfg["content_defaults"]["cta"]
    script=textwrap.dedent(f"""\
    HOOK: {hook}
    CONTEXT: This is an evidence-aware overview, not a personal-use claim.
    FACTS TO PRESENT: {facts_text}
    CAVEAT: Verify current pricing, availability, terms, and fit before purchase.
    CTA: {cta}
    DISCLOSURE: {disclosure}
    """).strip()
    caption=f"{title}\n\n{facts_text}\n\n{cta}\n\n{disclosure}"
    return title,hook,script,caption,cta,disclosure

def create_content(args):
    cfg=load_config(); conn=db(); product=conn.execute("SELECT * FROM products WHERE id=?",(args.product_id,)).fetchone()
    if not product: raise SystemExit("Product not found")
    title,hook,script,caption,cta,disclosure=make_script(product,args,cfg)
    full=" ".join([title,hook,script,caption]); flags=risk_scan(full,product)
    cid=rid("cnt"); conn.execute("INSERT INTO content VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (cid,product["id"],args.channel,args.angle,title,hook,script,caption,cta,disclosure,"draft",json_text(flags),"[]",now(),now()))
    conn.commit(); conn.close(); print(f"Created content {cid} with status draft and {len(flags)} risk flag(s)")

def list_items(args):
    conn=db()
    if args.kind=="products": rows=conn.execute("SELECT id,name,category,status,created_at FROM products ORDER BY created_at DESC").fetchall()
    else: rows=conn.execute("SELECT id,channel,angle,status,created_at,risk_flags FROM content ORDER BY created_at DESC").fetchall()
    for r in rows: print(dict(r))
    conn.close()

def approve(args):
    cfg=load_config(); conn=db(); c=conn.execute("SELECT * FROM content WHERE id=?",(args.content_id,)).fetchone()
    if not c: raise SystemExit("Content not found")
    flags=json.loads(c["risk_flags"])
    if args.decision=="approved" and flags and not args.override:
        raise SystemExit("Approval blocked: resolve risk flags first or use --override with an explicit reviewer note.")
    conn.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?)",(rid("appr"),args.content_id,args.reviewer,args.decision,args.notes,now()))
    conn.execute("UPDATE content SET status=?,updated_at=? WHERE id=?",(args.decision,now(),args.content_id)); conn.commit(); conn.close(); print(f"Content {args.content_id}: {args.decision}")

def export_content(args):
    cfg=load_config(); out=Path(cfg["output_dir"]); out.mkdir(parents=True,exist_ok=True); conn=db()
    rows=conn.execute("SELECT c.*,p.name product_name FROM content c LEFT JOIN products p ON p.id=c.product_id WHERE c.status='approved' ORDER BY c.updated_at DESC").fetchall()
    if args.content_id: rows=[r for r in rows if r["id"]==args.content_id]
    if not rows: raise SystemExit("No approved content available for export")
    files=[]
    for r in rows:
        safe="".join(ch if ch.isalnum() else "_" for ch in f"{r['channel']}_{r['id']}")
        path=out/f"{safe}.md"
        path.write_text(f"# {r['title']}\n\n**Product:** {r['product_name']}\n**Channel:** {r['channel']}\n**Angle:** {r['angle']}\n\n## Hook\n{r['hook']}\n\n## Script\n{r['script']}\n\n## Caption\n{r['caption']}\n\n## Disclosure\n{r['disclosure']}\n",encoding="utf-8")
        files.append(str(path))
    conn.close(); print("Exported:\n"+"\n".join(files))

def report(args):
    conn=db(); data={"products":conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],"evidence":conn.execute("SELECT COUNT(*) FROM evidence WHERE verified=1").fetchone()[0],"draft":conn.execute("SELECT COUNT(*) FROM content WHERE status='draft'").fetchone()[0],"approved":conn.execute("SELECT COUNT(*) FROM content WHERE status='approved'").fetchone()[0],"rejected":conn.execute("SELECT COUNT(*) FROM content WHERE status='rejected'").fetchone()[0]}; conn.close(); print(json.dumps(data,indent=2))

def main():
    init_db(); p=argparse.ArgumentParser(description="Human-reviewed affiliate content operations system"); sub=p.add_subparsers(dest="cmd",required=True)
    x=sub.add_parser("add-product"); x.add_argument("--name",required=True); x.add_argument("--category",default=""); x.add_argument("--url",default=""); x.add_argument("--affiliate-url",default=""); x.add_argument("--price",default=""); x.add_argument("--restrictions",default=""); x.add_argument("--notes",default=""); x.set_defaults(fn=add_product)
    x=sub.add_parser("add-evidence"); x.add_argument("--product-id",required=True); x.add_argument("--source-url",required=True); x.add_argument("--claim",required=True); x.add_argument("--source-type",default="official product page"); x.add_argument("--verified",action="store_true"); x.add_argument("--notes",default=""); x.set_defaults(fn=add_evidence)
    x=sub.add_parser("create-content"); x.add_argument("--product-id",required=True); x.add_argument("--channel",required=True); x.add_argument("--angle",required=True); x.add_argument("--title"); x.add_argument("--hook"); x.add_argument("--cta"); x.set_defaults(fn=create_content)
    x=sub.add_parser("list"); x.add_argument("kind",choices=["products","content"]); x.set_defaults(fn=list_items)
    x=sub.add_parser("approve"); x.add_argument("--content-id",required=True); x.add_argument("--reviewer",required=True); x.add_argument("--decision",choices=["approved","rejected"],required=True); x.add_argument("--notes",default=""); x.add_argument("--override",action="store_true"); x.set_defaults(fn=approve)
    x=sub.add_parser("export"); x.add_argument("--content-id"); x.set_defaults(fn=export_content)
    x=sub.add_parser("report"); x.set_defaults(fn=report)
    args=p.parse_args(); args.fn(args)

if __name__=="__main__": main()
