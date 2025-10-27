
// MQTT client wiring (browser, WebSockets)
// - Connects to broker via VITE_MQTT_URL 
// - Subscribes to restaurant/foods/<table>
// - Publishes orders to restaurant/orders/<table>
// - Updates Svelte stores on 'ready' and 'error' events

import mqtt, { type MqttClient } from 'mqtt'
import { TABLE_COUNT, markReady, markError } from './store'
import type { Order, FoodEvent } from './types'

let client: MqttClient | null = null

const BROKER_URL = import.meta.env.VITE_MQTT_URL ?? 'ws://localhost:8083/mqtt'
const CLIENT_ID = 'web-' + Math.random().toString(16).slice(2)

export function getClient(): MqttClient {
  if (client) return client

  client = mqtt.connect(BROKER_URL, {
    clientId: CLIENT_ID,
    clean: true,
    reconnectPeriod: 1000,
  })

  client.on('connect', () => {
    for (let t = 1; t <= TABLE_COUNT; t++) {
      client!.subscribe(`restaurant/foods/${t}`)
    }
    // listen to table 0 for "unknown/invalid" error events from backend
    client!.subscribe('restaurant/foods/0')
    console.info('MQTT connected:', BROKER_URL)
  })

  client.on('message', (_topic, payload) => {
    try {
        // Robustly decode Buffer | Uint8Array | string
        const text =
        typeof payload === 'string'
            ? payload
            : payload instanceof Uint8Array
            ? new TextDecoder().decode(payload)
            : (payload as any)?.toString?.() ?? String(payload)

        const evt = JSON.parse(text) as FoodEvent

        if (evt?.status === 'ready') {
        markReady(evt)
        } else if (evt?.status === 'error') {
        markError(evt)
        }
    } catch (e) {
        console.error('Bad payload from MQTT:', e)
    }
 })


  client.on('error', (err) => console.error('MQTT error', err))
  return client
}

export function publishOrder(order: Order) {
  const c = getClient()
  c.publish(`restaurant/orders/${order.table}`, JSON.stringify(order), { qos: 1 })
}


// helper to reset the singleton client between tests
export function __resetClientForTests() {
  client = null
}