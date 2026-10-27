# -*- coding: utf-8 -*-
from utils.srt_from_transcript import build_srt_from_cues, transcript_dict_to_srt


def test_transcript_dict_to_srt() -> None:
    srt = transcript_dict_to_srt(
        {
            "text": "ab",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "你好"},
                {"start": 1.5, "end": 3.0, "text": "世界"},
            ],
        }
    )
    assert srt is not None
    assert "00:00:00,000 --> 00:00:01,500" in srt
    assert "你好" in srt
    assert "世界" in srt


def test_build_srt_from_cues() -> None:
    s = build_srt_from_cues([(0, 1, "a")])
    assert s.startswith("1\n")
    assert "a" in s
