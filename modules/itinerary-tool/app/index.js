import './main.css'
import './react-select.css'

import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import { createStore } from 'redux'
import rootReducer from './reducers'
import App from './components/App'

/*
  ===============
  State structure 
  ======================
  `modal` takes a string
  `dates` takes an Immutable.Map object
  =====================================

  {
    modal: ("NEW_ITEM", "ASSIGN_HOST", "NONE"),
    dates: {
      '2016-02-26': { 
        city: melbourne,
        experiences: {
          items: [
            {
              id: 12345,
              title: "Great experience"
            },
            ...
          ],
          host: "Some person",
          display: ("EDIT", "NORMAL")
        },
        transport: {
          items: [...],
          host: "Some person",
          display: ("EDIT", "NORMAL")
        },
        accommodation: {
          items: [...],
          host: "Some person",
          display: ("EDIT", "NORMAL")
        },
        restaurants: {
          items: [...],
          host: "Some person",
          display: ("EDIT", "NORMAL")
        } 
      },
      '2016-02-27': {
        city: melbourne,
        experiences: {...},
        ...
      }, 
      ...   
    }
  }

*/

let initialState = window.STATE_FROM_SERVER
let store = createStore(rootReducer, initialState)

render(
  <Provider store={store}>
    <App />
  </Provider>,
  document.getElementById('root')
)

