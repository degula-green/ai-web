# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawlerPro-SignSrv project.
# Repository: https://github.com/MediaCrawlerPro/MediaCrawlerPro-SignSrv/blob/main/logic/ks/ks_logic.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究JS签名目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


# -*- coding: utf-8 -*-
import json
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import parse_qsl

import execjs
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from constant import KS_JAVASCRIPT_SIGN
from params.ks_sign import KsSignRequest, KsSignResponse


class AbstractKsSign(ABC):
    @abstractmethod
    async def sign(self, req_data: KsSignRequest, force_init: bool = False) -> KsSignResponse:
        raise NotImplementedError


class KsJavascriptSign(AbstractKsSign):
    def __init__(self):
        script_path = Path('pkg/js/ks.js')
        script_content = script_path.read_text(encoding='utf-8')
        self.ks_sign_obj = execjs.compile(script_content)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
    async def sign(self, req: KsSignRequest, force_init: bool = False) -> KsSignResponse:
        """
        快手请求签名js版本, 如果发生异常默认重试3次，每次间隔500ms
        签名仅绑定 path + query + body + 时间窗，不绑定 UA/cookie
        Args:
            req :
            force_init:

        Returns:

        """
        query_json = json.dumps(dict(parse_qsl(req.query_params))) if req.query_params else '{"caver":"2"}'
        ns_hxfalcon = self.ks_sign_obj.call("ks_sign", req.uri, query_json, req.body or "{}")
        return KsSignResponse(ns_hxfalcon=ns_hxfalcon)


class KsSignFactory:
    @staticmethod
    def get_sign(sign_type: str) -> AbstractKsSign:
        if sign_type == KS_JAVASCRIPT_SIGN:
            return KsJavascriptSign()
        else:
            raise NotImplementedError


class KsSignLogic:
    def __init__(self, sign_type: str):
        """
        初始化
        :param sign_type:
        """
        self.sign_server = KsSignFactory.get_sign(sign_type)

    async def sign(self, req_data: KsSignRequest) -> KsSignResponse:
        """
        签名
        :param req_data:
        :return:
        """
        try:
            return await self.sign_server.sign(req_data)
        except RetryError:
            return await self.sign_server.sign(req_data, force_init=True)
