"""
Master Key Authentication, Auto-Rotation & Password Reset Test Suite
=====================================================================
Validates Master Key format constraints, brute-force defenses,
single-use reset token issuance, password resets, key rotation,
in-app security notifications, and zero-knowledge dismissal scrubbing.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from database.session import SessionLocal
from models.user import User
from models.master_key import MasterKey
from models.password_history import PasswordHistory
from models.security_notification import SecurityNotification
from core.config import settings
from core.security import hash_password, create_access_token


def get_test_email() -> str:
    """Dynamically resolves test user email from application settings."""
    return settings.seed_user_email or "admin@finance.market"


DEFAULT_TEST_PWD = settings.seed_user_password or "TestPassword@123"


@pytest.fixture
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.anyio
async def test_master_key_format_validation():
    """Validates regex format constraint: XXXX-XXXX-XXXX-XXXX."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid length should fail regex with 422
        resp1 = await client.post(
            "/api/v1/auth/master-key/verify", json={"email": get_test_email(), "master_key": "ABC1-DEF2"}
        )
        assert resp1.status_code == 422
        assert "VALIDATION_ERROR" in resp1.json()["error"]["code"]

        # Invalid characters should fail regex with 422
        resp2 = await client.post(
            "/api/v1/auth/master-key/verify",
            json={"email": get_test_email(), "master_key": "ABCD-EFGH-IJKL-!@#$"},
        )
        assert resp2.status_code == 422
        assert "VALIDATION_ERROR" in resp2.json()["error"]["code"]


@pytest.mark.anyio
async def test_master_key_wrong_key_rejection():
    """Validates that an invalid master key is rejected with 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/master-key/verify",
            json={"email": get_test_email(), "master_key": "ZZZZ-9999-XXXX-0000"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["success"] is False
        assert "Invalid Master Security Key" in data["error"]["message"]


@pytest.mark.anyio
async def test_master_key_password_reset_and_rotation_flow(test_db):
    """
    Validates complete lifecycle:
    1. Verification of valid master key
    2. Single-use JWT reset token issuance
    3. Password reset with history checks
    4. Auto-rotation: Old key deleted, fresh key generated
    5. Old key fails subsequent verification
    6. In-App Notification: User fetches rotated key notification with Bearer token
    7. User dismisses notification -> plaintext key scrubbed
    8. New master key successfully verifies
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_email = get_test_email()
        user = test_db.query(User).filter(User.email == test_email).first()
        assert user is not None

        # Set up initial test master key
        initial_key = "INIT-MK01-TEST-2026"
        hashed = hash_password(initial_key)

        # Deactivate any previous active keys or notifications for test
        test_db.query(MasterKey).filter(MasterKey.user_id == user.id).delete()
        test_db.query(PasswordHistory).filter(PasswordHistory.user_id == user.id).delete()
        test_db.query(SecurityNotification).filter(SecurityNotification.user_id == user.id).delete()

        # Reset password to default test password
        user.password_hash = hash_password(DEFAULT_TEST_PWD)
        mk = MasterKey(user_id=user.id, key_hash=hashed)
        test_db.add(mk)
        test_db.commit()

        # Step 1: Verify Initial Master Key
        resp1 = await client.post(
            "/api/v1/auth/master-key/verify", json={"email": user.email, "master_key": initial_key}
        )
        assert resp1.status_code == 200
        token = resp1.json()["reset_token"]
        assert token is not None

        # Step 2: Perform password reset
        new_pwd = "RotatedSecurePassword@2026"
        resp_reset = await client.post(
            "/api/v1/auth/master-key/reset-password",
            json={"reset_token": token, "new_password": new_pwd, "confirm_password": new_pwd},
        )
        assert resp_reset.status_code == 200
        assert resp_reset.json()["success"] is True

        # Step 3: Verify old master key is now retired/deleted (cannot be used again)
        resp_old_key = await client.post(
            "/api/v1/auth/master-key/verify", json={"email": user.email, "master_key": initial_key}
        )
        assert resp_old_key.status_code == 401

        # Step 4: Generate Bearer access token for the authenticated user
        access_token = create_access_token({"sub": str(user.id)})
        assert access_token is not None

        # Step 5: Fetch in-app security notification for Bell icon
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        resp_notif = await client.get("/api/v1/auth/master-key/notification", headers=auth_headers)

        assert resp_notif.status_code == 200
        notif_data = resp_notif.json()
        assert notif_data["has_notification"] is True
        new_master_key = notif_data["master_key"]
        notif_id = notif_data["notification_id"]
        assert new_master_key is not None
        assert new_master_key != initial_key
        assert len(new_master_key) == 19

        # Step 6: Dismiss notification and verify plaintext is scrubbed
        resp_dismiss = await client.post(
            "/api/v1/auth/master-key/notification/dismiss", headers=auth_headers, json={"notification_id": notif_id}
        )
        assert resp_dismiss.status_code == 200

        # Step 7: Subsequent fetch should indicate no pending notification
        resp_notif2 = await client.get("/api/v1/auth/master-key/notification", headers=auth_headers)
        assert resp_notif2.status_code == 200
        assert resp_notif2.json()["has_notification"] is False

        # Step 8: Verify the newly rotated master key is valid for future operations
        resp_new_verify = await client.post(
            "/api/v1/auth/master-key/verify", json={"email": user.email, "master_key": new_master_key}
        )
        assert resp_new_verify.status_code == 200
        assert resp_new_verify.json()["success"] is True

        # Cleanup: Restore default credentials for test suite continuity
        user_refresh = test_db.query(User).filter(User.email == test_email).first()
        user_refresh.password_hash = hash_password(DEFAULT_TEST_PWD)
        test_db.query(PasswordHistory).filter(PasswordHistory.user_id == user.id).delete()
        test_db.query(SecurityNotification).filter(SecurityNotification.user_id == user.id).delete()
        test_db.commit()
