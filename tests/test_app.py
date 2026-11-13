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
                    telefone_resp='11988887777', medicamento='Não faz uso', chegada='', pagamento='PIX')
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
