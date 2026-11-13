# SHEKINAH 2027

Site de inscrições do III Retiro de Jovens da Paróquia Nossa Senhora Aparecida — Jardim Imperial.

## Executar localmente

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="uma-chave-longa-e-aleatoria"
export ADMIN_USERNAME="coordenador"
export ADMIN_PASSWORD="defina-uma-senha-forte"
flask --app app run --port 5000
```

Acesse `http://localhost:5000` e `/admin/login` para a coordenação. O administrador é criado na primeira inicialização com `ADMIN_PASSWORD` configurada. Alterar a variável depois não troca uma senha já cadastrada.

## Funcionalidades

- Página responsiva com identidade em preto e dourado, abertura de adoração e ícones locais, sem depender de fontes ou imagens externas.
- Inscrição em três etapas com validação também no servidor e preservação dos dados após erros. Sem JavaScript, o formulário completo continua disponível.
- Checklist de bagagem salvo no navegador quando `localStorage` está disponível.
- Download de calendário `.ics`, contato por WhatsApp e cópia de PIX com alternativa manual.
- Protocolo de inscrição imprimível.
- Coordenação com login, filtros combináveis, fichas, confirmação manual de pagamentos e exportação CSV.

Conteúdo e formulários públicos estão em `templates/`; estilos em `static/site.css` e interações em `static/site.js`. As rotas e os templates administrativos existentes estão em `app.py`.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário, sem alterar as inscrições reais. Capturas da versão revisada estão em `artifacts/`.

## Railway

Configure `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` e `DATABASE_PATH=/data/shekinah.db`. Adicione volume persistente em `/data`. O `Procfile` usa Gunicorn.

A inscrição fica pendente até a coordenação confirmar o pagamento. A chave PIX exibida é para copiar; não há integração bancária automática. As datas, o valor e os contatos foram preservados do projeto original. O endereço exato do retiro deve ser confirmado com a coordenação.

Antes de receber dados de menores, configure política de privacidade e consentimento apropriado.

## Identidade visual

A abertura usa a cena de adoração já existente em `static/hero-shekinah.jpg`. O arquivo `static/shekinah-oficial.png` é uma adaptação assistida por imagem da captura de tela enviada pela organização: pomba branca, cruz, luz dourada e lema. Não é o arquivo vetorial original; quando ele estiver disponível, esse asset pode ser substituído diretamente.

A versão em uso, `static/shekinah-transparente.png`, tem fundo transparente. No rodapé, a identificação da paróquia usa `static/logo-igreja-oficial.svg`, em vez de texto separado.
