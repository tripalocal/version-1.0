import React, { PropTypes } from 'react'
import Row from './Row'

const Table = ({ days }) => (
  <table className="table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Activities</th>
        <th>Transport</th>
        <th>Accommodation</th>
        <th>Restaurants</th>
      </tr>
    </thead>
    <tbody>
      {days.map(day => <Row fields={day} key={day.date} />)}
    </tbody>
  </table>
)

Table.propTypes = {
  days: PropTypes.array,
  handleChange: PropTypes.func,
  searchItems: PropTypes.func
}

export default Table
