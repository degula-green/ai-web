# MediaCrawler Wrapper Integration

This directory contains a non-invasive wrapper layer for integrating
`agent-stack` into the backend task system.

## Goals

- Keep `agent-stack` source code untouched.
- Start backend once and have SignSrv + crawler execution available.
- Isolate dependency/runtime conflicts by running MediaCrawler as subprocesses.

## Runtime Model

- `MediaCrawlerIntegrationService`
  - Starts/stops SignSrv sidecar (optional/autostart).
  - Builds job spec from backend tasks.
  - Bridges backend config to MediaCrawler env/config overrides.
- `MediaCrawlerRunner`
  - Executes crawler jobs via `uv run --directory <crawler-engine> ...`.
  - Captures output, parses `CRAWL_SUMMARY`, persists logs/spec files.
- `MediaCrawlerTaskOrchestrator`
  - Submits async jobs from `TaskService` when `start_async=true`.
  - Drives task state transitions: `created -> collecting -> parsing|failed`.

## Startup Integration

Wired in app lifecycle:

- On backend startup: `container.media_crawler_service.startup()`
- On backend shutdown: `container.media_crawler_service.shutdown()`

SignSrv startup behavior:

- If `/signsrv/pong` already healthy: reuse existing process (do not manage).
- If not healthy and `MEDIACRAWLER_SIGNSRV_AUTOSTART=true`: start sidecar.
- If startup fails:
  - strict mode (`MEDIACRAWLER_SIGNSRV_STRICT_STARTUP=true`): backend startup fails.
  - non-strict mode: backend starts with degraded crawler availability.

## Task Trigger Contract

To submit a MediaCrawler task through existing Task API:

```json
{
  "task_type": "crawler_collect",
  "platform": "xiaohongshu",
  "source_type": "search",
  "source_value": "护肤",
  "start_async": true,
  "config": {
    "collector": "mediacrawler",
    "crawler_type": "search",
    "keywords": "护肤,成分党",
    "enable_comments": false
  }
}
```

Minimum trigger conditions in current wrapper:

- `start_async=true`
- and (`config.collector == "mediacrawler"` or `task_type` is
  `mediacrawler_collect` / `crawler_collect`)

## Config Entry Points

See `.env.example` for all `MEDIACRAWLER_*` keys.

Main path keys:

- `MEDIACRAWLER_ROOT_DIR`
- `MEDIACRAWLER_PYTHON_DIR`
- `MEDIACRAWLER_SIGNSRV_DIR`

Main runtime keys:

- `MEDIACRAWLER_SIGNSRV_AUTOSTART`
- `MEDIACRAWLER_SIGNSRV_STRICT_STARTUP`
- `MEDIACRAWLER_SIGNSRV_HOST`
- `MEDIACRAWLER_SIGNSRV_PORT`
- `MEDIACRAWLER_RUN_TIMEOUT_SECONDS`

## Outputs

Runtime artifacts are written under:

- `runtime/mediacrawler/jobs/*.json`
- `runtime/mediacrawler/logs/*.log`

Task execution result is stored at:

- `task.config.mediacrawler_result`
