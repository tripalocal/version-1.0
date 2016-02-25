import React, { PropTypes } from 'react'
import Cell from './Cell'

const Row = ({ fields, handleChange, searchItems }) => (
  <tr> 
  {Object.keys(fields).map(field =>
    if (field === 'date') {
      return <td>{fields.field}</td>
    }
    return(
      <Cell key={fields}
        item={fields.field}
        type={field}
        searchItems={searchItems}
        handleChange={handleChange}
      />
    )
  )}
  </tr>
)

Row.propTypes = {
  fields: PropTypes.arrayOf(PropTypes.shape({

  })),
  handleChange: PropTypes.func,
  searchItems: PropTypes.func
}

export default Row
