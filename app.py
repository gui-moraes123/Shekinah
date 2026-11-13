import os,sqlite3,secrets,csv,io
from datetime import date,datetime
from functools import wraps
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
 c.execute("CREATE TABLE IF NOT EXISTS inscricoes (id INTEGER PRIMARY KEY, tipo TEXT,nome TEXT,responsavel TEXT,nascimento TEXT,endereco TEXT,telefone TEXT,telefone_resp TEXT,medicamento TEXT,chegada TEXT,pagamento TEXT,status TEXT DEFAULT 'Pendente',criado TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS admin (usuario TEXT PRIMARY KEY,senha TEXT)")
 if os.getenv("ADMIN_PASSWORD") and not c.execute("SELECT 1 FROM admin").fetchone():c.execute("INSERT INTO admin VALUES (?,?)",(os.getenv("ADMIN_USERNAME","coordenador"),generate_password_hash(os.getenv("ADMIN_PASSWORD"))))
BASE='''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SHEKINAH 2027</title><style>body{margin:0;background:#0e1424;color:#fff;font:16px Arial,sans-serif}header,main,footer{max-width:950px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:center}a{color:#f5ca6a}h1{font-size:clamp(48px,9vw,92px);margin:10px 0;color:#f3c66a}h2{color:#f3c66a}section,.card{background:#1b263c;padding:24px;border-radius:18px;margin:20px 0}label{display:block;margin:14px 0 6px}input,select,textarea{box-sizing:border-box;width:100%;padding:13px;border-radius:9px;border:1px solid #66738a;background:#fff;color:#151515;font-size:16px}button,.btn{display:inline-block;background:#e9b950;color:#181818;border:0;border-radius:10px;padding:14px 20px;font-weight:bold;cursor:pointer;text-decoration:none;margin:8px 4px 8px 0}.secondary{background:#fff}small{color:#c8d0df}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #4c586d;text-align:left} .scroll{overflow-x:auto}.hero{text-align:center;padding:70px 15px;background:radial-gradient(circle at top,#604b30,#0e1424 70%)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.grid .card{margin:0}.msg{padding:12px;background:#654d26;border-radius:10px}</style><header><b>✝ NOSSA SENHORA APARECIDA<br><small>Jardim Imperial</small></b><a href="/admin/login">Coordenação</a></header>{% with msgs=get_flashed_messages() %}{% for m in msgs %}<main class="msg">{{m}}</main>{% endfor %}{% endwith %}{% block body %}{% endblock %}<footer>III Retiro de Jovens • SHEKINAH 2027</footer></html>'''
def page(body,**kw):return render_template_string(BASE.replace("{% block body %}{% endblock %}",body),**kw)
@app.get("/")
def home():
 return page('''<div class="hero"><p>III RETIRO DE JOVENS</p><h1>SHEKINAH</h1><h2>“A Glória de Deus se manifesta”</h2><p>15, 16 e 17 de janeiro de 2027</p><p>Paróquia Nossa Senhora Aparecida — Jardim Imperial</p><a class="btn" href="#inscricao">FAZER INSCRIÇÃO</a></div><main><div class="grid"><div class="card"><h2>R$ 70,00</h2>Encontristas e trabalhadores</div><div class="card"><h2>11 anos</h2>Idade mínima</div><div class="card"><h2>29/12/2026</h2>Prazo do pagamento</div></div><section><h2>O que levar?</h2><p>📖 Bíblia • 🛏️ Colchonete • Roupa de cama • Itens de higiene pessoal</p><a class="btn secondary" href="https://wa.me/5511998654722?text=Ol%C3%A1%2C%20Jo%C3%A3o%21%20Gostaria%20de%20mais%20informa%C3%A7%C3%B5es%20sobre%20o%20III%20Retiro%20SHEKINAH%202027.">Deseja mais informações? Fale com João</a></section><section id="inscricao"><h2>Faça sua inscrição</h2><form method="post" action="/inscrever"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Você participará como *</label><select name="tipo" id="tipo" onchange="document.getElementById('chegada').hidden=this.value!=='Trabalhador'" required><option value="Encontrista">Encontrista</option><option value="Trabalhador">Equipe de trabalho</option></select><label>Nome completo *</label><input name="nome" required maxlength="150"><label>Nome do responsável *</label><input name="responsavel" required maxlength="150"><label>Data de nascimento *</label><input type="date" name="nascimento" required><label>Endereço *</label><input name="endereco" required maxlength="250"><label>Telefone do participante *</label><input type="tel" name="telefone" required maxlength="25"><label>Telefone do responsável *</label><input type="tel" name="telefone_resp" required maxlength="25"><label>Faz uso de algum medicamento? *</label><select name="medicamento" required><option>Não faz uso</option><option>Controlado</option><option>Uso contínuo</option></select><div id="chegada" hidden><label>Quando chegará ao retiro? *</label><select name="chegada"><option value="">Selecione</option><option>Sexta-feira à noite</option><option>Sábado pela manhã</option><option>Sábado à tarde</option></select></div><label>Forma de pagamento *</label><select name="pagamento" required><option>PIX</option><option>Dinheiro</option></select><p>PIX: <b>11 97342-5262</b><br>Daniela F N Rodrigues</p><button type="button" class="secondary" onclick="navigator.clipboard.writeText('11973425262').then(()=>alert('Chave copiada!'))">Copiar chave PIX</button><p><small>Pagamento até 29/12/2026. A inscrição ficará pendente até confirmação da coordenação. Seus dados serão acessados apenas pela equipe autorizada.</small></p><button>Finalizar inscrição</button></form></section></main>''')
