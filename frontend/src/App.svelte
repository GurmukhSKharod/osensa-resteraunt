<script lang="ts">
  import { onMount } from 'svelte';
  import { TABLE_COUNT, inFlight, tableFood, errors } from './lib/store';
  import { publishOrder } from './lib/mqtt';
  import { wakeBackend } from './lib/wakeBackend';

  // Nudge backend as soon as the UI loads
  onMount(() => {
    wakeBackend();
  });

  async function askFood(table: number) {
    const food = prompt(`Enter food name for table ${table}`);
    if (!food || !food.trim()) return;

    // Nudge again right before first meaningful action
    await wakeBackend();

    const order = { orderId: crypto.randomUUID(), table, food: food.trim(), ts: Date.now() };
    inFlight.update(v => ({ ...v, [order.orderId]: order }));
    publishOrder(order);
  }
</script>


<h1>OSENSA Restaurant</h1>
<p>Click ORDER, type a food, and it will appear when ready. Errors show below each table.</p>

<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;max-width:900px">
  {#each Array.from({ length: TABLE_COUNT }, (_, i) => i + 1) as t}
    <div style="border:1px solid #aaa;padding:12px;border-radius:8px">
      <h2>Table {t}</h2>
      <button on:click={() => askFood(t)}>ORDER</button>

      <h3>Ready Food</h3>
      <ul>
        {#each $tableFood[t] as item}<li>{item}</li>{/each}
      </ul>

      <h3>Errors</h3>
      <ul>
        {#each $errors[t] as err}<li style="color:#b00020">{err}</li>{/each}
      </ul>
    </div>
  {/each}
</div>

<h3>Global Errors (table 0)</h3>
<ul>
  {#each $errors[0] as err}<li style="color:#b00020">{err}</li>{/each}
</ul>

<h3>In-flight Orders</h3>
<ul>
  {#each Object.values($inFlight) as o}
    <li>Table {o.table}: {o.food} (preparing)</li>
  {/each}
</ul>
