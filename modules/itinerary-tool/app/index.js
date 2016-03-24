import './react-select.css'

import React from 'react'
import { render } from 'react-dom'
import { Provider } from 'react-redux'
import { createStore, applyMiddleware } from 'redux'
import thunk from 'redux-thunk'
import rootReducer from './reducers'
import App from './containers/App'

/*
  ===============
  State structure 
  ======================
  `modal` takes a string
  `dates` takes an object
  =====================================
   
window.initialState = {
  selected: '',
  modal: {
    display: 'NONE',
    date: '',
    field: ''
  }, 
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
        display: 'NORMAL'
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
        display: 'NORMAL'
      }
    }
  }
}
*/
let store = createStore(rootReducer, window.initialState, applyMiddleware(thunk))

render(
  <Provider store={store}>
    <App />
  </Provider>,
  document.getElementById('root')
)

