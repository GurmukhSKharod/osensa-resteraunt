
// Svelte stores (app state)
// - tableFood: map table -> list of "Food (ready, 1234ms)"
// - errors: map table -> list of error strings (table 0 = unknown table)
// - inFlight: map orderId -> pending order 

import { writable, type Writable } from 'svelte/store'
import type { Order, FoodEvent } from './types'

export const TABLE_COUNT = 4

// tableFood: for each table number, a list of strings like "pizza (ready, 2700ms)"
export const tableFood: Writable<Record<number, string[]>> = writable(
  Object.fromEntries(Array.from({ length: TABLE_COUNT }, (_, i) => [i + 1, []]))
)

// errors: per table list of error strings; table 0 is “global/unknown table”
export const errors: Writable<Record<number, string[]>> = writable(
  Object.fromEntries([[0, []], ...Array.from({ length: TABLE_COUNT }, (_, i) => [i + 1, []])])
)

// inFlight: orders we have sent but are not ready yet keyed by orderId
export const inFlight: Writable<Record<string, Order>> = writable({})

// When backend says a food is ready, add it and remove from inFlight
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

// When backend sends an error (bad table, validation, etc.)
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
