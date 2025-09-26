# tests/test_main.py

def test_index_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    # トップページにアクセス
    response = client.get('/')
    
    # HTTPステータスコードが200 (OK) であることを確認
    assert response.status_code == 200
    
    # ページに特定の文字列が含まれていることを確認
    assert "最短ルートを".encode('utf-8') in response.data
    assert "無料で始める".encode('utf-8') in response.data