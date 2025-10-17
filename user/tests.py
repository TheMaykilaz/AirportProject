from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient


User = get_user_model()


class UserAuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.base = "/api/users/"

    def test_registration_returns_tokens(self):
        url = self.base + "auth/register/"
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "strongpass123",
            "first_name": "New",
            "last_name": "User",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertIn("user", data)
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_email_login_request_and_verify(self):
        # Request a verification code
        req_url = self.base + "auth/email/request/"
        email = "codeuser@example.com"
        resp = self.client.post(req_url, {"email": email}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        # In DEBUG the code is returned for convenience
        self.assertIn("verification_code", data)
        code = data["verification_code"]

        # Verify the code and receive tokens
        verify_url = self.base + "auth/email/verify/"
        resp2 = self.client.post(verify_url, {"email": email, "code": code}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        data2 = resp2.json()
        self.assertIn("access", data2)
        self.assertIn("refresh", data2)
        self.assertIn("user", data2)

    def test_me_endpoint_requires_auth(self):
        me_url = self.base + "users/me/"
        # Unauthenticated should be 401
        resp = self.client.get(me_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated returns user data
        user = User.objects.create_user(email="me@example.com", password="pass12345", username="me")
        self.client.force_authenticate(user=user)
        resp2 = self.client.get(me_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.json().get("email"), user.email)

    def test_change_password_flow(self):
        user = User.objects.create_user(email="pw@example.com", password="oldpass123", username="pw")
        self.client.force_authenticate(user=user)
        url = self.base + "auth/password/change/"
        # Wrong old password
        resp = self.client.post(url, {"old_password": "bad", "new_password": "newpass123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # Correct old password
        resp2 = self.client.post(url, {"old_password": "oldpass123", "new_password": "newpass123"}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

    def test_admin_ping_permission(self):
        url = self.base + "auth/test/admin/"
        # Regular user forbidden
        user = User.objects.create_user(email="u@example.com", password="p12345678", username="u")
        self.client.force_authenticate(user=user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Staff/admin allowed
        admin = User.objects.create_user(email="a@example.com", password="p12345678", username="a", is_staff=True)
        self.client.force_authenticate(user=admin)
        resp2 = self.client.get(url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
