// Tests: mqtt wiring (subscribe, message handling) with module mock
import { vi, expect, test, beforeEach } from 'vitest'

// Capture callbacks the code registers on the fake client
const handlers: Record<string, Function[]> = {}

const fakeClient = {
  subscribe: vi.fn(),
  publish: vi.fn(),
  on: vi.fn((event: string, cb: Function) => {
    handlers[event] ??= []
    handlers[event].push(cb)
  }),
}

// Mock the 'mqtt' module so `mqtt.connect()` returns our fake client
vi.mock('mqtt', () => {
  return {
    default: {
      connect: vi.fn(() => fakeClient),
    },
  }
})

import { get } from 'svelte/store'
import { tableFood, errors, inFlight } from '../store'
import { getClient, publishOrder, __resetClientForTests } from '../mqtt'

beforeEach(() => {
  // clear handlers and spies
  Object.keys(handlers).forEach((k) => delete handlers[k])
  fakeClient.subscribe.mockClear()
  fakeClient.publish.mockClear()
  __resetClientForTests()

  tableFood.set({ 1: [], 2: [], 3: [], 4: [] } as any)
  errors.set({ 0: [], 1: [], 2: [], 3: [], 4: [] } as any)
  inFlight.set({})
})

test('getClient subscribes to restaurant/foods/1..4 and 0', () => {
  const c = getClient()
  expect(c).toBeTruthy()

  // simulate the connect event to trigger subscribe logic
  handlers['connect']?.forEach((h) => h())

  // Expect 5 subscriptions (tables 1..4 + 0 for global errors)
  const topics = fakeClient.subscribe.mock.calls.map((args) => args[0])
  expect(topics).toContain('restaurant/foods/1')
  expect(topics).toContain('restaurant/foods/2')
  expect(topics).toContain('restaurant/foods/3')
  expect(topics).toContain('restaurant/foods/4')
  expect(topics).toContain('restaurant/foods/0')
})

test('incoming ready message updates tableFood', () => {
  getClient()
  // capture 'message' handler
  const onMessage = handlers['message'][0] as (t: string, p: Uint8Array) => void

  const payload = JSON.stringify({ orderId: 'x', table: 1, food: 'Soup', status: 'ready', prepMs: 900 })
  onMessage('restaurant/foods/1', new TextEncoder().encode(payload))

  expect(get(tableFood)[1][0]).toContain('Soup')
})

test('incoming error message updates errors store', () => {
  getClient()
  const onMessage = handlers['message'][0] as (t: string, p: Uint8Array) => void

  const payload = JSON.stringify({ orderId: 'bad', table: 0, food: '', status: 'error', error: 'invalid' })
  onMessage('restaurant/foods/0', new TextEncoder().encode(payload))

  expect(get(errors)[0][0]).toMatch(/invalid/)
})

test('publishOrder sends to correct topic with JSON body', () => {
  getClient()
  publishOrder({ orderId: 'o1', table: 3, food: 'Pasta', ts: 1 })
  const [topic, json, opts] = fakeClient.publish.mock.calls[0]

  expect(topic).toBe('restaurant/orders/3')
  expect(JSON.parse(json).food).toBe('Pasta')
  expect(opts.qos).toBe(1)
})
