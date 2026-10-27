# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawlerPro-SignSrv project.
# Repository: https://github.com/MediaCrawlerPro/MediaCrawlerPro-SignSrv/blob/main/params/ks_sign.py
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

from pydantic import BaseModel, Field


class KsSignRequest(BaseModel):
    uri: str = Field(..., title="request_uri", description="请求的uri，如 /rest/v/profile/feed")
    query_params: str = Field(..., title="query_params", description="请求的query_params(urlencode之后的参数，如 caver=2)")
    body: str = Field("", title="body", description="请求的body(JSON字符串)，如 {\"user_id\":\"xxx\",\"pcursor\":\"\",\"page\":\"profile\"}")
    user_agent: str = Field("", title="user_agent", description="请求的user_agent(签名不绑定UA，可留空)")
    cookies: str = Field("", title="cookies", description="请求的cookies(签名不绑定cookie，可留空)")


class KsSignResponse(BaseModel):
    ns_hxfalcon: str = Field(..., title="ns_hxfalcon", description="快手 __NS_hxfalcon 签名（请求时作为 __NS_hxfalcon 参数传入）")
