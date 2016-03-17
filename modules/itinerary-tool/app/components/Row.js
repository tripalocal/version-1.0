import React, { PropTypes } from 'react'
import CellState from '../containers/CellState'

const Row = ({ date, fields }) => (
  <tr>
    <td>{date}</td>
    <td>{fields['city']}</td>
    <CellState date={date} city={fields['city']} key={date + 'experiences'} fieldName="experiences" field={fields['experiences']} />
    <CellState date={date} city={fields['city']} key={date + 'transport'} fieldName="transport" field={fields['transport']} />
    <CellState date={date} city={fields['city']} key={date + 'accommodation'} fieldName="accommodation" field={fields['accommodation']} />
    <CellState date={date} city={fields['city']} key={date + 'restaurants'} fieldName="restaurants" field={fields['restaurants']} />
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
