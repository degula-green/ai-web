# -*- coding: utf-8 -*-
from services.dashscope_paraformer_asr import DashScopeParaformerError, parse_transcription_json


def test_parse_transcription_sample() -> None:
    payload = {
        "file_url": "https://example.com/a.wav",
        "transcripts": [
            {
                "channel_id": 0,
                "sentences": [
                    {
                        "begin_time": 100,
                        "end_time": 2000,
                        "text": "你好世界",
                        "sentence_id": 1,
                        "words": [
                            {"begin_time": 100, "end_time": 500, "text": "你好", "punctuation": ""},
                            {"begin_time": 500, "end_time": 2000, "text": "世界", "punctuation": "。"},
                        ],
                    }
                ],
            }
        ],
    }
    raw = parse_transcription_json(payload)
    assert "你好世界" in raw.text
    assert len(raw.tokens) >= 1


def test_parse_empty_transcripts_raises() -> None:
    try:
        parse_transcription_json({"transcripts": []})
    except DashScopeParaformerError:
        return
    raise AssertionError("expected DashScopeParaformerError")
