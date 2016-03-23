import { combineReducers } from 'redux'
import { reducer as formReducer } from 'redux-form'
import update from 'react-addons-update'

function title(state = '', action) {
  switch (action.type) {
    case 'CHANGE_TITLE':
      return action.title
    default:
      return state
  }
}

function selected(state = '', action) {
  switch (action.type) {
    case 'SELECT_DATE':
      if (state == action.date) {
        return '' 
      }
      return action.date
    default:
      return state
  }
}

function modal(state = {date: '', field: '', display: 'NONE'}, action) {
  switch (action.type) {
    case 'SHOW_MODAL':
      return update(state, {
        date: {$set: action.date},
        field: {$set: action.field},
        display: {$set: action.setting}
      })
    default:
      return state
  }
}

function dates(state = {}, action) {
  switch (action.type) {
    case 'SHOW_SELECT':
      return update(state, {
        [action.date]: {[action.field]: {display: {$set: action.setting}}}
      })
    case 'UPDATE_ITEMS':
      return update(state, {
        [action.date]: {[action.field]: {items: {$set: action.value}}} 
      })
    case 'ADD_DATE':
      if (state[action.date]) {
        let newDate = new Date(action.date)
        return Object.keys(state).reduce((newState, key) => {
          let thisDate = new Date(key) 
          if (thisDate >= newDate) {
            thisDate.setTime(thisDate.getTime() + 86400000)
          }
          newState[thisDate.toISOString().slice(0,10)] = state[key]
          return newState 
        }, {[action.date]: {'city': action.city, 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}})
      }
      return Object.assign({}, state, {
        [action.date]: {'city': action.city, 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}
      })
    case 'REMOVE_DATE':
      let newState = Object.assign({}, state)
      delete newState[action.date]
      return newState
    case 'MOVE_DATE':
      return update(state, {
        [action.oldDate] : {$set: state[action.newDate]},
        [action.newDate] : {$set: state[action.oldDate]}
      })
    case 'ASSIGN_HOST':
      return update(state, {
        [action.date]: {[action.field]: {host: {$set: action.host}}}
      })
    default:
      return state
  }
}

const rootReducer = combineReducers({
  title,
  selected,
  modal,
  dates,
  form: formReducer
})

export default rootReducer
