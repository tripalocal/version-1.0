import React, { PropTypes } from 'react'
import CellState from '../containers/CellState'

const Row = ({ date, fields }) => (
  <tr>
    <td>{date}</td>
    {Object.keys(fields).map(field => {
      if (field === 'city') {
        return <td key={date + field}>{fields[field]}</td>
      }
      return <CellState date={date} key={date + field} fieldName={field} field={fields[field]} />
    })}
  </tr>
)

Row.propTypes = {
  date: PropTypes.string,
  fields: PropTypes.shape({
    city: PropTypes.string,
    experiences: PropTypes.object,
    transport: PropTypes.object,
    accommodation: PropTypes.object,
    restaurants: PropTypes.object
  })
}

export default Row
