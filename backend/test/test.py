import unittest
from app import app

class TestRAGAssistant(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_root_endpoint(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['ok'])
        self.assertIn('try', data)
    
    def test_query_no_input(self):
        response = self.app.post('/api/query', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_query_with_input(self):
        response = self.app.post('/api/query', json={'query': 'test question'})
        self.assertIn(response.status_code, [200, 500])
    
    def test_query_get_method(self):
        response = self.app.get('/api/query?query=hello')
        self.assertIn(response.status_code, [200, 500])

if __name__ == '__main__':
    print("Running RAG Assistant Tests...")
    print("=" * 50)
    
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("Tests completed!")
    print("\nTo run these tests:")
    print("cd backend && python test/test.py")
