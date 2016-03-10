export const updateItems = (date, field, value) => {
  return {
    type: 'UPDATE_ITEMS',
    date,
    field,
    value
  }
}

export const newItem = (item) => {
  return {
    type: 'NEW_ITEM',
    item
  }
}

export const assignHost = (date, field, host) => {
  return {
    type: 'ASSIGN_HOST',
    date,
    field,
    host
  }
}

export const showModal = (date, field, setting) => {
  return {
    type: 'SHOW_MODAL',
    date,
    field,
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
