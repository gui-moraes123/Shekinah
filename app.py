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
BASE='''<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SHEKINAH 2027</title><style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Cinzel+Decorative:wght@700&display=swap');*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f7f0e5;color:#251d18;font:15px Montserrat,Arial,sans-serif}header{height:62px;display:flex;justify-content:space-between;align-items:center;gap:15px;padding:9px max(20px,calc((100vw - 1250px)/2));background:#17110de8;color:#fff}header b{font-size:15px;line-height:1.25}header small{font-size:12px;font-weight:400;color:#f1e8dd}header a{color:#fff;text-decoration:none;font-size:13px}a{color:#9a651c}h1,h2,h3{margin-top:0}h2{font-size:23px}main{max-width:1300px;margin:auto;padding:20px 28px}footer{padding:25px;text-align:center;color:#725c42}section,.card{background:#fff;border-radius:13px;padding:25px;box-shadow:0 4px 15px #35211212}label{display:block;font-size:12px;font-weight:700;margin:14px 0 6px}input,select,textarea{width:100%;border:1px solid #d1c9c0;border-radius:7px;background:#fff;padding:12px;color:#26201c;font:14px Montserrat,Arial}input:focus,select:focus{outline:2px solid #d6a841}button,.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(100deg,#e4ac35,#f9d16d);border:1px solid #c99b37;color:#1e180f;border-radius:9px;padding:13px 19px;text-decoration:none;font-weight:800;cursor:pointer;margin:8px 4px 8px 0;font:700 13px Montserrat,Arial}button:hover,.btn:hover{filter:brightness(1.07)}.secondary{background:#fff;color:#3c2b19}.hero{position:relative;min-height:535px;display:flex;justify-content:center;align-items:center;text-align:center;padding:40px 20px;color:#fff;background:linear-gradient(90deg,#170b05bc,#21100475,#170b05bb),linear-gradient(0deg,#120b06aa,transparent 65%),url('https://images.unsplash.com/photo-1519491050282-cf00c82424b4?auto=format&fit=crop&w=1800&q=85') center/cover}.hero:after{content:'';position:absolute;bottom:-1px;left:0;right:0;height:22px;background:#f7f0e5;clip-path:polygon(0 65%,4% 35%,9% 75%,14% 30%,19% 60%,24% 25%,30% 65%,35% 30%,41% 60%,48% 25%,54% 70%,60% 40%,66% 65%,73% 25%,79% 70%,85% 35%,92% 65%,97% 30%,100% 60%,100% 100%,0 100%)}.hero-inner{max-width:960px;position:relative;z-index:1}.hero h1{font-family:'Cinzel Decorative',Georgia,serif;font-size:clamp(49px,9vw,112px);line-height:1.15;color:#f9cf75;letter-spacing:2px;text-shadow:0 4px 18px #000}.hero .theme{font:italic clamp(19px,2.7vw,30px) Georgia,serif;margin:5px 0 20px}.gold-strip{background:linear-gradient(90deg,transparent,#e3ae43,transparent);color:#231409;font-weight:800;font-size:clamp(16px,2.8vw,27px);padding:6px 20px;letter-spacing:2px}.hero .parish{font-weight:700;font-size:clamp(12px,1.6vw,17px);letter-spacing:1px}.hero-facts{display:flex;justify-content:center;gap:0;margin:24px auto 16px;flex-wrap:wrap}.hero-facts div{padding:5px 24px;border-right:1px solid #ddc9a0;font-weight:700;font-size:14px}.hero-facts div:last-child{border:0}.hero-facts strong{display:block;color:#f8cc6a;font-size:17px}.packing{border:1px solid #e9c16b;border-radius:8px;padding:10px 20px;margin:15px auto;max-width:680px;font-weight:700;font-size:12px}.hero .btn{font-size:17px;padding:15px 35px;border-radius:28px}.whatsapp{display:block;color:#fff;text-decoration:none;font-weight:700;font-size:13px}.feature-strip{display:flex;flex-wrap:wrap;justify-content:space-evenly;align-items:center;gap:15px;padding:21px 18px;color:#593b1d;background:#f7f0e5;font-weight:700}.feature-strip span{font-size:17px}.feature-strip i{font-size:27px;font-style:normal;vertical-align:middle;margin-right:9px}.registration{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:24px;align-items:start}.registration section{background:#2b211a;padding:10px;border-radius:15px}.registration .form-head{padding:14px 18px;color:#fff}.registration .form-head h2{margin:0 0 6px}.registration .form-head p{margin:0;font-size:13px}.registration form{background:#fff;padding:20px;border-radius:10px}.registration form p{font-size:13px}.registration form button[type=submit],.registration form button:not([type]){width:100%}.admin-preview{background:#fff;border:1px solid #ddd;border-radius:14px;overflow:hidden;box-shadow:0 4px 15px #0002}.admin-top{background:#26211f;color:#fff;padding:15px 22px;font-weight:700}.admin-layout{display:grid;grid-template-columns:160px 1fr;min-height:350px}.admin-side{background:#282522;color:#eee;padding:15px 10px;font-size:12px}.admin-side div{padding:12px 10px;border-radius:6px}.admin-side .active{background:#e8b84e;color:#251a0e;font-weight:800}.admin-content{padding:22px}.admin-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.admin-stats div{border:1px solid #e7ded4;background:#f8f6f2;padding:15px 8px;text-align:center;border-radius:8px;font-size:11px}.admin-stats strong{display:block;font-size:21px;color:#9b671c}.admin-content p{font-size:12px;color:#5e5851}.admin-content .fake-table{margin-top:20px;background:#f4f2ee;border-radius:6px;padding:12px;font-size:12px}.admin-content .fake-row{padding:10px;border-bottom:1px solid #ddd}.admin-content .fake-row:last-child{border:0}.admin-content .fake-row b{float:right;color:#8a631c}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left}.scroll{overflow-x:auto}.msg{padding:12px;background:#fff3d8;border-radius:8px}@media(max-width:820px){header{padding:10px 15px}header b{font-size:11px}header a{font-size:11px}.hero{min-height:560px}.hero-facts div{padding:7px 12px;font-size:11px}.hero-facts strong{font-size:14px}.registration{grid-template-columns:1fr}main{padding:15px}.admin-layout{grid-template-columns:120px 1fr}.admin-content{padding:12px}.admin-stats{grid-template-columns:1fr 1fr}.packing{font-size:11px}.feature-strip span{font-size:13px}}</style><header><b>✝ NOSSA SENHORA APARECIDA<br><small>Jardim Imperial</small></b><a href="/admin/login">Coordenação</a></header>{% with msgs=get_flashed_messages() %}{% for m in msgs %}<main class="msg">{{m}}</main>{% endfor %}{% endwith %}{% block body %}{% endblock %}<footer>III Retiro de Jovens • SHEKINAH 2027</footer></html>'''
def page(body,**kw):return render_template_string(BASE.replace("{% block body %}{% endblock %}",body),**kw)
@app.get("/")
def home():
 return page('''<div class="hero"><div class="hero-inner"><h1>SHEKINAH</h1><p class="theme">“A Glória de Deus se manifesta”</p><div class="gold-strip">III RETIRO DE JOVENS</div><p class="parish">PARÓQUIA NOSSA SENHORA APARECIDA — JARDIM IMPERIAL</p><div class="hero-facts"><div>📅 DIAS 15, 16 E 17<strong>JANEIRO DE 2027</strong></div><div>🏷 VALOR DA FICHA<strong>R$ 70,00</strong></div><div>♧ IDADE MÍNIMA<strong>11 ANOS</strong></div></div><div class="packing">▣ LEVAR BÍBLIA, COLCHONETE, ROUPA DE CAMA E ITENS DE HIGIENE PESSOAL.</div><a class="btn" href="#inscricao">✎ FAÇA SUA INSCRIÇÃO ❯</a><a class="whatsapp" href="https://wa.me/5511998654722?text=Ol%C3%A1%2C%20Jo%C3%A3o%21%20Gostaria%20de%20mais%20informa%C3%A7%C3%B5es%20sobre%20o%20III%20Retiro%20SHEKINAH%202027.">☏ Deseja mais informações? WhatsApp (11) 99865-4722 — João</a></div></div><div class="feature-strip"><span><i>✧</i> Encontro com Deus</span><span><i>♧</i> Comunhão</span><span><i>♨</i> Formação</span><span><i>♡</i> Amizade</span></div><main><div class="registration"><section id="inscricao"><div class="form-head"><h2>▤ Inscrição no Retiro</h2><p>Preencha seus dados para garantir sua vaga.</p></div><form method="post" action="/inscrever"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Você participará como *</label><select name="tipo" id="tipo" onchange="document.getElementById('chegada').hidden=this.value!=='Trabalhador'" required><option value="Encontrista">Encontrista</option><option value="Trabalhador">Equipe de trabalho</option></select><label>Nome completo *</label><input name="nome" required maxlength="150"><label>Nome do responsável *</label><input name="responsavel" required maxlength="150"><label>Data de nascimento *</label><input type="date" name="nascimento" required><label>Endereço *</label><input name="endereco" required maxlength="250"><label>Telefone do participante *</label><input type="tel" name="telefone" required maxlength="25"><label>Telefone do responsável *</label><input type="tel" name="telefone_resp" required maxlength="25"><label>Faz uso de algum medicamento? *</label><select name="medicamento" required><option>Não faz uso</option><option>Controlado</option><option>Uso contínuo</option></select><div id="chegada" hidden><label>Quando chegará ao retiro? *</label><select name="chegada"><option value="">Selecione</option><option>Sexta-feira à noite</option><option>Sábado pela manhã</option><option>Sábado à tarde</option></select></div><label>Forma de pagamento *</label><select name="pagamento" required><option>PIX</option><option>Dinheiro</option></select><p>PIX: <b>11 97342-5262</b><br>Daniela F N Rodrigues</p><button type="button" class="secondary" onclick="navigator.clipboard.writeText('11973425262').then(()=>alert('Chave copiada!'))">Copiar chave PIX</button><p><small>Pagamento até 29/12/2026. A inscrição ficará pendente até confirmação da coordenação. Seus dados serão acessados apenas pela equipe autorizada.</small></p><button>Finalizar inscrição</button></form></section><div class="admin-preview"><div class="admin-top">♙ Área do Coordenador <small style="font-weight:400">— Gestão do Retiro de Jovens</small></div><div class="admin-layout"><div class="admin-side"><div class="active">⌂ Painel</div><div>▤ Inscrições</div><div>♧ Encontristas</div><div>⚙ Equipe de Trabalho</div><div>▥ Relatórios</div><div>⇩ Exportar CSV</div><div>⚙ Configurações</div></div><div class="admin-content"><h2 style="color:#29231d;font:700 20px Montserrat">Painel do Retiro</h2><div class="admin-stats"><div>Inscrições<strong>✓</strong></div><div>Encontristas<strong>♧</strong></div><div>Trabalhadores<strong>⚙</strong></div></div><div class="fake-table"><b>Organização do retiro</b><div class="fake-row">Inscrições por categoria <b>✓</b></div><div class="fake-row">Controle de pagamentos <b>✓</b></div><div class="fake-row">Dados e contatos <b>✓</b></div><div class="fake-row">Exportação para Excel <b>✓</b></div></div><p>Os números reais ficam disponíveis após entrar no painel.</p><a class="btn" href="/admin/login">Entrar no painel do coordenador</a></div></div></div></div></main>''')
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
