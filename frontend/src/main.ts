// OSENSA Restaurant – Main entry point, mounts Svelte App and initializes MQTT client
import './app.css'
import App from './App.svelte'
import { mount } from 'svelte'
import { getClient } from './lib/mqtt'

getClient()

mount(App, { target: document.getElementById('app')! })
