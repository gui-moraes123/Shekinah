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
BASE='''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SHEKINAH 2027</title><style>@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=DM+Sans:wght@400;600;700&display=swap');*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#0b1916;color:#f8f1e5;font:16px 'DM Sans',Arial;line-height:1.6}header{display:flex;justify-content:space-between;align-items:center;max-width:1100px;margin:auto;padding:22px}header b{font-family:Cinzel,serif;font-size:14px}header small{font-size:10px;letter-spacing:2px;color:#d9b86c}header a{font-size:12px;text-transform:uppercase;letter-spacing:1px}main,footer{max-width:1100px;margin:auto;padding:26px}footer{text-align:center;color:#b7c4bb;border-top:1px solid #ffffff20}a{color:#eac47b}h1,h2,h3{font-family:Cinzel,Georgia,serif}h1{font-size:clamp(52px,11vw,120px);letter-spacing:4px;margin:10px 0;color:#f0cb83;text-shadow:0 6px 24px #000}h2{color:#e9c27c;font-size:clamp(24px,3vw,36px)}section,.card{background:linear-gradient(140deg,#1c3b32,#142a24);padding:clamp(22px,4vw,40px);border:1px solid #d9b66b50;border-radius:8px;margin:24px 0;box-shadow:0 15px 40px #0003}label{display:block;margin:17px 0 7px;font-size:13px;font-weight:700}input,select,textarea{width:100%;padding:15px;border-radius:5px;border:1px solid #7a8b80;background:#faf5ec;color:#17231e;font:16px 'DM Sans',sans-serif}input:focus,select:focus{outline:2px solid #edc679}button,.btn{display:inline-block;background:#e8bd6d;color:#1a281e;border:1px solid #e8bd6d;border-radius:4px;padding:14px 23px;font-weight:700;letter-spacing:1px;text-transform:uppercase;text-decoration:none;cursor:pointer;margin:8px 6px 8px 0}button:hover,.btn:hover{background:#ffdc96;color:#18231e}.secondary{background:transparent;color:#e8bd6d}small{color:#b8c8bc}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #496054;text-align:left}.scroll{overflow-x:auto}.hero{min-height:570px;display:flex;align-items:center;justify-content:center;text-align:center;padding:80px 20px;background:linear-gradient(90deg,#091711e8,#0b2114a8,#091711e8),linear-gradient(0deg,#0b1916,transparent 60%),url('https://images.unsplash.com/photo-1519491050282-cf00c82424b4?auto=format&fit=crop&w=1800&q=85') center/cover}.hero p{margin:15px}.hero .theme{font:italic clamp(21px,3vw,30px) Georgia,serif;color:#f5e5c9}.eyebrow{color:#e8c17a;letter-spacing:3px;text-transform:uppercase;font-size:12px;font-weight:700}.info-bar{background:#e6c17c;color:#183328;text-align:center;padding:20px;font-size:13px;font-weight:700;letter-spacing:1px}.info-bar span{display:inline-block;margin:5px 18px}.intro{text-align:center;margin:55px auto 25px;max-width:700px}.intro p{color:#b9c7bb}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px}.grid .card{margin:0;text-align:center}.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px}.feature{padding:25px 18px;text-align:center;background:#173129;border:1px solid #d5b57250;border-radius:6px}.feature strong{display:block;color:#e7c27b;font-family:Cinzel,serif}.feature .symbol{font-size:30px}.registration{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(260px,1fr);gap:22px;align-items:start}.registration section{margin:0}.aside{padding:28px;border:1px solid #d9b66b55;background:linear-gradient(135deg,#2d4b3d,#193329);border-radius:8px}.aside li{margin:12px 0}.msg{padding:14px;background:#6b4d25;border-radius:6px}@media(max-width:750px){.registration{grid-template-columns:1fr}.hero{min-height:490px}header{padding:15px}header b{font-size:11px}.info-bar span{margin:4px 8px}main{padding:18px}}</style><header><b>✝ NOSSA SENHORA APARECIDA<br><small>Jardim Imperial</small></b><a href="/admin/login">Coordenação</a></header>{% with msgs=get_flashed_messages() %}{% for m in msgs %}<main class="msg">{{m}}</main>{% endfor %}{% endwith %}{% block body %}{% endblock %}<footer>III Retiro de Jovens • SHEKINAH 2027</footer></html>'''
def page(body,**kw):return render_template_string(BASE.replace("{% block body %}{% endblock %}",body),**kw)
@app.get("/")
def home():
 return page('''<div class="hero"><div><div class="eyebrow">Paróquia Nossa Senhora Aparecida • Jardim Imperial</div><p class="eyebrow">III Retiro de Jovens</p><h1>SHEKINAH</h1><p class="theme">“A Glória de Deus se manifesta”</p><p>15, 16 e 17 de janeiro de 2027</p><a class="btn" href="#inscricao">Quero me inscrever →</a></div></div><div class="info-bar"><span>✦ 15–17 JANEIRO 2027</span><span>✦ R$ 70,00</span><span>✦ A PARTIR DE 11 ANOS</span></div><main><div class="intro"><div class="eyebrow">Uma experiência de fé</div><h2>Um encontro que transforma</h2><p>Três dias de oração, amizade, formação e partilha. Venha viver a presença de Deus.</p></div><div class="features"><div class="feature"><div class="symbol">✝</div><strong>Encontro com Deus</strong><p>Renove sua fé.</p></div><div class="feature"><div class="symbol">♡</div><strong>Comunhão</strong><p>Partilhe em comunidade.</p></div><div class="feature"><div class="symbol">✦</div><strong>Formação</strong><p>Cresça na caminhada.</p></div><div class="feature"><div class="symbol">☀</div><strong>Amizade</strong><p>Laços para a vida.</p></div></div><div class="registration"><section id="inscricao"><div class="eyebrow">Inscrições abertas</div><h2>Faça parte do SHEKINAH</h2><p>Preencha sua ficha para participar ou trabalhar no retiro.</p><form method="post" action="/inscrever"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Você participará como *</label><select name="tipo" id="tipo" onchange="document.getElementById('chegada').hidden=this.value!=='Trabalhador'" required><option value="Encontrista">Encontrista</option><option value="Trabalhador">Equipe de trabalho</option></select><label>Nome completo *</label><input name="nome" required maxlength="150"><label>Nome do responsável *</label><input name="responsavel" required maxlength="150"><label>Data de nascimento *</label><input type="date" name="nascimento" required><label>Endereço *</label><input name="endereco" required maxlength="250"><label>Telefone do participante *</label><input type="tel" name="telefone" required maxlength="25"><label>Telefone do responsável *</label><input type="tel" name="telefone_resp" required maxlength="25"><label>Faz uso de algum medicamento? *</label><select name="medicamento" required><option>Não faz uso</option><option>Controlado</option><option>Uso contínuo</option></select><div id="chegada" hidden><label>Quando chegará ao retiro? *</label><select name="chegada"><option value="">Selecione</option><option>Sexta-feira à noite</option><option>Sábado pela manhã</option><option>Sábado à tarde</option></select></div><label>Forma de pagamento *</label><select name="pagamento" required><option>PIX</option><option>Dinheiro</option></select><p>PIX: <b>11 97342-5262</b><br>Daniela F N Rodrigues</p><button type="button" class="secondary" onclick="navigator.clipboard.writeText('11973425262').then(()=>alert('Chave copiada!'))">Copiar chave PIX</button><p><small>Pagamento até 29/12/2026. A inscrição ficará pendente até confirmação da coordenação. Seus dados serão acessados apenas pela equipe autorizada.</small></p><button>Finalizar inscrição</button></form></section><aside class="aside"><div class="eyebrow">Informações do retiro</div><h2>Prepare seu coração</h2><p>15, 16 e 17 de janeiro de 2027</p><h2>R$ 70,00</h2><p>Encontristas e trabalhadores</p><hr><h3>O que levar?</h3><ul><li>📖 Bíblia</li><li>🛏️ Colchonete</li><li>Roupa de cama</li><li>Itens de higiene pessoal</li></ul><p><b>Pagamento até 29/12/2026</b></p><a class="btn secondary" href="https://wa.me/5511998654722?text=Ol%C3%A1%2C%20Jo%C3%A3o%21%20Gostaria%20de%20mais%20informa%C3%A7%C3%B5es%20sobre%20o%20III%20Retiro%20SHEKINAH%202027.">Dúvidas? Fale com João ↗</a></aside></div></main>''')
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
