<script lang="ts">
  import { TABLE_COUNT, inFlight, tableFood } from './lib/store'
  import { publishOrder } from './lib/mqtt'

  function askFood(table: number) {
    const food = prompt(`Enter food name for table ${table}`)
    if (!food || !food.trim()) return
    const order = { orderId: crypto.randomUUID(), table, food: food.trim(), ts: Date.now() }
    inFlight.update(v => ({ ...v, [order.orderId]: order }))
    publishOrder(order)
  }
</script>

<h1>OSENSA Restaurant</h1>
<p>Click ORDER, type a food, and it will appear when ready.</p>

<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;max-width:800px">
  {#each Array.from({ length: TABLE_COUNT }, (_, i) => i + 1) as t}
    <div style="border:1px solid #aaa;padding:12px;border-radius:8px">
      <h2>Table {t}</h2>
      <button on:click={() => askFood(t)}>ORDER</button>
      <h3>Ready Food</h3>
      <ul>
        {#each $tableFood[t] as item}<li>{item}</li>{/each}
      </ul>
    </div>
  {/each}
</div>

<h3>In-flight Orders</h3>
<ul>
  {#each Object.values($inFlight) as o}
    <li>Table {o.table}: {o.food} (preparing)</li>
  {/each}
</ul>
