import React, { PropTypes } from 'react'
import { connect } from 'react-redux'
import { assignHost, showModal } from '../actions'

const AssignHostForm = ({ bookings, handleChange }) => (
  <div>
    <h2>分配工作</h2>
  {bookings.map(booking => 
    <div className="form-group">
      <label>{booking.title}</label>
      <select value={booking.host} className="form-control" onChange={e => handleChange(booking.id, e.target.value)}>
        <option selected value="None" label="不分配">不分配</option>
        <option value="tripalocal" label="本土客">本土客</option>
        <option value="host1" label="司导1">司导1</option>
        <option value="host2" label="司导2">司导2</option>
        <option value="host3" label="司导3">司导3</option>
        <option value="host4" label="司导4">司导4</option>
      </select>
    </div>)}
  </div>
)

const mapStateToProps = (state) => {
  return {
    bookings: state.bookings
  }
}

const mapDispatchToProps = (dispatch, ownProps) => {
  return {
    handleChange: (id, val) => {
      dispatch(assignHost(id, val))
    }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(AssignHostForm)
