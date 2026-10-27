from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import string
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from app.adapters.verification.base import BaseSmsProvider, DeliveryReceipt
from app.core.config import SmsSettings


@dataclass(slots=True, frozen=True)
class SmsMessageRecord:
    phone_number: str
    message: str
    code: str
    purpose: str
    ttl_minutes: int


class MockSmsProvider(BaseSmsProvider):
    def __init__(self) -> None:
        self.sent_messages: list[SmsMessageRecord] = []

    def send_verification_code(self, *, phone_number: str, code: str, purpose: str, ttl_minutes: int) -> DeliveryReceipt:
        message = f"Verification code for {purpose}: {code}. Expires in {ttl_minutes} minutes."
        self.sent_messages.append(
            SmsMessageRecord(
                phone_number=phone_number,
                message=message,
                code=code,
                purpose=purpose,
                ttl_minutes=ttl_minutes,
            )
        )
        print("\n" + "*"*50)
        print(f"📱 [MOCK SMS] 发送验证码至: {phone_number}")
        print(f"📌 场景: {purpose}")
        print(f"🔢 验证码: {code}")
        print(f"⏳ 有效期: {ttl_minutes} 分钟")
        print("*"*50 + "\n")

        return DeliveryReceipt(
            provider="mock_sms",
            destination=phone_number,
            accepted=True,
            message_id=f"mock-sms-{len(self.sent_messages)}",
            detail="mock_sent",
            payload={"purpose": purpose, "ttl_minutes": str(ttl_minutes)},
        )

    def verify_verification_code(self, *, phone_number: str, code: str) -> bool:
        for item in reversed(self.sent_messages):
            if item.phone_number == phone_number:
                return item.code == code
        return False


class AliyunSmsProvider(BaseSmsProvider):
    def __init__(self, settings: SmsSettings) -> None:
        self.settings = settings

    def _create_client(self):
        try:
            from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
            from alibabacloud_tea_openapi import models as open_api_models
            
            config = open_api_models.Config(
                access_key_id=self.settings.access_key_id,
                access_key_secret=self.settings.access_key_secret,
            )
            config.endpoint = self.settings.endpoint
            return Dypnsapi20170525Client(config)
        except ImportError:
            raise RuntimeError("Aliyun SMS SDK not installed. Please run: pip install alibabacloud_dypnsapi20170525 alibabacloud_tea_openapi")

    def send_verification_code(self, *, phone_number: str, code: str, purpose: str, ttl_minutes: int) -> DeliveryReceipt:
        try:
            from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
            from alibabacloud_tea_util import models as util_models
            
            client = self._create_client()
            send_sms_verify_code_request = dypnsapi_20170525_models.SendSmsVerifyCodeRequest(
                phone_number=phone_number,
                sign_name=self.settings.sign_name,
                template_code=self.settings.template_code,
                template_param=json.dumps({"code": code, "min": str(ttl_minutes)})
            )
            runtime = util_models.RuntimeOptions()
            resp = client.send_sms_verify_code_with_options(send_sms_verify_code_request, runtime)
            accepted = resp.body.code == "OK"
            return DeliveryReceipt(
                provider="aliyun_sms",
                destination=phone_number,
                accepted=accepted,
                message_id=resp.body.request_id,
                detail=resp.body.message,
                payload={"purpose": purpose, "ttl_minutes": str(ttl_minutes), "raw": resp.to_map()},
            )
        except ImportError:
            return DeliveryReceipt(
                provider="aliyun_sms",
                destination=phone_number,
                accepted=False,
                detail="Aliyun SMS SDK not installed. Please run: pip install alibabacloud_dypnsapi20170525 alibabacloud_tea_openapi",
                payload={"purpose": purpose},
            )
        except Exception as e:
            return DeliveryReceipt(
                provider="aliyun_sms",
                destination=phone_number,
                accepted=False,
                detail=str(e),
                payload={"purpose": purpose},
            )

    def verify_verification_code(self, *, phone_number: str, code: str) -> bool:
        try:
            from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
            from alibabacloud_tea_util import models as util_models
            
            client = self._create_client()
            check_sms_verify_code_request = dypnsapi_20170525_models.CheckSmsVerifyCodeRequest(
                phone_number=phone_number,
                verify_code=code
            )
            runtime = util_models.RuntimeOptions()
            resp = client.check_sms_verify_code_with_options(check_sms_verify_code_request, runtime)
            return resp.body.code == "OK"
        except Exception:
            return False

