
// Svelte stores (app state)
// - tableFood: map table -> list of "Food (ready, 1234ms)"
// - errors: map table -> list of error strings (table 0 = unknown table)
// - inFlight: map orderId -> pending order 

import { writable, type Writable } from 'svelte/store'
import type { Order, FoodEvent } from './types'

export const TABLE_COUNT = 4

export const tableFood: Writable<Record<number, string[]>> = writable(
  Object.fromEntries(Array.from({ length: TABLE_COUNT }, (_, i) => [i + 1, []]))
)

export const errors: Writable<Record<number, string[]>> = writable(
  Object.fromEntries([[0, []], ...Array.from({ length: TABLE_COUNT }, (_, i) => [i + 1, []])])
)

export const inFlight: Writable<Record<string, Order>> = writable({})

export function markReady(evt: FoodEvent) {
  tableFood.update((m) => {
    const line = `${evt.food} (${evt.status}${evt.prepMs ? `, ${evt.prepMs}ms` : ''})`
    m[evt.table] = [...(m[evt.table] ?? []), line]
    return m
  })
  // clear from in-flight if present
  inFlight.update((f) => {
    delete f[evt.orderId]
    return f
  })
}

export function markError(evt: FoodEvent) {
  // Unknown/invalid table from backend uses 0
  const t = evt.table && evt.table > 0 ? evt.table : 0
  errors.update((m) => {
    const msg = evt.error ? `${evt.food || '(no food)'} — ${evt.error}` : `${evt.food || '(no food)'} — error`
    m[t] = [...(m[t] ?? []), msg]
    return m
  })
  // clear matching in-flight order id
  if (evt.orderId) {
    inFlight.update((f) => {
      delete f[evt.orderId]
      return f
    })
  }
}
