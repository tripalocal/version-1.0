import React, { PropTypes } from 'react'
import Select from 'react-select'

const Cell = ({ type, items, searchItems, handleChange }) => (
  <td>
    <Select.Async
      loadOptions={searchItems}
      placeholder={type}
      onChange={handleChange}
      value={items}
      clearable={false}
      multi
    /> 
  </td>
)

Cell.propTypes = {
  type: PropTypes.string,
  items: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string,
    value: PropTypes.number
  })),
  searchItems: PropTypes.func,
  handleChange: PropTypes.func
}

export default Cell
