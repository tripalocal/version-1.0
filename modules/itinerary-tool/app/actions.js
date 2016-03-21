export const addDate = (date, city, position) => {
  const targetDate = new Date(date)
  let newDate = new Date()
  if (position === 'BEFORE') {
    newDate.setDate(targetDate.getDate() - 1)
    return {
      type: 'ADD_DATE',
      city,
      date: newDate.toISOString().slice(0,10)
    }
  }
  newDate.setDate(targetDate.getDate() + 1)
  return {
    type: 'ADD_DATE',
    city,
    date: newDate.toISOString().slice(0,10)
  }
}

export const removeDate = (date) => {
  return {
    type: 'REMOVE_DATE',
    date
  }
}

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

export function updateThenSave(date, field, val) {
  return (dispatch, getState) => {
    dispatch(updateItems(date, field, val))
    setTimeout(() => {
      const { dates } = getState()
      window.submit(dates)
    }, 1000)
  }
}
