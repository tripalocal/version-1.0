import React from 'react'
import { connect } from 'react-redux'
import { updateBooking, updateThenSave } from '../actions'

const SideBar = ({ bookings, total, guests, dispatch }) => (
  <div className="side-bar">
    <table className="table">
      <thead>
        <tr className="table-header">
          <th>项目</th>
          <th>单位</th>
          <th>报价</th>
          <th>数量</th>
          <th>小计</th>
        </tr>
      </thead>
      <tbody>
        {bookings.map(booking => 
          <tr>
            <td style={{width: '200px'}}>{booking.title}</td>
            <td>每个</td>
            <td>{booking.price}</td>
            <td><input value={booking.guests} onChange={e => dispatch(updateThenSave(updateBooking, [booking.id, e.target.value]))} className="form-control" /></td>
            <td>{booking.guests * booking.price}</td>
          </tr>
        )}
      </tbody>
    </table>
    <div className="bottom-bar">
      <table className="table">
        <thead>
          <tr>
            <th>澳元成本</th> 
            <th>利润</th> 
            <th>人民币</th> 
            <th>人民币每人</th> 
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{total}</td>
            <td>{Math.round(total/(1-0.15))}</td>
            <td>{Math.round(total * 4.91)}</td>
            <td>{Math.round(total * 4.91 / guests)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
)

const mapStateToProps = (state) => {
  return {
    bookings: state.bookings,
    guests: state.guests,
    total: state.bookings.reduce((previous, current) => {
      return previous + (current.guests * current.price)  
    }, 0)
  }
}

export default connect(mapStateToProps)(SideBar)
