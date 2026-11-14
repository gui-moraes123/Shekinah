import os,sqlite3,secrets,csv,io,json
from datetime import date,datetime
from functools import wraps
from pathlib import Path
from flask import Flask,request,redirect,session,render_template_string,flash,abort,Response
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash,check_password_hash
app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"]=True
app.config["SESSION_COOKIE_SAMESITE"]="Lax"
app.config["SESSION_COOKIE_SECURE"]=os.getenv("RAILWAY_ENVIRONMENT") is not None
CSRFProtect(app)
path=os.getenv("DATABASE_PATH","shekinah.db")
os.makedirs(os.path.dirname(os.path.abspath(path)),exist_ok=True)
def db():
 c=sqlite3.connect(path);c.row_factory=sqlite3.Row;return c
with db() as c:
 c.execute("BEGIN IMMEDIATE")
 c.execute("CREATE TABLE IF NOT EXISTS inscricoes (id INTEGER PRIMARY KEY, tipo TEXT,nome TEXT,responsavel TEXT,nascimento TEXT,endereco TEXT,telefone TEXT,telefone_resp TEXT,medicamento TEXT,chegada TEXT,pagamento TEXT,status TEXT DEFAULT 'Pendente',criado TEXT)")
 if "restricao_alimentar" not in {column["name"] for column in c.execute("PRAGMA table_info(inscricoes)")}:
  c.execute("ALTER TABLE inscricoes ADD COLUMN restricao_alimentar TEXT NOT NULL DEFAULT ''")
 c.execute("CREATE TABLE IF NOT EXISTS admin (usuario TEXT PRIMARY KEY,senha TEXT)")
 if os.getenv("ADMIN_PASSWORD") and not c.execute("SELECT 1 FROM admin").fetchone():c.execute("INSERT INTO admin VALUES (?,?)",(os.getenv("ADMIN_USERNAME","coordenador"),generate_password_hash(os.getenv("ADMIN_PASSWORD"))))
BASE=(Path(__file__).parent / "templates" / "base.html").read_text()
GALLERY=json.loads((Path(__file__).parent / "data" / "gallery.json").read_text())
def page(body,**kw):
 return render_template_string(BASE.replace("{% block body %}{% endblock %}",body),**kw)
def home_page(values=None, errors=None):
 return page("{% include 'home.html' %}", values=values or {}, errors=errors or {}, gallery=GALLERY)
@app.get("/")
def home():
 return home_page()
@app.get("/retiro.ics")
def calendario():
 content="\r\n".join(["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Shekinah//Retiro 2027//PT-BR","CALSCALE:GREGORIAN","BEGIN:VEVENT","UID:shekinah-2027@retiro.local","DTSTAMP:20261113T000000Z","DTSTART;VALUE=DATE:20270115","DTEND;VALUE=DATE:20270118","SUMMARY:III Retiro de Jovens SHEKINAH","DESCRIPTION:A Glória de Deus se manifesta. Leve Bíblia e itens pessoais.","END:VEVENT","END:VCALENDAR",""])
 return Response(content,mimetype="text/calendar",headers={"Content-Disposition":"attachment; filename=shekinah-2027.ics"})
@app.post("/inscrever")
def inscrever():
 keys=["tipo","nome","responsavel","nascimento","endereco","telefone","telefone_resp","medicamento","chegada","pagamento","restricao_alimentar"]
 v={k:request.form.get(k,"").strip() for k in keys}
 errors={}
 limits={"nome":150,"responsavel":150,"endereco":250,"telefone":25,"telefone_resp":25,"restricao_alimentar":500}
 for k in keys:
  if k!="chegada" and not v[k]: errors[k]="Preencha este campo."
 for k,limit in limits.items():
  if len(v[k])>limit: errors[k]=f"Use até {limit} caracteres."
 for k in ("telefone","telefone_resp"):
  digits="".join(ch for ch in v[k] if ch.isdigit())
  if len(digits) not in (10,11,12,13): errors[k]="Informe um telefone com DDD."
 for k,options in {"tipo":("Encontrista","Trabalhador"),"medicamento":("Não faz uso","Controlado","Uso contínuo"),"pagamento":("PIX","Dinheiro")}.items():
  if v[k] not in options: errors[k]="Selecione uma opção válida."
 if v["tipo"]=="Trabalhador":
  if v["chegada"] not in ("Sexta-feira à noite","Sábado pela manhã","Sábado à tarde"): errors["chegada"]="Selecione quando chegará."
 else: v["chegada"]=""
 try:
  b=date.fromisoformat(v["nascimento"]);age=2027-b.year-((1,15)<(b.month,b.day))
  if age<11 or b>date.today() or age>120: raise ValueError()
 except ValueError: errors["nascimento"]="É necessário ter 11 anos completos em 15/01/2027. Confira a data."
 if errors: return home_page(v,errors),422
 with db() as c:
  cur=c.execute("INSERT INTO inscricoes(tipo,nome,responsavel,nascimento,endereco,telefone,telefone_resp,medicamento,chegada,pagamento,restricao_alimentar,criado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",tuple(v[k] for k in keys)+(datetime.now().isoformat(timespec="seconds"),))
  numero=cur.lastrowid
 return page("{% include 'success.html' %}",numero=numero,pagamento=v["pagamento"])

