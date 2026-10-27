#!/bin/bash
#
# 火山引擎语音识别（异步模式）
#
# 用法: ./volcengine_transcribe.sh <audio_url>
# 输出: volcengine_result.json
#

AUDIO_URL="$1"

if [ -z "$AUDIO_URL" ]; then
  echo "❌ 用法: ./volcengine_transcribe.sh <audio_url>"
  exit 1
fi

# 获取 API Key
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$(dirname "$(dirname "$SCRIPT_DIR")")/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 找不到 $ENV_FILE"
  echo "请创建 .env：VOLCENGINE_APP_ID + VOLCENGINE_ACCESS_TOKEN（音视频字幕 VC），或 VOLCENGINE_API_KEY（旧方式）"
  exit 1
fi

get_env() {
  local k="$1"
  grep "^${k}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-
}

API_KEY=$(get_env VOLCENGINE_API_KEY)
APP_ID=$(get_env VOLCENGINE_APP_ID)
ACCESS_TOKEN=$(get_env VOLCENGINE_ACCESS_TOKEN)

USE_VC=0
if [ -n "$APP_ID" ] && [ -n "$ACCESS_TOKEN" ]; then
  USE_VC=1
elif [ -z "$API_KEY" ]; then
  echo "❌ .env 需配置其一："
  echo "   - 推荐：VOLCENGINE_APP_ID + VOLCENGINE_ACCESS_TOKEN（控制台「音视频字幕生成」）"
  echo "   - 或：VOLCENGINE_API_KEY（豆包 x-api-key，需开通对应资源）"
  exit 1
fi

echo "🎤 提交火山引擎转录任务..."
echo "音频 URL: $AUDIO_URL"
if [ "$USE_VC" -eq 1 ]; then
  echo "🔑 认证：音视频字幕 VC（appid + Bearer;AccessToken）"
else
  echo "🔑 认证：x-api-key"
fi

# 读取热词词典
# 词典在 videocut/字幕/（SCRIPT_DIR 为 videocut/剪口播/scripts）
DICT_FILE="$(dirname "$(dirname "$SCRIPT_DIR")")/字幕/词典.txt"
HOT_WORDS=""
if [ -f "$DICT_FILE" ]; then
  # API 要求 hot_words 为对象数组（非字符串数组），每项至少含 word 字段
  HOT_WORDS=$(grep -v '^[[:space:]]*$' "$DICT_FILE" | sed 's/\\/\\\\/g;s/"/\\"/g' | while IFS= read -r word || [ -n "$word" ]; do
    [ -z "$word" ] && continue
    printf '{"word":"%s"},' "$word"
  done | sed 's/,$//')
  echo "📖 加载热词: $(grep -cv '^[[:space:]]*$' "$DICT_FILE" 2>/dev/null || echo 0) 个"
fi

# 构建请求体（VC 官方示例为 JSON 仅含 url；热词非 VC 文档标配，仅 x-api-key 模式附带）
if [ "$USE_VC" -eq 1 ]; then
  REQUEST_BODY="{\"url\": \"$AUDIO_URL\"}"
else
  if [ -n "$HOT_WORDS" ]; then
    REQUEST_BODY="{\"url\": \"$AUDIO_URL\", \"hot_words\": [$HOT_WORDS]}"
  else
    REQUEST_BODY="{\"url\": \"$AUDIO_URL\"}"
  fi
fi

SUBMIT_QS="language=zh-CN&use_itn=True&use_capitalize=True&max_lines=1&words_per_line=15"
if [ "$USE_VC" -eq 1 ]; then
  SUBMIT_QS="appid=${APP_ID}&${SUBMIT_QS}"
fi

# 步骤1: 提交任务
if [ "$USE_VC" -eq 1 ]; then
  SUBMIT_RESPONSE=$(curl -s -L -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?${SUBMIT_QS}" \
    -H "Accept: */*" \
    -H "Authorization: Bearer;${ACCESS_TOKEN}" \
    -H "Connection: keep-alive" \
    -H "content-type: application/json" \
    -d "$REQUEST_BODY")
else
  SUBMIT_RESPONSE=$(curl -s -L -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?${SUBMIT_QS}" \
    -H "Accept: */*" \
    -H "x-api-key: $API_KEY" \
    -H "Connection: keep-alive" \
    -H "content-type: application/json" \
    -d "$REQUEST_BODY")
fi

# 提取任务 ID
TASK_ID=$(echo "$SUBMIT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
  echo "❌ 提交失败，响应:"
  echo "$SUBMIT_RESPONSE"
  exit 1
fi

echo "✅ 任务已提交，ID: $TASK_ID"
echo "⏳ 等待转录完成..."

# 步骤2: 轮询结果
MAX_ATTEMPTS=120  # 最多等待 10 分钟（每 5 秒查一次）
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 5
  ATTEMPT=$((ATTEMPT + 1))

  if [ "$USE_VC" -eq 1 ]; then
    QUERY_URL="https://openspeech.bytedance.com/api/v1/vc/query?appid=${APP_ID}&id=${TASK_ID}"
    QUERY_RESPONSE=$(curl -s -L -X GET "$QUERY_URL" \
      -H "Accept: */*" \
      -H "Authorization: Bearer;${ACCESS_TOKEN}" \
      -H "Connection: keep-alive")
  else
    QUERY_RESPONSE=$(curl -s -L -X GET "https://openspeech.bytedance.com/api/v1/vc/query?id=$TASK_ID" \
      -H "Accept: */*" \
      -H "x-api-key: $API_KEY" \
      -H "Connection: keep-alive")
  fi

  # 检查状态
  STATUS=$(echo "$QUERY_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | cut -d':' -f2)

  if [ "$STATUS" = "0" ]; then
    # 成功完成
    echo "$QUERY_RESPONSE" > volcengine_result.json
    echo "✅ 转录完成，已保存 volcengine_result.json"

    # 显示统计
    UTTERANCES=$(echo "$QUERY_RESPONSE" | grep -o '"text"' | wc -l)
    echo "📝 识别到 $UTTERANCES 段语音"
    exit 0
  elif [ "$STATUS" = "1000" ] || [ "$STATUS" = "2000" ]; then
    # 处理中（1000 / 2000 依产品线文档）
    echo -n "."
  else
    # 其他错误
    echo ""
    echo "❌ 转录失败，响应:"
    echo "$QUERY_RESPONSE"
    exit 1
  fi
done

echo ""
echo "❌ 超时，任务未完成"
exit 1
