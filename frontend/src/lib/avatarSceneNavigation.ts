import type { LocationQuery, LocationQueryRaw } from 'vue-router'

export function buildDraftlessQuery(query: LocationQuery | LocationQueryRaw): LocationQueryRaw {
  const nextQuery: LocationQueryRaw = { ...query }
  delete nextQuery.draftId
  return nextQuery
}