def guard(fn):
 @wraps(fn)
 def wrapped(*a,**k):
  if not session.get("admin"):return redirect("/admin/login")
  return fn(*a,**k)
 return wrapped
@app.route("/admin/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  with db() as c:r=c.execute("SELECT * FROM admin WHERE usuario=?",(request.form.get("usuario"),)).fetchone()
  if r and check_password_hash(r["senha"],request.form.get("senha","")):session.clear();session["admin"]=True;return redirect("/admin")
  flash("Acesso inválido.")
 return page("{% include 'login.html' %}")

@app.get("/admin")
@guard
def admin():
 tipo=request.args.get("tipo","Todos")
 if tipo not in ("Todos","Encontrista","Trabalhador"):tipo="Todos"
 busca=request.args.get("busca","").strip()[:100]
 status=request.args.get("status","Todos")
 if status not in ("Todos","Pendente","Confirmado"):status="Todos"
 with db() as c:
  rows=c.execute("SELECT * FROM inscricoes WHERE (?='Todos' OR tipo=?) AND (?='Todos' OR status=?) AND (nome LIKE ? OR telefone LIKE ?) ORDER BY id DESC",(tipo,tipo,status,status,"%"+busca+"%","%"+busca+"%")).fetchall()
  stats=c.execute("SELECT COUNT(*) total, SUM(CASE WHEN tipo='Encontrista' THEN 1 ELSE 0 END) encontristas, SUM(CASE WHEN tipo='Trabalhador' THEN 1 ELSE 0 END) trabalhadores, SUM(CASE WHEN status='Confirmado' THEN 1 ELSE 0 END) confirmados, SUM(CASE WHEN status='Pendente' THEN 1 ELSE 0 END) pendentes FROM inscricoes").fetchone()
 return page("""<style>
body{background:#f5f5f7;color:#25262b}header{background:#211e1c}.dashboard{max-width:1400px;margin:24px auto;padding:0 22px}.dash-header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:24px}.dash-header h2{font-size:29px;color:#222;margin:4px 0}.dash-header p{color:#777;margin:0}.dash-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.dash-actions form{margin:0}.dash-actions button,.dash-actions .btn{margin:0}.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-bottom:22px}.stat{background:#fff;padding:21px;border:1px solid #e8e7e4;border-radius:13px;box-shadow:0 5px 16px #00000008}.stat .ico{font-size:25px;margin-bottom:13px}.stat .number{font-size:32px;font-weight:800;color:#292624;line-height:1.1}.stat .name{color:#777;font-size:12px;margin-top:8px}.stat.gold{background:#fff8e8;border-color:#efd9a7}.stat.green{background:#eef9f0;border-color:#cce8d0}.stat.purple{background:#f4efff;border-color:#e1d5fa}.stat.red{background:#fff3ef;border-color:#f5d6ca}.panel{background:#fff;border:1px solid #e9e7e3;border-radius:14px;overflow:hidden;box-shadow:0 7px 20px #0000000a}.panel-title{padding:23px 25px;border-bottom:1px solid #eceae6}.panel-title h3{font-size:19px;margin:0 0 5px}.panel-title p{font-size:12px;color:#777;margin:0}.filters{padding:18px 24px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}.filters input{max-width:300px;flex:1 1 220px}.filters select{max-width:175px;flex:1 1 140px}.filters button{margin:0}.tabs{display:flex;gap:8px;flex-wrap:wrap;padding:0 24px 18px}.tabs a{padding:10px 15px;text-decoration:none;border-radius:8px;background:#f2f1ef;color:#555;font-size:12px;font-weight:700}.tabs a.active{background:#eac05e;color:#241b10}.tablewrap{overflow-x:auto}.dash-table{min-width:800px;width:100%;border-collapse:collapse}.dash-table th{background:#f7f7f8;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#666}.dash-table td{font-size:12px;vertical-align:middle;padding:14px 12px;border-bottom:1px solid #efefef}.dash-table tr:hover td{background:#fcfbf8}.person{font-weight:700;font-size:13px}.sub{font-size:11px;color:#777;margin-top:5px}.chip{display:inline-block;padding:5px 9px;border-radius:20px;font-size:10px;font-weight:700}.chip.enc{background:#e5f5e8;color:#26743d}.chip.work{background:#f0e8ff;color:#7140a3}.chip.ok{background:#dff4e4;color:#21743a}.chip.wait{background:#fff0d1;color:#996013}.pay-form{display:flex;align-items:center;gap:6px}.pay-form select{min-width:115px;padding:8px;font-size:11px}.pay-form button{padding:9px 11px;font-size:10px;margin:0}.details{margin-top:8px}.details summary{cursor:pointer;color:#9b6b21;font-weight:700;font-size:11px}.details p{margin:5px 0;font-size:11px;color:#5c5c5c;overflow-wrap:anywhere}.empty{padding:45px;text-align:center;color:#777}@media(max-width:1000px){.stats{grid-template-columns:repeat(3,1fr)}}@media(max-width:760px){.tablewrap{overflow:visible}.dash-table{min-width:0}.dash-table thead{display:none}.dash-table tbody{display:grid;gap:12px;padding:12px}.dash-table tr{display:block;border:1px solid #e8e4df;border-radius:12px;padding:12px;background:#fff}.dash-table td{display:block;padding:7px 3px;border:0}.dash-table td:first-child{border-bottom:1px solid #eee;padding-bottom:12px}.dash-table td:nth-child(4){display:none}.dash-table td:nth-child(6){border-top:1px solid #eee;padding-top:12px}.pay-form select{flex:1}.filters input,.filters select{max-width:none}}@media(max-width:620px){.dashboard{padding:0 12px;margin:16px auto}.stats{grid-template-columns:repeat(2,1fr);gap:9px}.stat{padding:15px}.stat .number{font-size:27px}.dash-header h2{font-size:24px}.filters{padding:14px}.tabs{padding:0 14px 15px}.panel-title{padding:18px}}
</style><div class="dashboard"><div class="dash-header"><div><div style="color:#a7782e;font-weight:800;font-size:12px;letter-spacing:2px">SHEKINAH 2027 • COORDENAÇÃO</div><h2>Painel do Retiro</h2><p>Gerencie inscrições, equipes e pagamentos em um só lugar.</p></div><div class="dash-actions"><a class="btn" href="/admin/exportar">↓ Exportar planilha (CSV)</a><form action="/admin/sair" method="post"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><button class="secondary">Sair</button></form></div></div><div class="stats"><div class="stat gold"><div class="ico">👥</div><div class="number">{{stats["total"] or 0}}</div><div class="name">Total de inscritos</div></div><div class="stat green"><div class="ico">✦</div><div class="number">{{stats["encontristas"] or 0}}</div><div class="name">Encontristas</div></div><div class="stat purple"><div class="ico">⚙</div><div class="number">{{stats["trabalhadores"] or 0}}</div><div class="name">Equipe de trabalho</div></div><div class="stat green"><div class="ico">✓</div><div class="number">{{stats["confirmados"] or 0}}</div><div class="name">Pagamentos confirmados</div></div><div class="stat red"><div class="ico">◷</div><div class="number">{{stats["pendentes"] or 0}}</div><div class="name">Pagamentos pendentes</div></div></div><div class="panel"><div class="panel-title"><h3>Inscrições recebidas</h3><p>Consulte os dados dos participantes e atualize os pagamentos.</p></div><div class="filters"><form method="get" action="/admin" style="display:contents"><input name="busca" placeholder="Pesquisar nome ou telefone..." value="{{busca}}"><input type="hidden" name="tipo" value="{{tipo}}"><select name="status"><option value="Todos" {% if status=="Todos" %}selected{% endif %}>Todos os pagamentos</option><option value="Pendente" {% if status=="Pendente" %}selected{% endif %}>Pendentes</option><option value="Confirmado" {% if status=="Confirmado" %}selected{% endif %}>Confirmados</option></select><button>Buscar</button></form></div><div class="tabs"><a href="{{url_for('admin',tipo='Todos',status=status,busca=busca)}}" class="{{'active' if tipo=='Todos' else ''}}">Todas</a><a href="{{url_for('admin',tipo='Encontrista',status=status,busca=busca)}}" class="{{'active' if tipo=='Encontrista' else ''}}">Encontristas</a><a href="{{url_for('admin',tipo='Trabalhador',status=status,busca=busca)}}" class="{{'active' if tipo=='Trabalhador' else ''}}">Equipe de trabalho</a></div><div class="tablewrap"><table class="dash-table"><thead><tr><th>Participante</th><th>Categoria</th><th>Contato</th><th>Informações</th><th>Pagamento</th><th>Atualizar</th></tr></thead><tbody>{% for r in rows %}<tr><td><a class="person" href="/admin/inscricao/{{r['id']}}" style="color:#8c611e;text-decoration:underline">{{r["nome"]}}</a><div class="sub">Inscrição #{{r["id"]}} • {{r["criado"][:10]}}</div></td><td><span class="chip {{'enc' if r['tipo']=='Encontrista' else 'work'}}">{{r["tipo"]}}</span></td><td><div>{{r["telefone"]}}</div><div class="sub">Resp.: {{r["responsavel"]}}</div></td><td><details class="details"><summary>Ver ficha completa</summary><p><b>Nascimento:</b> {{r["nascimento"]}}</p><p><b>Endereço:</b> {{r["endereco"]}}</p><p><b>Telefone responsável:</b> {{r["telefone_resp"]}}</p><p><b>Medicamento:</b> {{r["medicamento"]}}</p><p><b>Restrição alimentar:</b> {{r["restricao_alimentar"] or "Não informado"}}</p><p><b>Chegada:</b> {{r["chegada"] or '—'}}</p></details></td><td><span class="chip {{'ok' if r['status']=='Confirmado' else 'wait'}}">{{r["status"]}}</span><div class="sub">{{r["pagamento"]}}</div></td><td><form class="pay-form" method="post" action="/admin/pagamento/{{r['id']}}"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><select name="status"><option {% if r["status"]=="Pendente" %}selected{% endif %}>Pendente</option><option {% if r["status"]=="Confirmado" %}selected{% endif %}>Confirmado</option></select><button>Salvar</button></form><a class="delete-link" href="{{url_for('excluir_inscricao',numero=r['id'])}}">Excluir inscrição</a></td></tr>{% else %}<tr><td colspan="6" class="empty">Nenhuma inscrição encontrada para esses filtros.</td></tr>{% endfor %}</tbody></table></div></div></div>""",rows=rows,stats=stats,tipo=tipo,status=status,busca=busca)
@app.get("/admin/inscricao/<int:numero>")
@guard
def ficha(numero):
 with db() as c:
  r=c.execute("SELECT * FROM inscricoes WHERE id=?",(numero,)).fetchone()
 if not r:abort(404)
 return page("""<style>body{background:#f5f5f7;color:#292724}.ficha{max-width:800px;margin:24px auto;padding:0 16px}.sheet{background:white;border-radius:16px;overflow:hidden;box-shadow:0 8px 30px #0001}.sheet-head{background:#29231e;color:white;padding:24px}.sheet-head h2{color:#eac16d;margin:8px 0}.sheet-body{padding:22px}.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.field{background:#f7f6f4;padding:14px;border-radius:9px;overflow-wrap:anywhere}.field small{display:block;color:#777;margin-bottom:5px}.section-label{font-size:13px;font-weight:800;color:#976922;margin:25px 0 12px;text-transform:uppercase}.payment{background:#fff5df;padding:18px;border-radius:12px;margin-top:20px}.payment form{display:flex;gap:10px;flex-wrap:wrap;align-items:end}.payment select{max-width:220px}.payment button{margin:0}@media(max-width:600px){.fields{grid-template-columns:1fr}.sheet-body{padding:14px}.ficha{margin:12px auto}}</style><div class="ficha"><p class="sheet-actions"><a href="/admin">← Voltar ao painel</a><a class="delete-link" href="{{url_for('excluir_inscricao',numero=r['id'])}}">Excluir inscrição</a></p><div class="sheet"><div class="sheet-head"><small>SHEKINAH 2027 • FICHA DE INSCRIÇÃO</small><h2>{{r["nome"]}}</h2><p>#{{r["id"]}} • {{r["tipo"]}}</p></div><div class="sheet-body"><div class="section-label">Dados do participante</div><div class="fields"><div class="field"><small>Nome completo</small><b>{{r["nome"]}}</b></div><div class="field"><small>Data de nascimento</small><b>{{r["nascimento"]}}</b></div><div class="field"><small>Telefone</small><b>{{r["telefone"]}}</b></div><div class="field"><small>Categoria</small><b>{{r["tipo"]}}</b></div><div class="field"><small>Endereço</small><b>{{r["endereco"]}}</b></div></div><div class="section-label">Responsável</div><div class="fields"><div class="field"><small>Nome</small><b>{{r["responsavel"]}}</b></div><div class="field"><small>Telefone</small><b>{{r["telefone_resp"]}}</b></div></div><div class="section-label">Informações adicionais</div><div class="fields"><div class="field"><small>Medicamento</small><b>{{r["medicamento"]}}</b></div><div class="field"><small>Restrição alimentar</small><b style="white-space:pre-wrap">{{r["restricao_alimentar"] or "Não informado"}}</b></div><div class="field"><small>Chegada</small><b>{{r["chegada"] or "Não se aplica"}}</b></div></div><div class="payment"><b>Pagamento: R$ 70,00 • {{r["pagamento"]}}</b><p>Situação: {{r["status"]}}</p><form method="post" action="/admin/pagamento/{{r['id']}}"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><div><label>Atualizar pagamento</label><select name="status"><option {% if r["status"]=="Pendente" %}selected{% endif %}>Pendente</option><option {% if r["status"]=="Confirmado" %}selected{% endif %}>Confirmado</option></select></div><button>Salvar</button></form></div></div></div></div>""",r=r)
@app.route("/admin/inscricao/<int:numero>/excluir",methods=["GET","POST"])
@guard
def excluir_inscricao(numero):
 with db() as c:
  r=c.execute("SELECT * FROM inscricoes WHERE id=?",(numero,)).fetchone()
  if not r:abort(404)
  if request.method=="POST":
   if request.form.get("confirmacao")!="excluir":abort(400)
   c.execute("DELETE FROM inscricoes WHERE id=?",(numero,))
 if request.method=="POST":
  flash(f"Inscrição #{numero} excluída com sucesso.")
  return redirect("/admin",code=303)
 return page("{% include 'delete_registration.html' %}",r=r)

@app.post("/admin/pagamento/<int:numero>")
@guard
def pagamento(numero):
 s=request.form.get("status")
 if s not in ("Pendente","Confirmado"):abort(400)
 with db() as c:
  result=c.execute("UPDATE inscricoes SET status=? WHERE id=?",(s,numero))
  if not result.rowcount: abort(404)
 flash("Situação do pagamento atualizada.")
 return redirect("/admin")
@app.get("/admin/exportar")
@guard
def exportar():
 with db() as c:rows=c.execute("SELECT * FROM inscricoes ORDER BY id").fetchall()
 out=io.StringIO();w=csv.writer(out,delimiter=";")
 w.writerow(rows[0].keys() if rows else ["id","tipo","nome"])
 for r in rows:w.writerow(["'"+str(v) if isinstance(v,str) and v.startswith(("=","+","-","@")) else v for v in r])
 return Response("\ufeff"+out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=inscricoes.csv","Cache-Control":"no-store"})
@app.post("/admin/sair")
@guard
def sair():session.clear();return redirect("/")
@app.after_request
def headers(r):
 r.headers["X-Content-Type-Options"]="nosniff"
 if request.path.startswith("/admin"):r.headers["Cache-Control"]="no-store"
 return r
@app.errorhandler(400)
def bad_request(error):
 return page('<main class="narrow"><section><h1>Não foi possível enviar</h1><p>Atualize a página e tente novamente. Sua sessão pode ter expirado.</p><a class="btn" href="/">Voltar ao início</a></section></main>'),400
@app.errorhandler(404)
def not_found(error):
 return page('<main class="narrow"><section><h1>Página não encontrada</h1><p>Este endereço não está disponível.</p><a class="btn" href="/">Voltar ao início</a></section></main>'),404
if __name__=="__main__":app.run()
