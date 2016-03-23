export const changeTitle = (title) => {
  return {
    type: 'CHANGE_TITLE',
    title
  }
}

export const addDate = (date, city, position) => {
  const targetDate = new Date(date)
  let newDate = new Date()
  if (position.toUpperCase() === 'BEFORE') {
    newDate.setTime(targetDate.getTime() - 86400000)
    return {
      type: 'ADD_DATE',
      city,
      date: newDate.toISOString().slice(0,10)
    }
  }
  newDate.setTime(targetDate.getTime() + 86400000)
  return {
    type: 'ADD_DATE',
    city,
    date: newDate.toISOString().slice(0,10)
  }
}

export const moveDate = (date, direction) => {
  const oldDate = new Date(date)
  const newDate = new Date()
  if (direction === 'BACK') {
    newDate.setDate(oldDate.getDate() - 1)
    return {
      type: 'MOVE_DATE',
      oldDate: oldDate.toISOString().slice(0,10),
      newDate: newDate.toISOString().slice(0,10)
    }
  }
  newDate.setDate(oldDate.getDate() + 1)
  return {
    type: 'MOVE_DATE',
    oldDate: oldDate.toISOString().slice(0,10),
    newDate: newDate.toISOString().slice(0,10)
  }
}

export const removeDate = (date) => {
  return {
    type: 'REMOVE_DATE',
    date
  }
}

export const selectDate = (date) => {
  return {
    type: 'SELECT_DATE',
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
