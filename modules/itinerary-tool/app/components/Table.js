import React, { PropTypes } from 'react'
import Row from './Row'

const Table = ({ dates }) => (
  <table className="table">
    <thead>
      <tr>
        <th>Date</th>
        <th>City</th>
        <th>Activities</th>
        <th>Transport</th>
        <th>Accommodation</th>
        <th>Restaurants</th>
      </tr>
    </thead>
    <tbody>
      {Object.keys(dates).map(date => <Row key={date} date={date} />)}
    </tbody>
  </table>
)

Table.propTypes = {
  days: PropTypes.array,
  handleChange: PropTypes.func,
  searchItems: PropTypes.func
}

export default Table
