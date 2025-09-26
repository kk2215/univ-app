# tests/test_auth.py

from app.models import User

def test_registration(client, app):
    """
    新規ユーザー登録が成功することを確認するテスト
    """
    # /registerページにPOSTリクエストを送信
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'password',
        'password_confirm': 'password',
        'grade': 'high3',
        'course_type': 'science',
        'school': 'テスト大学',
        'faculty': 'テスト学部'
    }, follow_redirects=True)

    # 登録後にダッシュボードにリダイレクトされていることを確認
    assert response.status_code == 200
    assert "こんにちは、testuserさん！".encode('utf-8') in response.data

    # データベースにユーザーが本当に作成されたかを確認
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None

def test_login_logout(client, app):
    """
    ログインとログアウトが成功することを確認するテスト
    """
    # まず、テスト用のユーザーを登録しておく
    client.post('/register', data={
        'username': 'loginuser',
        'password': 'password',
        'password_confirm': 'password',
        'grade': 'high3', 'course_type': 'science', 'school': 'テスト大学', 'faculty': 'テスト学部'
    })

    # ログイン処理
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'password'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "こんにちは、loginuserさん！".encode('utf-8') in response.data
    assert "その他".encode('utf-8') in response.data 
    # ログアウト処理
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert "ログイン".encode('utf-8') in response.data