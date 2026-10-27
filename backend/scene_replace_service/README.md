# scene_replace_service

基于 FastAPI + PyTorch + RVM 的最小可运行版“视频一键替换场景”服务。

当前版本只做：

- 上传人物视频
- 上传背景图
- 用 RVM 对人物视频逐帧抠图
- 将人物按比例缩放后居中合成到新背景
- 输出 mp4
- 返回输出文件路径
- 提供健康检查接口

## 目录结构

```text
scene_replace_service/
  app/
    main.py
    api/
      routes_scene_replace.py
    core/
      config.py
      logger.py
    services/
      matting_service.py
      compose_service.py
      file_service.py
    schemas/
      response.py
    utils/
      ffmpeg_helper.py
      video_helper.py
  models/
    README.md
  uploads/
  outputs/
  requirements.txt
  README.md
```

## 环境要求

- Python 3.11
- 已安装 FFmpeg，并保证 `ffmpeg` 命令可直接执行
- 建议 CUDA 环境可用；如果没有 CUDA，会自动退回 CPU

Windows 下验证方式：

```powershell
ffmpeg -version
python --version
```

## 安装

进入服务目录：

```powershell
cd backend\scene_replace_service
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动服务：

```powershell
uvicorn app.main:app --reload
```

默认地址：

`http://127.0.0.1:8000`

## 模型权重下载与放置方式

本项目主实现使用 RobustVideoMatting。

默认模型路径：

`models/rvm_mobilenetv3.pth`

建议下载官方 MobileNetV3 权重后放到这里，文件名保持为：

`rvm_mobilenetv3.pth`

说明：

- 当前工程通过 `torch.hub.load("PeterL1n/RobustVideoMatting", "mobilenetv3", pretrained=False)` 加载模型结构
- 再从本地 `models/rvm_mobilenetv3.pth` 加载权重
- 第一次运行时，`torch.hub` 可能会拉取官方仓库代码
- 如果你后续希望完全离线，可把 RVM 官方模型代码 vendoring 到项目里，再把 `matting_service.py` 里的加载逻辑改成本地 import

这里采用的是偏稳妥的工程写法；如果你下载到的权重字段名和当前 `load_state_dict` 略有差异，可按实际模型接口微调。

## 接口

### 1. 健康检查

`GET /health`

返回：

```json
{
  "status": "ok"
}
```

### 2. 场景替换

`POST /api/v1/scene-replace`

`multipart/form-data` 字段：

- `source_video`: 原始人物视频
- `background_image`: 背景图文件，可选
- `background_image_url`: 背景图 URL，可选
- `output_width`: 可选，默认 `1080`
- `output_height`: 可选，默认 `1920`

注意：

- `background_image` 和 `background_image_url` 二选一即可
- 第一版 `source_video` 仍按上传文件处理

返回：

```json
{
  "success": true,
  "message": "scene replaced successfully",
  "data": {
    "task_id": "xxxxxxxx",
    "output_video": "outputs/xxxxxxxx.mp4"
  }
}
```

输出文件可直接访问：

`http://127.0.0.1:8000/outputs/<文件名>.mp4`

## 实现说明

### 处理流程

1. 保存上传的视频与背景图
2. 用 OpenCV 读取视频元数据
3. 用 RVM 对视频逐帧推理，导出前景帧与 alpha mask 帧
4. 遍历 alpha 计算人物全局参考尺寸
5. 将人物缩放后居中贴到背景图上
6. 先导出无声 mp4
7. 用 FFmpeg 将原视频音频复用到结果视频

### 当前合成策略

- 背景图采用 cover 缩放，尽量避免黑边
- 人物按全局最大 bbox 估算统一缩放比例，减少忽大忽小
- 人物居中放置，适合第一版 MVP

### 已处理的边界

- 无 CUDA 时自动走 CPU
- 原视频无音频时，FFmpeg 仍可正常导出视频
- Windows 路径通过 `pathlib` 处理

## 最小测试示例

### curl

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/scene-replace" \
  -F "source_video=@demo/person.mp4" \
  -F "background_image=@demo/bg.jpg" \
  -F "output_width=1080" \
  -F "output_height=1920"
```

### Python requests

```python
import requests

with open("demo/person.mp4", "rb") as source_video, open("demo/bg.jpg", "rb") as background_image:
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/scene-replace",
        files={
            "source_video": source_video,
            "background_image": background_image,
        },
        data={
            "output_width": 1080,
            "output_height": 1920,
        },
        timeout=600,
    )

print(response.status_code)
print(response.json())
```

### 使用背景图 URL

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/scene-replace" \
  -F "source_video=@demo/person.mp4" \
  -F "background_image_url=https://example.com/background.jpg" \
  -F "output_width=1080" \
  -F "output_height=1920"
```

## 启动说明

```powershell
cd backend\scene_replace_service
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 后续可继续做但当前未纳入 MVP

- 背景视频替换
- MODNet fallback 真正接入
- 人物落点与安全边距可配置
- 边缘羽化与色彩匹配
- 异步任务队列
