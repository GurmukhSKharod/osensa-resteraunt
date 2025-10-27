// Used by both mqtt.ts and store.ts
export type Order = { orderId: string; table: number; food: string; ts: number }
export type FoodEvent = {
  orderId: string; table: number; food: string;
  status: 'ready' | 'error'; prepMs?: number; error?: string
}