@app.post("/inscrever")
def inscrever():
 keys=["tipo","nome","responsavel","nascimento","endereco","telefone","telefone_resp","medicamento","chegada","pagamento"]
 v={k:request.form.get(k,"").strip() for k in keys}
 if any(not v[k] for k in keys if k!="chegada"):flash("Preencha todos os campos.");return redirect("/#inscricao")
 if v["tipo"] not in ("Encontrista","Trabalhador") or v["medicamento"] not in ("Não faz uso","Controlado","Uso contínuo") or v["pagamento"] not in ("PIX","Dinheiro"):abort(400)
 if v["tipo"]=="Trabalhador" and v["chegada"] not in ("Sexta-feira à noite","Sábado pela manhã","Sábado à tarde"):flash("Selecione a chegada.");return redirect("/#inscricao")
 try:
  b=date.fromisoformat(v["nascimento"]);age=2027-b.year-((1,15)<(b.month,b.day))
  if age<11 or b>date.today():raise ValueError()
 except ValueError:flash("Nascimento inválido ou idade inferior a 11 anos.");return redirect("/#inscricao")
 with db() as c:
  cur=c.execute("INSERT INTO inscricoes(tipo,nome,responsavel,nascimento,endereco,telefone,telefone_resp,medicamento,chegada,pagamento,criado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",tuple(v[k] for k in keys)+(datetime.now().isoformat(timespec="seconds"),))
  numero=cur.lastrowid
 return page('<main><section><h2>Inscrição recebida!</h2><p>Protocolo #{{numero}}. Pagamento pendente de confirmação.</p><p>Valor R$ 70,00 • PIX 11 97342-5262 — Daniela F N Rodrigues</p><a class="btn" href="/">Voltar</a></section></main>',numero=numero)
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
 return page('<main><section><h2>Área da coordenação</h2><form method="post"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Usuário</label><input name="usuario" required><label>Senha</label><input name="senha" type="password" required><button>Entrar</button></form></section></main>')
@app.get("/admin")
@guard
def admin():
 tipo=request.args.get("tipo","Todos")
 with db() as c:
  rows=c.execute("SELECT * FROM inscricoes WHERE (?='Todos' OR tipo=?) ORDER BY id DESC",(tipo,tipo)).fetchall()
  counts=c.execute("SELECT tipo,count(*) n FROM inscricoes GROUP BY tipo").fetchall()
 return page('''<main><h2>Painel do coordenador</h2><p>{% for x in counts %}{{x["tipo"]}}: {{x["n"]}} • {% endfor %}</p><a class="btn" href="/admin?tipo=Todos">Todos</a><a class="btn" href="/admin?tipo=Encontrista">Encontristas</a><a class="btn" href="/admin?tipo=Trabalhador">Trabalhadores</a><a class="btn secondary" href="/admin/exportar">Exportar CSV</a><form action="/admin/sair" method="post"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><button>Sair</button></form><div class="scroll"><table><tr><th>Inscrição</th><th>Contato</th><th>Detalhes</th><th>Pagamento</th></tr>{% for r in rows %}<tr><td>#{{r["id"]}}<br>{{r["nome"]}}<br>{{r["tipo"]}}</td><td>{{r["telefone"]}}<br>Responsável: {{r["responsavel"]}}<br>{{r["telefone_resp"]}}</td><td>{{r["nascimento"]}}<br>{{r["endereco"]}}<br>Medicamento: {{r["medicamento"]}}<br>Chegada: {{r["chegada"]}}</td><td>{{r["pagamento"]}}<form method="post" action="/admin/pagamento/{{r['id']}}"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><select name="status"><option {% if r["status"]=="Pendente" %}selected{% endif %}>Pendente</option><option {% if r["status"]=="Confirmado" %}selected{% endif %}>Confirmado</option></select><button>Salvar</button></form></td></tr>{% endfor %}</table></div></main>''',rows=rows,counts=counts)
@app.post("/admin/pagamento/<int:numero>")
@guard
def pagamento(numero):
 s=request.form.get("status")
 if s not in ("Pendente","Confirmado"):abort(400)
 with db() as c:c.execute("UPDATE inscricoes SET status=? WHERE id=?",(s,numero))
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
if __name__=="__main__":app.run()
