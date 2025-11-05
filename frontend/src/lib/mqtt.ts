
// MQTT client wiring (browser, WebSockets)
// - Connects to broker via VITE_MQTT_URL 
// - Subscribes to restaurant/foods/<table>
// - Publishes orders to restaurant/orders/<table>
// - Updates Svelte stores on 'ready' and 'error' events
// Publish = "shout a message to a topic." Here: restaurant/orders/3 means "order for table 3."
//Subscribe = “listen to a topic." We listen to restaurant/foods/3 to hear when that table’s food is ready.
//MQTT is great at this: many clients can subscribe; the broker fans the message to all of them.
//1. User clicks ORDER on Table 3 → askFood(3) builds an order.
//2. UI adds it to $inFlight immediately (optimistic “preparing”).
//3. publishOrder sends the JSON to topic restaurant/orders/3.
//4. Backend (Python) is subscribed to restaurant/orders/#. It:
//5. validates the order, waits a random time, publishes to restaurant/foods/3 with {status:'ready', prepMs,...}.
//6. mqtt.ts receives the message, parses JSON, calls markReady.
//7. markReady updates $tableFood[3] and removes from $inFlight.
//8. UI auto-updates because Svelte re-renders on store change.


import mqtt, { type MqttClient } from 'mqtt'
import { TABLE_COUNT, markReady, markError } from './store'
import type { Order, FoodEvent } from './types'

let client: MqttClient | null = null

const BROKER_URL = import.meta.env.VITE_MQTT_URL ?? 'ws://localhost:8083/mqtt'
const CLIENT_ID = 'web-' + Math.random().toString(16).slice(2)

// Get or create a singleton MQTT client (one browser tab -> one connection)
export function getClient(): MqttClient {
  if (client) return client

  client = mqtt.connect(BROKER_URL, {
    clientId: CLIENT_ID,
    clean: true,
    reconnectPeriod: 1000,
  })

  // When connected, subscribe to per-table topics so we hear ready food
  client.on('connect', () => {
    for (let t = 1; t <= TABLE_COUNT; t++) {
      client!.subscribe(`restaurant/foods/${t}`)
    }
    // listen to table 0 for "unknown/invalid" error events from backend
    client!.subscribe('restaurant/foods/0')
    console.info('MQTT connected:', BROKER_URL)
  })

  // When a message arrives, decode JSON and update stores
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

// Publish an order to the appropriate topic, Ui - broker - backend
export function publishOrder(order: Order) {
  const c = getClient()
  c.publish(`restaurant/orders/${order.table}`, JSON.stringify(order), { qos: 1 })
}


// helper to reset the singleton client between tests
export function __resetClientForTests() {
  client = null
}