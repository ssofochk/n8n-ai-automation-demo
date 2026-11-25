import unittest
from fastapi.testclient import TestClient
from src.api import app

class APITests(unittest.TestCase):
    def test_operations(self):
        with TestClient(app) as client:
            for op, result in [('add',10),('subtract',6),('multiply',16),('divide',4)]:
                with self.subTest(op=op):
                    response = client.post('/api/calculate',json={'a':8,'b':2,'operation':op})
                    self.assertEqual(response.status_code,200)
                    self.assertEqual(response.json(),{'result':result})
    def test_division_error(self):
        with TestClient(app) as client:
            response = client.post('/api/calculate',json={'a':8,'b':0,'operation':'divide'})
            self.assertEqual(response.status_code,400)
            self.assertEqual(response.json(),{'detail':'Cannot divide by zero'})
    def test_invalid(self):
        with TestClient(app) as client:
            self.assertEqual(client.post('/api/calculate',json={'a':'oops','b':2,'operation':'add'}).status_code,422)
    def test_frontend_served(self):
        with TestClient(app) as client:
            self.assertIn('Kawaii',client.get('/').text)
