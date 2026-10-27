from __future__ import annotations

from fastapi import APIRouter, Depends, Request, UploadFile, File

from app.api.deps import get_auth_service, get_current_auth_context
from app.core.contract import contract_success
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterEmailRequest,
    RegisterPhoneRequest,
    SendEmailCodeRequest,
    SendSmsCodeRequest,
    VerifyEmailCodeRequest,
    VerifySmsCodeRequest,
    UpdateProfileRequest,
)

router = APIRouter()


@router.post("/login")
def login(payload: LoginRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.login(payload)
    return contract_success(data.model_dump(), msg="登录成功")


@router.post("/logout")
def logout(payload: LogoutRequest, auth_service=Depends(get_auth_service), context=Depends(get_current_auth_context)):
    data = auth_service.logout(context=context, payload=payload)
    return contract_success(data.model_dump(), msg="登出成功")


@router.get("/me")
def me(auth_service=Depends(get_auth_service), context=Depends(get_current_auth_context)):
    data = auth_service.me(context=context)
    return contract_success(data.model_dump(), msg="查询成功")


@router.patch("/me")
def update_me(payload: UpdateProfileRequest, auth_service=Depends(get_auth_service), context=Depends(get_current_auth_context)):
    data = auth_service.update_profile(context=context, payload=payload)
    return contract_success(data.model_dump(), msg="修改成功")


@router.post("/avatar/upload")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    auth_service=Depends(get_auth_service),
    context=Depends(get_current_auth_context)
):
    import uuid
    from fastapi import HTTPException
    
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    object_name = f"avatars/{context.user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    try:
        content = await file.read()
        url = request.app.state.container.storage_adapter.upload(
            object_name, 
            content, 
            content_type=file.content_type or "application/octet-stream"
        )
        return contract_success({"url": url}, msg="上传成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/refresh")
def refresh(payload: RefreshRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.refresh(refresh_token=payload.refreshToken, session_id=payload.sessionId)
    return contract_success(data.model_dump(), msg="刷新成功")


@router.post("/email/send-code")
def send_email_code(payload: SendEmailCodeRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.send_email_code(payload.email, scene=payload.scene)
    return contract_success(data.model_dump(), msg="验证码发送成功")


@router.post("/email/verify-code")
def verify_email_code(payload: VerifyEmailCodeRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.verify_email_code(payload.email, payload.code, scene=payload.scene)
    return contract_success(data.model_dump(), msg="校验成功")


@router.post("/sms/send-code")
def send_sms_code(payload: SendSmsCodeRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.send_sms_code(payload.phone, scene=payload.scene)
    return contract_success(data.model_dump(), msg="验证码发送成功")


@router.post("/sms/verify-code")
def verify_sms_code(payload: VerifySmsCodeRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.verify_sms_code(payload.phone, payload.code, scene=payload.scene)
    return contract_success(data.model_dump(), msg="校验成功")


@router.post("/register/email")
def register_email(payload: RegisterEmailRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.register_email(payload)
    return contract_success(data.model_dump(), msg="注册成功")


@router.post("/register/phone")
def register_phone(payload: RegisterPhoneRequest, auth_service=Depends(get_auth_service)):
    data = auth_service.register_phone(payload)
    return contract_success(data.model_dump(), msg="注册成功")
