from starlette.testclient import TestClient


def test_login_returns_token_and_me_reads_current_user(client: TestClient) -> None:
    """用户登录后应获得 JWT，并能读取当前用户信息。"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )

    assert response.status_code == 200
    token_body = response.json()
    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"
    assert me_response.json()["role"] == "admin"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    """错误密码不能换取访问令牌。"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_requires_valid_bearer_token(client: TestClient) -> None:
    """读取当前用户必须提供有效 Bearer Token。"""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_write_routes_require_authentication(client: TestClient) -> None:
    """写操作必须带有效 JWT，避免绕过前端守卫直接调用 API。"""
    response = client.post(
        "/api/v1/hosts",
        json={
            "name": "protected-host",
            "ip_address": "192.0.2.20",
            "ssh_port": 22,
            "ssh_user": "root",
            "private_key_path": "/home/demo/.ssh/id_rsa",
            "description": "protected",
        },
    )

    assert response.status_code == 401


def test_authenticated_user_can_create_host(client: TestClient) -> None:
    """登录用户可以继续完成主演示链路中的主机创建。"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/hosts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "authenticated-host",
            "ip_address": "192.0.2.21",
            "ssh_port": 22,
            "ssh_user": "root",
            "private_key_path": "/home/demo/.ssh/id_rsa",
            "description": "authenticated",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "authenticated-host"
