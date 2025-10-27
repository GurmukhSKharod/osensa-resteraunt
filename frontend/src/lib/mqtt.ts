// frontend/src/lib/mqtt.ts
import mqtt, { type MqttClient } from 'mqtt'

import { TABLE_COUNT, markReady } from './store'
import type { Order, FoodEvent } from './types'

let client: MqttClient | null = null

const BROKER_URL =
  import.meta.env.VITE_MQTT_URL ?? 'ws://localhost:8083/mqtt'
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
    console.info('MQTT connected:', BROKER_URL)
  })

  client.on('message', (_topic, payload) => {
    try {
      const evt = JSON.parse(payload.toString()) as FoodEvent
      if (evt?.status === 'ready') markReady(evt)
      // (optionally handle status === 'error')
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
