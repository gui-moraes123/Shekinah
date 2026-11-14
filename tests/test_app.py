import os
import re
import tempfile
import unittest

TEMP = tempfile.TemporaryDirectory()
os.environ['DATABASE_PATH'] = os.path.join(TEMP.name, 'test.db')
os.environ['SECRET_KEY'] = 'test-only-secret'
os.environ['ADMIN_USERNAME'] = 'test-coordinator'
os.environ['ADMIN_PASSWORD'] = 'test-only-password'
from app import app, db


class RetreatFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with db() as connection:
            connection.execute('DELETE FROM inscricoes')

    def token(self, url='/'):
        html = self.client.get(url).get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def registration(self, **changes):
        data = dict(tipo='Encontrista', nome='Maria Teste', responsavel='Responsável Teste',
                    nascimento='2010-05-04', endereco='Rua Teste, 10', telefone='11999998888',
                    telefone_resp='11988887777', medicamento='Não faz uso', chegada='', pagamento='PIX', restricao_alimentar='Não possuo')
        data.update(changes)
        data['csrf_token'] = self.token()
        return self.client.post('/inscrever', data=data)

    def login(self):
        return self.client.post('/admin/login', data=dict(csrf_token=self.token('/admin/login'),
                               usuario='test-coordinator', senha='test-only-password'))

    def test_public_pages_assets_and_calendar(self):
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('ACENDER', html)
        self.assertIn('/static/shekinah-transparente.png', html)
        for asset in re.findall(r'(?:src|href)="(/static/[^"?]+)', html):
            with self.client.get(asset) as response:
                self.assertEqual(response.status_code, 200, asset)
        calendar = self.client.get('/retiro.ics')
        self.assertIn('DTSTART;VALUE=DATE:20270115', calendar.get_data(as_text=True))
        self.assertIn('DTEND;VALUE=DATE:20270118', calendar.get_data(as_text=True))
        self.assertIn('attachment', calendar.headers['Content-Disposition'])
        self.assertEqual(self.client.get('/missing').status_code, 404)

    def test_gallery_selection_and_sources(self):
        from app import GALLERY
        self.assertEqual(len(GALLERY), 12)
        self.assertEqual(sum(photo['edition'] == 1 for photo in GALLERY), 6)
        self.assertEqual(sum(photo['edition'] == 2 for photo in GALLERY), 6)
        self.assertEqual(len({photo['src'] for photo in GALLERY}), 12)
        self.assertEqual(len({photo['post'] for photo in GALLERY}), 4)
        html = self.client.get('/').get_data(as_text=True)
        self.assertEqual(html.count('class="gallery-photo"'), 12)
        for photo in GALLERY:
            self.assertTrue(photo['source'].startswith('https://www.instagram.com/p/'))
            with self.client.get(photo['src']) as response:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'image/jpeg')

    def test_csrf_and_admin_protection(self):
        self.assertEqual(self.client.post('/inscrever', data={}).status_code, 400)
        for route in ['/admin', '/admin/exportar', '/admin/inscricao/1']:
            self.assertEqual(self.client.get(route).status_code, 302)
        self.assertEqual(self.client.post('/admin/pagamento/1', data={'status':'Confirmado'}).status_code, 400)

    def test_register_confirm_inspect_export_and_logout(self):
        response = self.registration(nome='<script>alert(1)</script>')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Seu protocolo'.upper(), response.get_data(as_text=True))
        with db() as connection:
            row = connection.execute('SELECT * FROM inscricoes').fetchone()
            number = row['id']
            self.assertEqual(row['status'], 'Pendente')
        self.assertEqual(self.login().status_code, 302)
        dashboard = self.client.get('/admin').get_data(as_text=True)
        self.assertIn('&lt;script&gt;', dashboard)
        self.assertNotIn('<script>alert(1)</script>', dashboard)
        self.assertIn('Não faz uso', self.client.get(f'/admin/inscricao/{number}').get_data(as_text=True))
        token = self.token('/admin')
        response = self.client.post(f'/admin/pagamento/{number}', data={'csrf_token':token,'status':'Confirmado'})
        self.assertEqual(response.status_code, 302)
        with db() as connection:
            self.assertEqual(connection.execute('SELECT status FROM inscricoes').fetchone()[0], 'Confirmado')
        self.assertIn('Confirmado', self.client.get('/admin/exportar').get_data(as_text=True))
        self.assertEqual(self.client.post('/admin/sair', data={'csrf_token':token}).status_code, 302)
        self.assertEqual(self.client.get('/admin').status_code, 302)

    def test_delete_requires_login_csrf_and_explicit_confirmation(self):
        self.registration()
        with db() as connection:
            number = connection.execute('SELECT id FROM inscricoes').fetchone()[0]
        url = f'/admin/inscricao/{number}/excluir'
        token = self.token()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(url, data={'csrf_token':token,'confirmacao':'excluir'}).status_code, 302)
        self.login()
        self.assertEqual(self.client.post(url, data={'confirmacao':'excluir'}).status_code, 400)
        token = self.token(url)
        self.assertEqual(self.client.post(url, data={'csrf_token':token}).status_code, 400)
        with db() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM inscricoes').fetchone()[0], 1)

    def test_delete_confirmation_is_safe_and_only_removes_selected_registration(self):
        self.registration(nome='Excluir <script>teste</script>')
        self.registration(nome='Manter participante')
        with db() as connection:
            number = connection.execute('SELECT MIN(id) FROM inscricoes').fetchone()[0]
        self.login()
        url = f'/admin/inscricao/{number}/excluir'
        confirmation = self.client.get(url).get_data(as_text=True)
        self.assertIn('Excluir &lt;script&gt;teste&lt;/script&gt;', confirmation)
        self.assertIn('Cancelar e voltar', confirmation)
        self.assertIn(url, self.client.get('/admin').get_data(as_text=True))
        self.assertIn(url, self.client.get(f'/admin/inscricao/{number}').get_data(as_text=True))
        with db() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM inscricoes').fetchone()[0], 2)
        response = self.client.post(url, data={'csrf_token':self.token(url),'confirmacao':'excluir'})
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.location.endswith('/admin'))
        self.assertIn('excluída com sucesso', self.client.get('/admin').get_data(as_text=True))
        with db() as connection:
            rows = connection.execute('SELECT nome FROM inscricoes').fetchall()
            self.assertEqual([r['nome'] for r in rows], ['Manter participante'])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(f'/admin/inscricao/{number}').status_code, 404)
        export = self.client.get('/admin/exportar').get_data(as_text=True)
        self.assertIn('Manter participante', export)
        self.assertNotIn('Excluir', export)
        self.assertEqual(self.client.post(url, data={'csrf_token':self.token('/admin'),'confirmacao':'excluir'}).status_code, 404)

    def test_dietary_restriction_validation_and_admin_visibility(self):
        for value in ('', '   ', 'x' * 501):
            self.assertEqual(self.registration(restricao_alimentar=value).status_code, 422)
        restriction = 'Alergia a amendoim; sem lactose <script>teste</script>'
        response = self.registration(restricao_alimentar=restriction, nome='')
        self.assertEqual(response.status_code, 422)
        self.assertIn('sem lactose &lt;script&gt;', response.get_data(as_text=True))
        self.assertEqual(self.registration(restricao_alimentar=restriction).status_code, 200)
        with db() as connection:
            row = connection.execute('SELECT * FROM inscricoes').fetchone()
            self.assertEqual(row['restricao_alimentar'], restriction)
            number = row['id']
        self.login()
        for url in ('/admin', f'/admin/inscricao/{number}'):
            html = self.client.get(url).get_data(as_text=True)
            self.assertIn('Alergia a amendoim; sem lactose &lt;script&gt;', html)
            self.assertNotIn('<script>teste</script>', html)
        export = self.client.get('/admin/exportar').get_data(as_text=True)
        self.assertIn('restricao_alimentar', export)
        self.assertIn('Alergia a amendoim', export)

    def test_dietary_migration_preserves_existing_registrations(self):
        import sqlite3
        import subprocess
        import sys
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            database = os.path.join(directory, 'legacy.db')
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE inscricoes (id INTEGER PRIMARY KEY, tipo TEXT,nome TEXT,responsavel TEXT,nascimento TEXT,endereco TEXT,telefone TEXT,telefone_resp TEXT,medicamento TEXT,chegada TEXT,pagamento TEXT,status TEXT DEFAULT 'Pendente',criado TEXT)")
                connection.execute("INSERT INTO inscricoes(id,nome,status) VALUES (42,'Cadastro anterior','Confirmado')")
            environment = dict(os.environ, DATABASE_PATH=database)
            for _ in range(2):
                subprocess.run([sys.executable, '-c', 'import app'], env=environment,
                               cwd=Path(__file__).resolve().parents[1], check=True, capture_output=True)
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute('SELECT id,nome,status,restricao_alimentar FROM inscricoes').fetchall(),
                                 [(42, 'Cadastro anterior', 'Confirmado', '')])
                self.assertEqual(sum(column[1] == 'restricao_alimentar' for column in connection.execute('PRAGMA table_info(inscricoes)')), 1)

    def test_validation_keeps_values_and_does_not_insert(self):
        for change in [dict(nascimento='2016-01-16'), dict(nascimento='invalid'), dict(nome='x'*151),
                       dict(telefone='abc'), dict(tipo='Other'), dict(tipo='Trabalhador',chegada='')]:
            with self.subTest(change=change):
                response = self.registration(**change)
                self.assertEqual(response.status_code, 422)
                self.assertIn('Rua Teste, 10', response.get_data(as_text=True))
        with db() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM inscricoes').fetchone()[0], 0)

    def test_age_boundary_worker_arrival_and_filter_preservation(self):
        self.assertEqual(self.registration(nascimento='2016-01-15',tipo='Trabalhador',chegada='Sábado pela manhã').status_code,200)
        self.login()
        filtered = self.client.get('/admin?status=Pendente&busca=Maria').get_data(as_text=True)
        self.assertIn('tipo=Trabalhador&amp;status=Pendente&amp;busca=Maria',filtered)
        token = self.token('/admin')
        self.assertEqual(self.client.post('/admin/pagamento/99999',data={'csrf_token':token,'status':'Confirmado'}).status_code,404)
        self.assertEqual(self.client.post('/admin/pagamento/1',data={'csrf_token':token,'status':'Invalid'}).status_code,400)


if __name__ == '__main__':
    unittest.main()
