export const addItem = (item) => {
  return {
    type: 'ADD_ITEM',

  }
}

export const newItem = (item) => {
  return {
    type: 'NEW_ITEM'
  }
}

export const deleteItem = (item, date) => {
  return {
    type: 'DELETE_ITEM'
  }
}

export const assignHost = (host, date) => {
  return {
    type: 'ASSIGN_HOST'
  }
}

export const showModal = (setting) => {
  return {
    type: 'SHOW_MODAL',
    setting
  }
}

export const showSelect = (date, field, setting) => {
  return {
    type: 'SHOW_SELECT',
    date,
    field,
    setting
  }
}
