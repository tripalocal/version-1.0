import { combineReducers } from 'redux'
import Immutable from 'immutable'

function modal(state = 'NONE', action) {
  switch (action.type) {
    case 'SHOW_MODAL':
      return action.setting
    default:
      return state
  }
}

function dates(state = Immutable.Map(), action) {
  switch (action.type) {
    case 'SHOW_SELECT':
      return state.updateIn([action.date, action.field, display], action.setting)
    default:
      return state
  }
}

const rootReducer = combineReducers({
  modal,
  dates
})

export default rootReducer
