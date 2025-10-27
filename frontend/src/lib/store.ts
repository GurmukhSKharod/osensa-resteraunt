import { writable, type Writable } from 'svelte/store'
import type { Order, FoodEvent } from './types'

export const TABLE_COUNT = 4

export const tableFood: Writable<Record<number, string[]>> = writable(
  Object.fromEntries(Array.from({ length: TABLE_COUNT }, (_, i) => [i + 1, []]))
)

export const inFlight: Writable<Record<string, Order>> = writable({})

export function markReady(evt: FoodEvent) {
  tableFood.update((m) => {
    const line = `${evt.food} (${evt.status}${evt.prepMs ? `, ${evt.prepMs}ms` : ''})`
    m[evt.table] = [...(m[evt.table] ?? []), line]
    return m
  })
  inFlight.update((f) => {
    delete f[evt.orderId]
    return f
  })
}
