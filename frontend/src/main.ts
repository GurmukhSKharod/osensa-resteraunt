import './app.css'
import App from './App.svelte'
import { mount } from 'svelte'          
import { getClient } from './lib/mqtt'

getClient() // start MQTT

// mount the root component
mount(App, {                          
  target: document.getElementById('app')!
})