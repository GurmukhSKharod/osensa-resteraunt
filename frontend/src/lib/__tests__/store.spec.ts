// Tests: Svelte stores (markReady / markError)
import { beforeEach, test, expect, vi } from 'vitest'
import { get } from 'svelte/store'
import { tableFood, errors, inFlight, markReady, markError } from '../store'
import type { FoodEvent } from '../types'

beforeEach(() => {
  // reset stores between tests
  inFlight.set({})
  tableFood.set({ 1: [], 2: [], 3: [], 4: [] } as any)
  errors.set({ 0: [], 1: [], 2: [], 3: [], 4: [] } as any)
})

test('markReady appends item & clears inFlight', () => {
  // arrange an in-flight order
  inFlight.update((f) => ({ ...f, o1: { orderId: 'o1', table: 2, food: 'Pizza', ts: Date.now() } }))

  const evt: FoodEvent = { orderId: 'o1', table: 2, food: 'Pizza', status: 'ready', prepMs: 1200 }
  markReady(evt)

  expect(get(tableFood)[2][0]).toContain('Pizza')
  expect(get(tableFood)[2][0]).toContain('1200ms')
  expect(get(inFlight)['o1']).toBeUndefined()
})

test('markError logs under table or global(0) and clears inFlight', () => {
  inFlight.update((f) => ({ ...f, bad: { orderId: 'bad', table: 3, food: '??', ts: Date.now() } }))

  // table-specific error
  markError({ orderId: 'bad', table: 3, food: '??', status: 'error', error: 'invalid order' })
  expect(get(errors)[3][0]).toMatch(/invalid order/)
  expect(get(inFlight)['bad']).toBeUndefined()

  // unknown table -> goes to bucket 0
  markError({ orderId: '', table: 0, food: '', status: 'error', error: 'unknown table' })
  expect(get(errors)[0][0]).toMatch(/unknown table/)
})
