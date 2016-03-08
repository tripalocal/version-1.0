import { combineReducers } from 'redux'
import { reducer as formReducer } from 'redux-form'
import update from 'react-addons-update'

function modal(state = 'NONE', action) {
  switch (action.type) {
    case 'SHOW_MODAL':
      return action.setting
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
      let { date, field, value } = action
      return update(state, {
        [action.date]: {[action.field]: {items: {$set: action.value}}} 
      })
    default:
      return state
  }
}

const rootReducer = combineReducers({
  modal,
  dates,
  form: formReducer
})

export default rootReducer
