import './main.css'
import './react-select.css'

import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import { createStore } from 'redux'
import rootReducer from './reducers'
import App from './containers/App'

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

let initialState = {
  modal: 'NONE', 
  dates: {
    '2016-03-01': {
      city: 'melbourne',
      experiences: {
        items: [{title: 'great activity', id: 1205}, {title: 'another great one', id:14902}],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton'],
        host: 'Guy',
        display: 'NORMAL'
      },
      restaurants: {
        items: ['Food Inc.'],
        host: 'Person',
        display: 'EDIT'
      }
    },
    '2016-03-02': {
      city: 'melbourne',
      experiences: {
        items: [{title: 'cool activity', id: 54950}, {title: 'another one', id: 54135}],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton'],
        host: 'Guy',
        display: 'NORMAL'
      },
      restaurants: {
        items: [{title: 'Food Inc.', id: 12345}],
        host: 'Person',
        display: 'EDIT'
      }
    }
  }
}

let store = createStore(rootReducer, initialState)

render(
  <Provider store={store}>
    <App />
  </Provider>,
  document.getElementById('root')
)

