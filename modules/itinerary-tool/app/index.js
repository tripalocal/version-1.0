import './main.css'
import './react-select.css'

import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import { createStore } from 'redux'
import itineraryTool from './reducers'
import App from './components/App'

render(
  <App days={DAYS} />,
  document.getElementById('root')
)

