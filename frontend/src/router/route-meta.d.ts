import 'vue-router'
import type { RouteNavKey } from '../navigation/config'

declare module 'vue-router' {
  interface RouteMeta {
    guestOnly?: boolean
    requiresAuth?: boolean
    legacyKey?: RouteNavKey
  }
}
