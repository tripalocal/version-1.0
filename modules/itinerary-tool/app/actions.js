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

export const changePrice = (id, price) => {
  return {
    type: 'CHANGE_PRICE',
    id,
    price
  }
}

export const changeProfit = (setting) => {
  if (setting === 'UP') {
    return {
      type: 'CHANGE_PROFIT',
      amount: 1
    }  
  }
  return {
    type: 'CHANGE_PROFIT',
    amount: -1
  }
}

export const addBookings = (bookings) => {
  return {
    type: 'ADD_BOOKINGS',
    bookings: bookings
  }
}

export const updateBooking = (id, guests) => {
  return {
    type: 'UPDATE_BOOKING',
    id,
    guests
  }
}

export function updateItems(date, field, value) {
  return (dispatch, getState) => {
    const { bookings } = getState()
    const bookingIDs = bookings.map(booking => booking.id)
    let newBookings = value.filter(item => {
      return (!(bookingIDs.indexOf(item.id) > -1))
    }).map(item => item.id)
    if (newBookings.length > 0) {
      console.log(newBookings)
      return fetch('/get_price/', {
        method: 'post',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          items: newBookings 
        })
      })
      .then((response) => {
        return response.json()
      })
      .then((json) => {
        dispatch(addBookings(json.bookings))
      })
      .then(() => {
        dispatch(addItems(date, field, value))
      })
      .catch((exception) => {
        console.log('get price error:', exception)
      })
    }
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

export const addItems = (date, field, value) => {
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

export const assignHost = (id, host) => {
  return {
    type: 'ASSIGN_HOST',
    id,
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

export function updateThenSave(action, args) {
  return (dispatch, getState) => {
    dispatch(action.apply(this, args))
    setTimeout(() => {
      const { title, dates, bookings, guests, profit } = getState()
      window.submit(title, dates, bookings, guests, profit)
    }, 1000)
  }
}
