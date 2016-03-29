export const changeTitle = (title) => {
  return {
    type: 'CHANGE_TITLE',
    title
  }
}

export const changeStartDate = (date) => {
  return {
    type: 'CHANGE_START_DATE',
    date
  }
}

export const changeGuests = (guests) => {
  return {
    type: 'CHANGE_GUESTS',
    guests
  }
}

export const addBookings = (items) => {
  return fetch('/get_price/', {
    method: 'post',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].getAttribute('value'),
      items: items 
    })
  }).then((response) => {
    return response.json()
  }).then((json) => {
    return {
      type: 'ADD_BOOKINGS',
      bookings: json.bookings
    }
  }).catch((exception) => {
    console.log('get price error:', exception)
    return {
    }
  })
}

export const updateBooking = (id, guests) => {
  return {
    type: 'UPDATE_BOOKING',
    id,
    guests
  }
}

export const addDate = (date, city, position) => {
  const targetDate = new Date(date)
  if (position.toUpperCase() === 'BEFORE') {
    return {
      type: 'ADD_DATE',
      city,
      date: targetDate.toISOString().slice(0,10)
    }
  }
  let newDate = new Date()
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
    newDate.setTime(oldDate.getTime() - 86400000)
    return {
      type: 'MOVE_DATE',
      oldDate: oldDate.toISOString().slice(0,10),
      newDate: newDate.toISOString().slice(0,10)
    }
  }
  newDate.setTime(oldDate.getTime() + 86400000)
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
      const { title, dates } = getState()
      window.submit(title, dates)
    }, 1000)
  }
}
